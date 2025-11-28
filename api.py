"""
FastAPI REST API for Task Assignment System
Provides endpoints for uploading audio, managing team members, and retrieving tasks
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import shutil
from pathlib import Path
import uvicorn

# Import from main pipeline
from main import (
    TaskAssignmentPipeline,
    TeamMember,
    Priority,
    DatabaseManager
)


app = FastAPI(
    title="Meeting Task Assignment API",
    description="Automatically extract and assign tasks from meeting recordings",
    version="1.0.0"
)

# Global pipeline instance
pipeline = TaskAssignmentPipeline()

# Storage directory for uploaded files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ==================== Request/Response Models ====================

class TeamMemberCreate(BaseModel):
    name: str
    role: str
    skills: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice Johnson",
                "role": "Frontend Developer",
                "skills": ["React", "JavaScript", "CSS", "frontend"]
            }
        }


class TeamMemberResponse(BaseModel):
    id: int
    name: str
    role: str
    skills: List[str]
    current_workload: int


class TaskResponse(BaseModel):
    id: int
    description: str
    assigned_to: Optional[str]
    priority: str
    deadline: Optional[str]
    dependencies: List[int]
    context_notes: str
    assignment_reasoning: str
    extracted_at: str
    meeting_id: int


class MeetingProcessResponse(BaseModel):
    meeting_id: int
    tasks_count: int
    processing_time: float
    summary: str
    tasks: List[dict]


class StatusResponse(BaseModel):
    status: str
    message: str


# ==================== API Endpoints ====================

@app.get("/", tags=["General"])
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Meeting Task Assignment API",
        "version": "1.0.0"
    }


@app.post("/team-members/", response_model=TeamMemberResponse, tags=["Team Members"])
async def create_team_member(member: TeamMemberCreate):
    """
    Create a new team member
    """
    try:
        team_member = TeamMember(
            id=None,
            name=member.name,
            role=member.role,
            skills=member.skills,
            current_workload=0
        )
        
        member_id = await pipeline.db.save_team_member(team_member)
        team_member.id = member_id
        
        return TeamMemberResponse(
            id=team_member.id,
            name=team_member.name,
            role=team_member.role,
            skills=team_member.skills,
            current_workload=team_member.current_workload
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/team-members/", response_model=List[TeamMemberResponse], tags=["Team Members"])
async def get_team_members():
    """
    Get all team members
    """
    try:
        members = await pipeline.db.get_team_members()
        return [
            TeamMemberResponse(
                id=m.id,
                name=m.name,
                role=m.role,
                skills=m.skills,
                current_workload=m.current_workload
            )
            for m in members
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/meetings/process", response_model=MeetingProcessResponse, tags=["Meetings"])
async def process_meeting(
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload and process a meeting audio file
    
    Accepts .wav, .mp3, or .m4a files
    """
    # Validate file type
    allowed_extensions = ['.wav', '.mp3', '.m4a']
    file_ext = Path(audio_file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    file_path = UPLOAD_DIR / audio_file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Get team members
    try:
        team_members = await pipeline.db.get_team_members()
        
        if not team_members:
            raise HTTPException(
                status_code=400, 
                detail="No team members found. Please add team members first."
            )
        
        # Process meeting
        result = await pipeline.process_meeting(str(file_path), team_members)
        
        return MeetingProcessResponse(
            meeting_id=result['meeting_id'],
            tasks_count=len(result['tasks']),
            processing_time=result['processing_time'],
            summary=result['summary'],
            tasks=result['tasks']
        )
    
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/meetings/{meeting_id}/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def get_meeting_tasks(meeting_id: int):
    """
    Get all tasks from a specific meeting
    """
    try:
        tasks = await pipeline.db.get_tasks_by_meeting(meeting_id)
        
        if not tasks:
            raise HTTPException(status_code=404, detail="Meeting not found or has no tasks")
        
        return [
            TaskResponse(
                id=task.id,
                description=task.description,
                assigned_to=task.assigned_to,
                priority=task.priority.value,
                deadline=task.deadline,
                dependencies=task.dependencies,
                context_notes=task.context_notes,
                assignment_reasoning=task.assignment_reasoning,
                extracted_at=task.extracted_at,
                meeting_id=task.meeting_id
            )
            for task in tasks
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/meetings/process-mock", response_model=MeetingProcessResponse, tags=["Meetings"])
async def process_mock_meeting():
    """
    Process a mock meeting transcript for testing (no audio file required)
    """
    try:
        # Get team members
        team_members = await pipeline.db.get_team_members()
        
        if not team_members:
            raise HTTPException(
                status_code=400, 
                detail="No team members found. Please add team members first."
            )
        
        # Mock transcript
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
        
        # Process without STT
        from datetime import datetime
        from main import Meeting
        
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
        
        # Update workloads
        for member in team_members:
            await pipeline.db.save_team_member(member)
        
        return MeetingProcessResponse(
            meeting_id=meeting_id,
            tasks_count=len(final_tasks),
            processing_time=0.5,
            summary=pipeline._generate_summary(final_tasks, 0.5),
            tasks=[task.to_dict() for task in final_tasks]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/reset-database", response_model=StatusResponse, tags=["Admin"])
async def reset_database():
    """
    Reset the entire database (use with caution!)
    """
    try:
        import os
        db_path = pipeline.db.db_path
        
        if Path(db_path).exists():
            os.remove(db_path)
        
        # Reinitialize
        pipeline.db.init_db()
        
        return StatusResponse(
            status="success",
            message="Database has been reset"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Starting Meeting Task Assignment API...")
    print(f"Upload directory: {UPLOAD_DIR.absolute()}")
    print("API is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down API...")


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
