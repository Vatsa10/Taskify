"""
Automated Task Assignment System from Meeting Recordings
An agentic pipeline for extracting, prioritizing, and assigning tasks from meeting audio
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path

# For speech-to-text (using OpenAI Whisper as example)
# pip install openai-whisper torch
# Alternative: Use any STT API like Google Cloud, Assembly AI, etc.
import whisper

# For NLP processing
# pip install spacy
# python -m spacy download en_core_web_sm
import spacy


# ==================== Data Models ====================

class Priority(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class TeamMember:
    id: int
    name: str
    role: str
    skills: List[str]
    current_workload: int = 0  # Number of assigned tasks
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Task:
    id: Optional[int]
    description: str
    assigned_to: Optional[str]
    priority: Priority
    deadline: Optional[str]
    dependencies: List[int]
    context_notes: str
    assignment_reasoning: str
    extracted_at: str
    meeting_id: int
    
    def to_dict(self):
        d = asdict(self)
        d['priority'] = self.priority.value
        return d


@dataclass
class Meeting:
    id: Optional[int]
    audio_file: str
    transcript: str
    processed_at: str
    tasks_count: int = 0


# ==================== Database Manager ====================

class DatabaseManager:
    def __init__(self, db_path: str = "task_assignment.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Meetings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_file TEXT NOT NULL,
                transcript TEXT,
                processed_at TEXT NOT NULL,
                tasks_count INTEGER DEFAULT 0
            )
        """)
        
        # Team members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                skills TEXT NOT NULL,
                current_workload INTEGER DEFAULT 0
            )
        """)
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                assigned_to TEXT,
                priority TEXT NOT NULL,
                deadline TEXT,
                dependencies TEXT,
                context_notes TEXT,
                assignment_reasoning TEXT,
                extracted_at TEXT NOT NULL,
                meeting_id INTEGER,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def save_meeting(self, meeting: Meeting) -> int:
        """Save meeting and return ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO meetings (audio_file, transcript, processed_at, tasks_count)
            VALUES (?, ?, ?, ?)
        """, (meeting.audio_file, meeting.transcript, meeting.processed_at, meeting.tasks_count))
        
        meeting_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return meeting_id
    
    async def save_task(self, task: Task) -> int:
        """Save task and return ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (description, assigned_to, priority, deadline, 
                             dependencies, context_notes, assignment_reasoning, 
                             extracted_at, meeting_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (task.description, task.assigned_to, task.priority.value, task.deadline,
              json.dumps(task.dependencies), task.context_notes, 
              task.assignment_reasoning, task.extracted_at, task.meeting_id))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    async def save_team_member(self, member: TeamMember) -> int:
        """Save or update team member"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO team_members (name, role, skills, current_workload)
            VALUES (?, ?, ?, ?)
        """, (member.name, member.role, json.dumps(member.skills), member.current_workload))
        
        member_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return member_id
    
    async def get_team_members(self) -> List[TeamMember]:
        """Retrieve all team members"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM team_members")
        rows = cursor.fetchall()
        conn.close()
        
        members = []
        for row in rows:
            members.append(TeamMember(
                id=row[0],
                name=row[1],
                role=row[2],
                skills=json.loads(row[3]),
                current_workload=row[4]
            ))
        return members
    
    async def get_tasks_by_meeting(self, meeting_id: int) -> List[Task]:
        """Retrieve all tasks from a meeting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE meeting_id = ?", (meeting_id,))
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append(Task(
                id=row[0],
                description=row[1],
                assigned_to=row[2],
                priority=Priority(row[3]),
                deadline=row[4],
                dependencies=json.loads(row[5]),
                context_notes=row[6],
                assignment_reasoning=row[7],
                extracted_at=row[8],
                meeting_id=row[9]
            ))
        return tasks


# ==================== Agent 1: Speech-to-Text ====================

class SpeechToTextAgent:
    def __init__(self, model_size: str = "base"):
        """Initialize Whisper model for STT"""
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
    
    async def transcribe(self, audio_path: str) -> str:
        """Convert audio to text"""
        print(f"Transcribing audio file: {audio_path}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            self.model.transcribe, 
            audio_path
        )
        
        transcript = result["text"]
        print(f"Transcription complete: {len(transcript)} characters")
        return transcript


# ==================== Agent 2: Task Extraction ====================

class TaskExtractionAgent:
    def __init__(self):
        """Initialize NLP model for task extraction"""
        print("Loading spaCy NLP model...")
        self.nlp = spacy.load("en_core_web_sm")
        
        # Task indicator keywords
        self.task_keywords = [
            "need to", "should", "must", "have to", "needs to",
            "will", "going to", "can you", "could you",
            "action item", "task", "todo", "to do",
            "responsible for", "assigned to", "work on"
        ]
        
        # Priority keywords
        self.priority_keywords = {
            Priority.CRITICAL: ["critical", "urgent", "asap", "immediately", "emergency"],
            Priority.HIGH: ["high priority", "important", "soon", "quickly"],
            Priority.MEDIUM: ["medium priority", "normal", "regular"],
            Priority.LOW: ["low priority", "when possible", "eventually", "nice to have"]
        }
        
        # Deadline patterns
        self.deadline_patterns = [
            r"by (tomorrow|today|tonight)",
            r"by (monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"by (next week|this week|end of week)",
            r"by (end of|this) month",
            r"in (\d+) (day|days|week|weeks|month|months)",
            r"(tomorrow|today|tonight)",
            r"(next|this) (week|month|quarter)"
        ]
    
    async def extract_tasks(self, transcript: str) -> List[Dict]:
        """Extract tasks from meeting transcript"""
        print("Extracting tasks from transcript...")
        
        # Split transcript into sentences
        doc = self.nlp(transcript)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        tasks = []
        task_id = 0
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            # Check if sentence contains task indicators
            is_task = any(keyword in sentence_lower for keyword in self.task_keywords)
            
            if is_task:
                task_id += 1
                
                # Extract task details
                task = {
                    'id': task_id,
                    'description': sentence,
                    'priority': self._extract_priority(sentence_lower),
                    'deadline': self._extract_deadline(sentence_lower),
                    'context': self._extract_context(sentences, i),
                    'mentioned_names': self._extract_names(sentence)
                }
                
                tasks.append(task)
        
        print(f"Extracted {len(tasks)} tasks")
        return tasks
    
    def _extract_priority(self, text: str) -> Priority:
        """Extract priority level from text"""
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in text for keyword in keywords):
                return priority
        return Priority.MEDIUM  # Default
    
    def _extract_deadline(self, text: str) -> Optional[str]:
        """Extract deadline from text"""
        for pattern in self.deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _extract_context(self, sentences: List[str], index: int, window: int = 2) -> str:
        """Extract surrounding context for a task"""
        start = max(0, index - window)
        end = min(len(sentences), index + window + 1)
        context = " ".join(sentences[start:end])
        return context[:500]  # Limit context length
    
    def _extract_names(self, text: str) -> List[str]:
        """Extract person names from text"""
        doc = self.nlp(text)
        names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        return names


# ==================== Agent 3: Task Assignment ====================

class TaskAssignmentAgent:
    def __init__(self):
        """Initialize assignment logic"""
        self.skill_keywords = {
            'frontend': ['ui', 'interface', 'design', 'frontend', 'react', 'vue', 'css', 'html'],
            'backend': ['api', 'database', 'server', 'backend', 'python', 'java', 'node'],
            'devops': ['deploy', 'deployment', 'ci/cd', 'docker', 'kubernetes', 'aws', 'cloud'],
            'testing': ['test', 'qa', 'quality', 'bug', 'testing', 'automation'],
            'documentation': ['document', 'documentation', 'wiki', 'guide', 'readme'],
            'data': ['data', 'analytics', 'ml', 'machine learning', 'model', 'dataset'],
            'management': ['schedule', 'coordinate', 'organize', 'meeting', 'plan']
        }
    
    async def assign_tasks(self, tasks: List[Dict], team_members: List[TeamMember]) -> List[Task]:
        """Assign tasks to team members based on skills and workload"""
        print("Assigning tasks to team members...")
        
        assigned_tasks = []
        
        for task_data in tasks:
            # Find best match
            best_member, reasoning = self._find_best_assignee(
                task_data, 
                team_members
            )
            
            # Create task object
            task = Task(
                id=None,
                description=task_data['description'],
                assigned_to=best_member.name if best_member else None,
                priority=task_data['priority'],
                deadline=task_data['deadline'],
                dependencies=[],
                context_notes=task_data['context'],
                assignment_reasoning=reasoning,
                extracted_at=datetime.now().isoformat(),
                meeting_id=0  # Will be set later
            )
            
            assigned_tasks.append(task)
            
            # Update workload
            if best_member:
                best_member.current_workload += 1
        
        print(f"Assigned {len(assigned_tasks)} tasks")
        return assigned_tasks
    
    def _find_best_assignee(self, task: Dict, members: List[TeamMember]) -> Tuple[Optional[TeamMember], str]:
        """Find the best team member for a task"""
        task_text = task['description'].lower()
        mentioned_names = task.get('mentioned_names', [])
        
        # Check if someone was explicitly mentioned
        for name in mentioned_names:
            for member in members:
                if name.lower() in member.name.lower():
                    return member, f"Explicitly mentioned in discussion: '{name}'"
        
        # Score each member based on skills
        scores = []
        for member in members:
            score = 0
            matched_skills = []
            
            # Check skill match
            for skill_category, keywords in self.skill_keywords.items():
                if skill_category in [s.lower() for s in member.skills]:
                    for keyword in keywords:
                        if keyword in task_text:
                            score += 2
                            matched_skills.append(skill_category)
                            break
            
            # Penalize for high workload
            workload_penalty = member.current_workload * 0.5
            final_score = score - workload_penalty
            
            scores.append({
                'member': member,
                'score': final_score,
                'matched_skills': matched_skills
            })
        
        # Sort by score
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        if scores and scores[0]['score'] > 0:
            best = scores[0]
            reasoning = f"Best skill match: {', '.join(best['matched_skills'])} (score: {best['score']:.1f})"
            return best['member'], reasoning
        else:
            # Assign to member with lowest workload
            min_workload_member = min(members, key=lambda m: m.current_workload)
            return min_workload_member, "Assigned based on lowest current workload"


# ==================== Agent 4: Dependency Analysis ====================

class DependencyAnalysisAgent:
    async def analyze_dependencies(self, tasks: List[Task]) -> List[Task]:
        """Analyze and link task dependencies"""
        print("Analyzing task dependencies...")
        
        dependency_keywords = [
            "after", "once", "when", "depends on", 
            "requires", "needs", "first", "before"
        ]
        
        for i, task in enumerate(tasks):
            task_text = task.description.lower()
            
            # Check for dependency keywords
            has_dependency = any(keyword in task_text for keyword in dependency_keywords)
            
            if has_dependency and i > 0:
                # Simple heuristic: tasks mentioned earlier are potential dependencies
                # In production, use more sophisticated NLP
                task.dependencies.append(i)  # Reference to previous task
        
        return tasks


# ==================== Main Pipeline Orchestrator ====================

class TaskAssignmentPipeline:
    def __init__(self, db_path: str = "task_assignment.db"):
        """Initialize the complete pipeline"""
        self.db = DatabaseManager(db_path)
        self.stt_agent = SpeechToTextAgent()
        self.extraction_agent = TaskExtractionAgent()
        self.assignment_agent = TaskAssignmentAgent()
        self.dependency_agent = DependencyAnalysisAgent()
    
    async def process_meeting(
        self, 
        audio_file: str, 
        team_members: List[TeamMember]
    ) -> Dict:
        """Process meeting audio end-to-end"""
        print(f"\n{'='*60}")
        print(f"Processing Meeting: {audio_file}")
        print(f"{'='*60}\n")
        
        start_time = datetime.now()
        
        # Stage 1: Speech-to-Text
        transcript = await self.stt_agent.transcribe(audio_file)
        
        # Stage 2: Extract Tasks
        raw_tasks = await self.extraction_agent.extract_tasks(transcript)
        
        if not raw_tasks:
            print("No tasks found in meeting")
            return {
                'meeting_id': None,
                'tasks': [],
                'summary': 'No tasks extracted from meeting'
            }
        
        # Stage 3: Assign Tasks
        assigned_tasks = await self.assignment_agent.assign_tasks(
            raw_tasks, 
            team_members
        )
        
        # Stage 4: Analyze Dependencies
        final_tasks = await self.dependency_agent.analyze_dependencies(assigned_tasks)
        
        # Save to database
        meeting = Meeting(
            id=None,
            audio_file=audio_file,
            transcript=transcript,
            processed_at=datetime.now().isoformat(),
            tasks_count=len(final_tasks)
        )
        meeting_id = await self.db.save_meeting(meeting)
        
        # Save tasks
        for task in final_tasks:
            task.meeting_id = meeting_id
            task.id = await self.db.save_task(task)
        
        # Update team member workloads
        for member in team_members:
            await self.db.save_team_member(member)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = self._generate_summary(final_tasks, processing_time)
        
        print(f"\n{'='*60}")
        print("Processing Complete!")
        print(f"{'='*60}\n")
        print(summary)
        
        return {
            'meeting_id': meeting_id,
            'tasks': [task.to_dict() for task in final_tasks],
            'summary': summary,
            'processing_time': processing_time
        }
    
    def _generate_summary(self, tasks: List[Task], processing_time: float) -> str:
        """Generate summary of processed meeting"""
        summary = f"Processing Time: {processing_time:.2f} seconds\n\n"
        summary += f"Total Tasks Identified: {len(tasks)}\n\n"
        
        # Priority breakdown
        priority_counts = {}
        for task in tasks:
            priority_counts[task.priority.value] = priority_counts.get(task.priority.value, 0) + 1
        
        summary += "Priority Breakdown:\n"
        for priority, count in priority_counts.items():
            summary += f"  - {priority}: {count}\n"
        
        # Assignment breakdown
        assignment_counts = {}
        for task in tasks:
            assignee = task.assigned_to or "Unassigned"
            assignment_counts[assignee] = assignment_counts.get(assignee, 0) + 1
        
        summary += "\nAssignment Breakdown:\n"
        for assignee, count in assignment_counts.items():
            summary += f"  - {assignee}: {count} task(s)\n"
        
        return summary


# ==================== API Interface ====================

async def main_example():
    """Example usage of the pipeline"""
    
    # Initialize pipeline
    pipeline = TaskAssignmentPipeline()
    
    # Define team members
    team_members = [
        TeamMember(
            id=1,
            name="Alice Johnson",
            role="Frontend Developer",
            skills=["React", "JavaScript", "CSS", "UI/UX", "frontend"]
        ),
        TeamMember(
            id=2,
            name="Bob Smith",
            role="Backend Developer",
            skills=["Python", "Django", "PostgreSQL", "API", "backend"]
        ),
        TeamMember(
            id=3,
            name="Carol Martinez",
            role="DevOps Engineer",
            skills=["AWS", "Docker", "Kubernetes", "CI/CD", "devops"]
        ),
        TeamMember(
            id=4,
            name="David Chen",
            role="QA Engineer",
            skills=["Testing", "Selenium", "QA", "Automation", "testing"]
        ),
        TeamMember(
            id=5,
            name="Eve Williams",
            role="Project Manager",
            skills=["Management", "Planning", "Coordination", "management"]
        )
    ]
    
    # Save team members to database
    for member in team_members:
        await pipeline.db.save_team_member(member)
    
    # Process meeting (replace with actual audio file path)
    audio_file = "meeting_recording.wav"
    
    # Check if file exists
    if not Path(audio_file).exists():
        print(f"Error: Audio file '{audio_file}' not found")
        print("\nCreating mock transcript for demonstration...")
        
        # For demo purposes, create a mock transcript
        mock_transcript = """
        Okay team, let's go through the tasks for this sprint. 
        First, Alice, we need you to redesign the user dashboard interface. 
        This is high priority and should be done by Friday.
        Bob, can you work on the API endpoints for the new authentication system? 
        This is critical and we need it by tomorrow.
        Carol, please set up the CI/CD pipeline for the staging environment.
        We need this done this week.
        David, once Bob finishes the authentication API, you'll need to write 
        automated tests for it. This depends on Bob's work.
        Eve, can you schedule a client demo for next week and coordinate with everyone?
        Also, we need to update the project documentation - that's low priority 
        but should be done eventually.
        """
        
        # Directly use extraction and assignment
        raw_tasks = await pipeline.extraction_agent.extract_tasks(mock_transcript)
        assigned_tasks = await pipeline.assignment_agent.assign_tasks(raw_tasks, team_members)
        final_tasks = await pipeline.dependency_agent.analyze_dependencies(assigned_tasks)
        
        # Save mock meeting
        meeting = Meeting(
            id=None,
            audio_file="mock_meeting.txt",
            transcript=mock_transcript,
            processed_at=datetime.now().isoformat(),
            tasks_count=len(final_tasks)
        )
        meeting_id = await pipeline.db.save_meeting(meeting)
        
        for task in final_tasks:
            task.meeting_id = meeting_id
            task.id = await pipeline.db.save_task(task)
        
        print("\n" + "="*60)
        print("EXTRACTED TASKS")
        print("="*60 + "\n")
        
        for task in final_tasks:
            print(f"Task #{task.id}")
            print(f"Description: {task.description}")
            print(f"Assigned To: {task.assigned_to}")
            print(f"Priority: {task.priority.value}")
            print(f"Deadline: {task.deadline or 'Not specified'}")
            print(f"Reasoning: {task.assignment_reasoning}")
            print("-" * 60 + "\n")
        
        return
    
    # Process actual audio file
    result = await pipeline.process_meeting(audio_file, team_members)
    
    # Display results
    print("\nTasks:")
    for task in result['tasks']:
        print(f"\nTask #{task['id']}: {task['description']}")
        print(f"  Assigned to: {task['assigned_to']}")
        print(f"  Priority: {task['priority']}")
        print(f"  Deadline: {task['deadline']}")


if __name__ == "__main__":
    asyncio.run(main_example())
