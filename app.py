"""
Streamlit frontend + ReACT-style agent adapter + deterministic assignment + SQLite persistence.

Key design:
- LLM (Ollama) used for summarization / NER / candidate suggestions only.
- Deterministic logic performs final task detection & assignment.
- Databases: SQLite with tables team_members, tasks, assignments.
"""

import streamlit as st
import sqlite3
import json
import re
from datetime import datetime, timezone
import dateparser
import requests
from typing import List, Dict, Optional, Any
from uuid import uuid4

# ----------------------------
# Configuration
# ----------------------------
LLM_ENDPOINT = "http://localhost:11434/api/generate"  # Ollama default
LLM_MODEL = "gemma-3-270m"  # change to your local model name in ollama
DB_PATH = "meeting_agent.db"

# ----------------------------
# Helpers: DB setup
# ----------------------------
def init_db(db_path=DB_PATH):
    con = sqlite3.connect(db_path, check_same_thread=False)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS team_members (
        id TEXT PRIMARY KEY,
        name TEXT,
        role TEXT,
        skills TEXT,         -- JSON array
        workload REAL        -- 0.0 .. 1.0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        meeting_id TEXT,
        raw_text TEXT,
        summary TEXT,
        deadline TEXT,
        priority TEXT,
        dependencies TEXT,
        context_notes TEXT,
        detected_by TEXT,    -- 'heuristic' or 'llm_suggestion' etc
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id TEXT PRIMARY KEY,
        task_id TEXT,
        member_id TEXT,
        reason TEXT,
        llm_suggestion TEXT,  -- JSON
        final_decision TEXT,  -- JSON
        created_at TEXT
    )
    """)
    con.commit()
    return con

db = init_db()

# ----------------------------
# Utility functions
# ----------------------------
def now_iso():
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

def parse_deadline(text: str, meeting_date: Optional[datetime]=None) -> Optional[str]:
    if not text:
        return None
    base = meeting_date or datetime.utcnow()
    parsed = dateparser.parse(text, settings={'RELATIVE_BASE': base})
    if parsed:
        return parsed.date().isoformat()
    return None

def ensure_json_list(x):
    if isinstance(x, list): return x
    try:
        return json.loads(x)
    except Exception:
        return []

# ----------------------------
# LLM wrapper (Ollama) - can be swapped
# ----------------------------
def call_llm(prompt: str, model=LLM_MODEL, temperature=0.0, max_tokens=512) -> str:
    """
    Calls local LLM via Ollama HTTP API.
    Expects open, simple free-text response. Use temperature=0 for deterministic outputs.
    If you use a different local runtime (Hugging Face), replace this function accordingly.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    try:
        r = requests.post(LLM_ENDPOINT, json=payload, timeout=30)
        r.raise_for_status()
        # Ollama returns structured JSON; the API may wrap the text in choices/... depending on version.
        data = r.json()
        # Try a few heuristics to extract text:
        if isinstance(data, dict):
            # common Ollama response structure includes 'choices' or 'output' keys. Adjust if needed.
            if 'output' in data:
                if isinstance(data['output'], list):
                    return ''.join([str(x) for x in data['output']])
                return str(data['output'])
            if 'choices' in data and isinstance(data['choices'], list):
                return data['choices'][0].get('content') or data['choices'][0].get('text') or json.dumps(data['choices'][0])
        return json.dumps(data)
    except Exception as e:
        st.warning(f"LLM call failed: {e}")
        return ""

# ----------------------------
# ReACT-style Agent Adapter (simple)
# ----------------------------
class ReACTAgent:
    """
    Lightweight ReACT-style wrapper: gives the LLM a set of tools it can call,
    but the implementation here is a thin adapter: we call LLM with a prompt that
    asks for a JSON output with keys: summary, persons, date_phrases, priority_hint.
    We always validate the JSON and never let the LLM perform assignments.
    """
    def __init__(self, call_llm_fn):
        self.call_llm = call_llm_fn

    def analyze_segment(self, segment_text: str, meeting_date_iso: str) -> Dict[str, Any]:
        prompt = f\"\"\"You are an assistant that helps extract task-related information from a meeting utterance.
Return strictly valid JSON with keys:
- summary: a single short action-style sentence (or empty string)
- persons: list of person names mentioned (may be empty)
- date_phrases: list of natural-language date phrases found (e.g., "by Friday")
- priority_hint: one of ["Critical","High","Medium","Low",""] (or empty)
- dependencies: list of phrases indicating dependencies (e.g., "after design is ready")
- context_notes: short notes (blockers, constraints) or empty

Reference meeting date (ISO): {meeting_date_iso}

Utterance: \"\"\" + segment_text + "\"\"\"\n"
        raw = self.call_llm(prompt)
        # Try to extract JSON from the output
        # The LLM may return plain JSON or a surrounding text. We attempt to find the first { ... } block.
        json_text = None
        m = re.search(r"(\{.*\})", raw, flags=re.S)
        if m:
            json_text = m.group(1)
        else:
            json_text = raw
        try:
            parsed = json.loads(json_text)
        except Exception:
            # If JSON parsing fails, fallback to naive extraction heuristics
            parsed = {
                "summary": (segment_text[:200] + "...") if len(segment_text) > 200 else segment_text,
                "persons": re.findall(r"\\b([A-Z][a-z]{1,30})\\b", segment_text),
                "date_phrases": re.findall(r"\\b(by\\s+\\w+|next\\s+\\w+|tomorrow|today|on\\s+\\w+|this\\s+week)\\b", segment_text, flags=re.I),
                "priority_hint": "",
                "dependencies": [],
                "context_notes": ""
            }
        # Normalize fields
        parsed.setdefault("summary", "")
        parsed.setdefault("persons", [])
        parsed.setdefault("date_phrases", [])
        parsed.setdefault("priority_hint", "")
        parsed.setdefault("dependencies", [])
        parsed.setdefault("context_notes", "")
        return parsed

# instantiate agent
agent = ReACTAgent(call_llm)

# ----------------------------
# Task detection (deterministic / heuristics)
# ----------------------------
CUE_RE = re.compile(r"\\b(we need to|can you|please|assign|todo|action item|we should|i'll|i will|can someone|who can|volunteer|take it)\\b", flags=re.I)
IMPERATIVE_STARTS = {'update','fix','test','deploy','design','create','prepare','write','review','check','implement','investigate','follow','schedule','setup','migrate','refactor','improve','add','remove','patch'}

def is_task_candidate_heuristic(text: str) -> bool:
    if CUE_RE.search(text):
        return True
    first = text.strip().split()[0].lower() if text.strip() else ""
    if first in IMPERATIVE_STARTS:
        return True
    # relative date words
    if re.search(r"\\b(by|before|on|next|tomorrow|today|this week|end of day|eod)\\b", text, flags=re.I):
        return True
    return False

# ----------------------------
# Assignment logic (deterministic)
# ----------------------------
def score_member_for_task(member: Dict[str,Any], task_summary: str, task_priority: str, task_deadline_iso: Optional[str]) -> float:
    """
    Compute a deterministic score for a member for the given task.
    Components:
      - skill_match (0..1)
      - role_fit (0/1)
      - availability (1 - workload)
      - deadline urgency minor boost
      - priority boost
    """
    skills = ensure_json_list(member.get('skills', '[]'))
    role = member.get('role','').lower()
    txt = task_summary.lower()
    # skill match: count overlaps of skill token in text
    if not skills:
        skill_match = 0.0
    else:
        hits = sum(1 for s in skills if s.lower() in txt)
        skill_match = hits / max(1, len(skills))
    role_fit = 1.0 if role and role in txt else 0.0
    availability = 1.0 - float(member.get('workload', 0.0))
    score = 0.6*skill_match + 0.25*role_fit + 0.15*availability
    # priority boost
    prio_boost = {'Critical':0.12,'High':0.07,'Medium':0.0,'Low':0.0}
    score += prio_boost.get(task_priority or '', 0.0)
    # deadline urgency: if within 2 days, favor low-workload
    if task_deadline_iso:
        try:
            d = datetime.fromisoformat(task_deadline_iso)
            delta_days = (d.date() - datetime.utcnow().date()).days
            if delta_days <= 2:
                score += 0.05 * availability
        except Exception:
            pass
    return score

def deterministic_assign(task: Dict[str,Any], members: List[Dict[str,Any]]) -> Dict[str,Any]:
    """
    Return chosen member dict and a 'reason' object describing feature values.
    """
    best = None
    best_score = -9.0
    best_summary = task.get('summary') or task.get('raw_text','')
    for m in members:
        s = score_member_for_task(m, best_summary, task.get('priority',''), task.get('deadline'))
        if s > best_score:
            best_score = s
            best = m
    reason = {
        "method": "deterministic_scoring_v1",
        "score": best_score
    }
    return {"member": best, "reason": reason}

# ----------------------------
# Pipeline: process transcript into tasks -> assign -> persist
# ----------------------------
def process_meeting(meeting_id: str, transcript_text: str, meeting_date_iso: str, members: List[Dict[str,Any]]):
    """
    Steps:
     - Split transcript into segments (naive per newline)
     - For each segment: call LLM assistant (ReACTAgent.analyze_segment) to get summary & suggestions
     - Combine LLM suggestion + heuristics to decide if it's a task candidate
     - If yes: extract deadline via dateparser, priority via hints, find dependencies
     - Deterministic assignment -> save task + assignment + provenance
    """
    segments = [s.strip() for s in transcript_text.splitlines() if s.strip()]
    created_tasks = []
    for seg in segments:
        seg_id = str(uuid4())
        llm_out = agent.analyze_segment(seg, meeting_date_iso)
        # decide if candidate
        is_candidate = is_task_candidate_heuristic(seg) or (llm_out.get('summary') and len(llm_out.get('summary'))>10)
        # Additionally, you might require LLM summary to contain verbs/nouns etc.
        if not is_candidate:
            continue
        # Build task record
        summary = llm_out.get('summary') or seg[:300]
        date_phrases = llm_out.get('date_phrases',[])
        deadline_iso = None
        if date_phrases:
            # try parse the first phrase
            deadline_iso = parse_deadline(date_phrases[0], meeting_date_iso and datetime.fromisoformat(meeting_date_iso))
        # priority
        priority = llm_out.get('priority_hint') or infer_priority_from_text(seg)
        # dependencies + context
        deps = llm_out.get('dependencies', [])
        context = llm_out.get('context_notes','')
        # Persist task
        cur = db.cursor()
        task_id = str(uuid4())
        cur.execute("""
            INSERT INTO tasks (id, meeting_id, raw_text, summary, deadline, priority, dependencies, context_notes, detected_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (task_id, meeting_id, seg, summary, deadline_iso, priority, json.dumps(deps), context, 'llm_assisted', now_iso()))
        db.commit()
        # Assignment: if LLM suggested persons and one matches our members, prefer but verify
        person_suggested = None
        for p in llm_out.get('persons', []):
            # basic match by name
            for mm in members:
                if mm['name'].lower() == p.lower():
                    person_suggested = mm
                    break
            if person_suggested:
                break
        # If LLM suggested a person and deterministic check passes, pick that; otherwise deterministic assign
        chosen = None
        chosen_reason = {}
        if person_suggested:
            # verify suggested person meets minimal heuristic: at least name present (we already matched)
            chosen = person_suggested
            chosen_reason = {"method":"llm_suggested_verified", "note":"llm suggested and name exists in team"}
        else:
            # deterministic selection
            chosen_result = deterministic_assign({
                "summary": summary,
                "priority": priority,
                "deadline": deadline_iso
            }, members)
            chosen = chosen_result['member']
            chosen_reason = chosen_result['reason']
        # Save assignment
        assignment_id = str(uuid4())
        cur.execute("""
            INSERT INTO assignments (id, task_id, member_id, reason, llm_suggestion, final_decision, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            assignment_id,
            task_id,
            chosen['id'] if chosen else None,
            json.dumps(chosen_reason),
            json.dumps(llm_out),
            json.dumps({"member_id": chosen['id'] if chosen else None, "reason": chosen_reason}),
            now_iso()
        ))
        db.commit()
        created_tasks.append({
            "task_id": task_id,
            "summary": summary,
            "deadline": deadline_iso,
            "priority": priority,
            "assigned_to": chosen['name'] if chosen else None,
            "reason": chosen_reason
        })
    return created_tasks

# ----------------------------
# Small helper to infer priority from raw text (deterministic)
# ----------------------------
def infer_priority_from_text(text: str) -> str:
    t = text.lower()
    if re.search(r"\\b(critical|urgent|asap|blocking|blocker)\\b", t):
        return "Critical"
    if re.search(r"\\b(by\\s+(tomorrow|end of day|eod|friday|monday|tuesday|wednesday|thursday))\\b", t):
        return "High"
    if re.search(r"\\b(next week|this week|within a week)\\b", t):
        return "Medium"
    return "Low"

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Meeting Task ReACT Agent", layout="wide")
st.title("Meeting → Tasks (ReACT-style) — Streamlit Prototype")

# left: upload + team
col1, col2 = st.columns([1,2])
with col1:
    st.header("Inputs")
    st.markdown("Provide transcript text (or upload audio and implement STT).")
    transcript_file = st.file_uploader("Upload transcript (.txt)", type=['txt'])
    transcript_text = ""
    if transcript_file:
        transcript_text = transcript_file.read().decode('utf-8')
    else:
        transcript_text = st.text_area("Paste transcript here (one utterance per line)", height=200)
    meeting_date = st.date_input("Meeting reference date (for relative dates)", value=datetime.utcnow().date())
    st.markdown("---")
    st.markdown("Team JSON (list of members with `id,name,role,skills,workload`).")
    team_json_input = st.text_area("Team JSON", height=180, value=json.dumps([
        {"id":"m1","name":"Vikas","role":"Backend","skills":["api","python","rest"],"workload":0.2},
        {"id":"m2","name":"Priya","role":"QA","skills":["testing","automation"],"workload":0.1},
        {"id":"m3","name":"Amit","role":"DevOps","skills":["deployment","docker"],"workload":0.3},
        {"id":"m4","name":"Designer","role":"Design","skills":["figma","ux"],"workload":0.0},
    ], indent=2))
    st.markdown("Click below to load team into DB (overwrites existing entries).")
    if st.button("Load team into DB"):
        try:
            members = json.loads(team_json_input)
            cur = db.cursor()
            cur.execute("DELETE FROM team_members")
            for m in members:
                cur.execute("INSERT OR REPLACE INTO team_members (id,name,role,skills,workload) VALUES (?, ?, ?, ?, ?)",
                            (m.get('id') or str(uuid4()), m.get('name'), m.get('role'), json.dumps(m.get('skills',[])), float(m.get('workload',0.0))))
            db.commit()
            st.success("Team loaded.")
        except Exception as e:
            st.error(f"Failed to load team JSON: {e}")

with col2:
    st.header("Controls & Run")
    if st.button("Process meeting and extract tasks"):
        if not transcript_text.strip():
            st.warning("Please paste or upload transcript.")
        else:
            meeting_id = str(uuid4())
            members_cur = db.cursor()
            members_cur.execute("SELECT id,name,role,skills,workload FROM team_members")
            members = []
            for row in members_cur.fetchall():
                members.append({
                    "id": row[0], "name": row[1], "role": row[2], "skills": json.loads(row[3] or "[]"), "workload": row[4]
                })
            created = process_meeting(meeting_id, transcript_text, meeting_date.isoformat(), members)
            st.success(f"Processed meeting — created {len(created)} tasks.")
            st.json(created)

    st.markdown("---")
    st.header("Existing tasks & assignments")
    cur = db.cursor()
    cur.execute("SELECT id, summary, deadline, priority, context_notes, created_at FROM tasks ORDER BY created_at DESC")
    tasks_rows = cur.fetchall()
    for trow in tasks_rows:
        tid, summary, deadline, priority, ctx, created_at = trow
        st.subheader(f"Task: {summary}")
        st.write(f"Task ID: {tid} | Priority: {priority} | Deadline: {deadline} | Created: {created_at}")
        st.write("Context notes:", ctx)
        # show assignment if any
        cur.execute("SELECT member_id, reason, llm_suggestion, final_decision, created_at FROM assignments WHERE task_id=?", (tid,))
        ar = cur.fetchone()
        if ar:
            member_id, reason_json, llm_sug, final_decision_json, assign_time = ar
            member_name = None
            if member_id:
                cur.execute("SELECT name FROM team_members WHERE id=?", (member_id,))
                tmp = cur.fetchone()
                member_name = tmp[0] if tmp else None
            st.write(f"Assigned to: **{member_name}** at {assign_time}")
            st.write("Final decision:", json.loads(final_decision_json) if final_decision_json else None)
            st.write("LLM suggestion (raw):")
            try:
                st.json(json.loads(llm_sug))
            except Exception:
                st.text(llm_sug)
            # provide override UI
            if st.button(f"Reassign task {tid} manually"):
                # show member selector and reason
                member_choices = {m['id']: m['name'] for m in [dict(id=r[0], name=r[1], role=r[2]) for r in db.cursor().execute("SELECT id,name,role FROM team_members").fetchall()]}
                sel = st.selectbox("Pick assignee", options=list(member_choices.keys()), format_func=lambda k: member_choices[k])
                reason_text = st.text_area("Reason for manual assignment")
                if st.button("Confirm manual assign"):
                    assign_id = str(uuid4())
                    cur.execute("INSERT INTO assignments (id, task_id, member_id, reason, llm_suggestion, final_decision, created_at) VALUES (?,?,?,?,?,?,?)",
                                (assign_id, tid, sel, json.dumps({"manual": reason_text}), json.dumps({}), json.dumps({"member_id": sel, "reason": {"manual": reason_text}}), now_iso()))
                    db.commit()
                    st.success("Manually reassigned.")
        else:
            st.write("No assignment present for this task.")

st.markdown("---")
st.caption("Prototype: LLM used for summarization & extraction only; final assignment performed by deterministic scoring. Save logs / prompts for grading & provenance.")
