"""
Test Script for Task Assignment Pipeline
Comprehensive tests for all agents and the full pipeline
"""

import asyncio
import sys
import pytest
from datetime import datetime
from main import (
    TaskAssignmentPipeline,
    TeamMember,
    Priority,
    TaskExtractionAgent,
    TaskAssignmentAgent,
    DependencyAnalysisAgent,
    DatabaseManager
)


# ==================== Test Data ====================

SAMPLE_TEAM = [
    TeamMember(
        id=1,
        name="Alice Johnson",
        role="Frontend Developer",
        skills=["React", "JavaScript", "CSS", "UI", "frontend"]
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
        skills=["Testing", "Selenium", "QA", "testing"]
    )
]

SAMPLE_TRANSCRIPT = """
Good morning team. Let's discuss the tasks for this week.

Alice, we need you to update the user interface for the dashboard. 
This is high priority and must be done by Friday.

Bob, can you implement the new authentication API endpoints? 
This is critical and we need it by tomorrow for the security audit.

Carol, please set up the deployment pipeline for the staging environment.
We need this done by next week.

David, once Bob finishes the API, you'll need to write automated tests.
This should be done by end of week.

Also, someone needs to update the project documentation. 
That's low priority but should be done eventually.
"""


# ==================== Unit Tests ====================

class TestTaskExtractionAgent:
    """Test the task extraction agent"""
    
    def setup_method(self):
        self.agent = TaskExtractionAgent()
    
    async def test_extract_tasks(self):
        """Test basic task extraction"""
        tasks = await self.agent.extract_tasks(SAMPLE_TRANSCRIPT)
        
        assert len(tasks) > 0, "Should extract at least one task"
        assert all('description' in task for task in tasks), "All tasks should have descriptions"
        assert all('priority' in task for task in tasks), "All tasks should have priority"
        
        print(f"✓ Extracted {len(tasks)} tasks from transcript")
    
    async def test_priority_detection(self):
        """Test priority level detection"""
        test_cases = [
            ("This is critical and urgent", Priority.CRITICAL),
            ("This is high priority", Priority.HIGH),
            ("We need to do this", Priority.MEDIUM),
            ("This is a nice to have feature", Priority.LOW)
        ]
        
        for text, expected_priority in test_cases:
            priority = self.agent._extract_priority(text.lower())
            assert priority == expected_priority, f"Failed to detect {expected_priority.value}"
        
        print("✓ Priority detection working correctly")
    
    async def test_deadline_extraction(self):
        """Test deadline extraction"""
        test_cases = [
            "by tomorrow",
            "by Friday",
            "next week",
            "in 3 days"
        ]
        
        for text in test_cases:
            deadline = self.agent._extract_deadline(text)
            assert deadline is not None, f"Failed to extract deadline from: {text}"
        
        print("✓ Deadline extraction working correctly")
    
    async def test_name_extraction(self):
        """Test person name extraction"""
        text = "Alice and Bob need to work on this"
        names = self.agent._extract_names(text)
        
        assert len(names) >= 2, "Should extract at least 2 names"
        assert any("Alice" in name for name in names), "Should extract Alice"
        assert any("Bob" in name for name in names), "Should extract Bob"
        
        print("✓ Name extraction working correctly")


class TestTaskAssignmentAgent:
    """Test the task assignment agent"""
    
    def setup_method(self):
        self.agent = TaskAssignmentAgent()
    
    async def test_skill_based_assignment(self):
        """Test assignment based on skills"""
        tasks = [
            {
                'description': 'Update the React UI components',
                'priority': Priority.HIGH,
                'deadline': 'Friday',
                'context': '',
                'mentioned_names': []
            },
            {
                'description': 'Create new API endpoints with Python',
                'priority': Priority.HIGH,
                'deadline': 'Tomorrow',
                'context': '',
                'mentioned_names': []
            },
            {
                'description': 'Deploy to AWS using Docker',
                'priority': Priority.MEDIUM,
                'deadline': 'Next week',
                'context': '',
                'mentioned_names': []
            }
        ]
        
        assigned_tasks = await self.agent.assign_tasks(tasks, SAMPLE_TEAM)
        
        # Check assignments
        assert assigned_tasks[0].assigned_to == "Alice Johnson", "Frontend task should go to Alice"
        assert assigned_tasks[1].assigned_to == "Bob Smith", "Backend task should go to Bob"
        assert assigned_tasks[2].assigned_to == "Carol Martinez", "DevOps task should go to Carol"
        
        print("✓ Skill-based assignment working correctly")
    
    async def test_explicit_mention_assignment(self):
        """Test assignment when someone is explicitly mentioned"""
        tasks = [
            {
                'description': 'Alice needs to review the code',
                'priority': Priority.HIGH,
                'deadline': None,
                'context': '',
                'mentioned_names': ['Alice']
            }
        ]
        
        assigned_tasks = await self.agent.assign_tasks(tasks, SAMPLE_TEAM)
        
        assert assigned_tasks[0].assigned_to == "Alice Johnson", "Should assign to explicitly mentioned person"
        assert "mentioned" in assigned_tasks[0].assignment_reasoning.lower(), "Reasoning should mention explicit assignment"
        
        print("✓ Explicit mention assignment working correctly")
    
    async def test_workload_balancing(self):
        """Test that workload is considered"""
        # Create team with varying workloads
        team = [
            TeamMember(id=1, name="Alice", role="Developer", skills=["Python"], current_workload=5),
            TeamMember(id=2, name="Bob", role="Developer", skills=["Python"], current_workload=1)
        ]
        
        tasks = [
            {
                'description': 'Python task with no strong skill match',
                'priority': Priority.MEDIUM,
                'deadline': None,
                'context': '',
                'mentioned_names': []
            }
        ]
        
        assigned_tasks = await self.agent.assign_tasks(tasks, team)
        
        # Should prefer Bob due to lower workload
        assert assigned_tasks[0].assigned_to == "Bob", "Should assign to person with lower workload"
        
        print("✓ Workload balancing working correctly")


class TestDependencyAnalysisAgent:
    """Test the dependency analysis agent"""
    
    def setup_method(self):
        self.agent = DependencyAnalysisAgent()
    
    async def test_dependency_detection(self):
        """Test dependency detection"""
        from main import Task
        
        tasks = [
            Task(
                id=1,
                description="Create API endpoint",
                assigned_to="Bob",
                priority=Priority.HIGH,
                deadline="Tomorrow",
                dependencies=[],
                context_notes="",
                assignment_reasoning="",
                extracted_at=datetime.now().isoformat(),
                meeting_id=1
            ),
            Task(
                id=2,
                description="After the API is done, write tests",
                assigned_to="David",
                priority=Priority.MEDIUM,
                deadline="Friday",
                dependencies=[],
                context_notes="",
                assignment_reasoning="",
                extracted_at=datetime.now().isoformat(),
                meeting_id=1
            )
        ]
        
        analyzed_tasks = await self.agent.analyze_dependencies(tasks)
        
        # Second task should have dependency on first
        assert len(analyzed_tasks[1].dependencies) > 0, "Should detect dependency"
        
        print("✓ Dependency detection working correctly")


class TestDatabaseManager:
    """Test database operations"""
    
    def setup_method(self):
        self.db = DatabaseManager("test_database.db")
    
    async def test_save_and_retrieve_team_member(self):
        """Test saving and retrieving team members"""
        member = SAMPLE_TEAM[0]
        member_id = await self.db.save_team_member(member)
        
        assert member_id > 0, "Should return valid ID"
        
        members = await self.db.get_team_members()
        assert len(members) > 0, "Should retrieve team members"
        
        print("✓ Database team member operations working")
    
    async def test_save_meeting_and_tasks(self):
        """Test saving meetings and tasks"""
        from main import Meeting, Task
        
        meeting = Meeting(
            id=None,
            audio_file="test.wav",
            transcript="Test transcript",
            processed_at=datetime.now().isoformat(),
            tasks_count=1
        )
        
        meeting_id = await self.db.save_meeting(meeting)
        assert meeting_id > 0, "Should return valid meeting ID"
        
        task = Task(
            id=None,
            description="Test task",
            assigned_to="Alice",
            priority=Priority.HIGH,
            deadline="Tomorrow",
            dependencies=[],
            context_notes="Test context",
            assignment_reasoning="Test reasoning",
            extracted_at=datetime.now().isoformat(),
            meeting_id=meeting_id
        )
        
        task_id = await self.db.save_task(task)
        assert task_id > 0, "Should return valid task ID"
        
        tasks = await self.db.get_tasks_by_meeting(meeting_id)
        assert len(tasks) == 1, "Should retrieve saved task"
        
        print("✓ Database meeting and task operations working")


# ==================== Integration Tests ====================

class TestFullPipeline:
    """Test the complete pipeline"""
    
    def setup_method(self):
        self.pipeline = TaskAssignmentPipeline("test_full_pipeline.db")
    
    async def test_full_pipeline_mock(self):
        """Test complete pipeline with mock transcript"""
        # Process mock transcript
        raw_tasks = await self.pipeline.extraction_agent.extract_tasks(SAMPLE_TRANSCRIPT)
        assigned_tasks = await self.pipeline.assignment_agent.assign_tasks(raw_tasks, SAMPLE_TEAM)
        final_tasks = await self.pipeline.dependency_agent.analyze_dependencies(assigned_tasks)
        
        # Verify results
        assert len(final_tasks) > 0, "Should extract tasks"
        assert all(task.assigned_to for task in final_tasks), "All tasks should be assigned"
        assert all(task.priority for task in final_tasks), "All tasks should have priority"
        
        # Check specific assignments
        frontend_tasks = [t for t in final_tasks if 'interface' in t.description.lower() or 'ui' in t.description.lower()]
        if frontend_tasks:
            assert frontend_tasks[0].assigned_to == "Alice Johnson", "UI tasks should go to frontend dev"
        
        backend_tasks = [t for t in final_tasks if 'api' in t.description.lower()]
        if backend_tasks:
            assert backend_tasks[0].assigned_to == "Bob Smith", "API tasks should go to backend dev"
        
        print(f"✓ Full pipeline processed {len(final_tasks)} tasks successfully")
        
        # Print task summary
        print("\nTask Summary:")
        for i, task in enumerate(final_tasks, 1):
            print(f"{i}. {task.description[:60]}...")
            print(f"   → Assigned to: {task.assigned_to}")
            print(f"   → Priority: {task.priority.value}")
            print(f"   → Deadline: {task.deadline or 'Not specified'}")


# ==================== Performance Tests ====================

class TestPerformance:
    """Test performance metrics"""
    
    async def test_extraction_speed(self):
        """Test extraction performance"""
        agent = TaskExtractionAgent()
        
        start = datetime.now()
        tasks = await agent.extract_tasks(SAMPLE_TRANSCRIPT)
        duration = (datetime.now() - start).total_seconds()
        
        assert duration < 2.0, f"Extraction took too long: {duration}s"
        print(f"✓ Extraction completed in {duration:.2f}s")
    
    async def test_assignment_speed(self):
        """Test assignment performance"""
        agent = TaskAssignmentAgent()
        
        # Create 20 mock tasks
        tasks = [
            {
                'description': f'Task {i}',
                'priority': Priority.MEDIUM,
                'deadline': None,
                'context': '',
                'mentioned_names': []
            }
            for i in range(20)
        ]
        
        start = datetime.now()
        assigned = await agent.assign_tasks(tasks, SAMPLE_TEAM)
        duration = (datetime.now() - start).total_seconds()
        
        assert duration < 1.0, f"Assignment took too long: {duration}s"
        print(f"✓ Assignment of 20 tasks completed in {duration:.2f}s")


# ==================== Main Test Runner ====================

async def run_all_tests():
    """Run all tests"""
    print("="*70)
    print("TASK ASSIGNMENT SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    test_classes = [
        TestTaskExtractionAgent,
        TestTaskAssignmentAgent,
        TestDependencyAnalysisAgent,
        TestDatabaseManager,
        TestFullPipeline,
        TestPerformance
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{'='*70}")
        print(f"Running {test_class.__name__}")
        print(f"{'='*70}\n")
        
        test_instance = test_class()
        if hasattr(test_instance, 'setup_method'):
            test_instance.setup_method()
        
        # Get all test methods
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                await method()
                passed_tests += 1
                print(f"✓ {method_name} PASSED\n")
            except AssertionError as e:
                print(f"✗ {method_name} FAILED: {e}\n")
            except Exception as e:
                print(f"✗ {method_name} ERROR: {e}\n")
    
    print(f"\n{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
