"""
Unit tests for data models and validation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID

from src.models.onboarding import (
    OnboardingInstance,
    Task,
    Escalation,
    OnboardingState,
    TaskType,
    TaskStatus,
    Assignee,
    System,
    NewHireEvent,
    TaskUpdateEvent,
    EscalationResolution,
)
from tests.test_data import TEST_EMPLOYEES, SAMPLE_ESCALATIONS


class TestOnboardingInstance:
    """Test cases for OnboardingInstance model."""

    def test_instance_creation(self):
        """Test creating a valid onboarding instance."""
        employee = TEST_EMPLOYEES[0]

        instance = OnboardingInstance(
            employee_id=employee["employee_id"],
            employee_email=employee["email"],
            employee_name=employee["name"],
            hire_date=employee["hire_date"],
            employment_type=employee["employment_type"],
            jurisdiction=employee["jurisdiction"],
            department=employee["department"],
            job_level=employee["job_level"],
        )

        assert instance.employee_id == "EMP001"
        assert instance.status == OnboardingState.NEW_HIRE
        assert isinstance(instance.id, str)
        assert len(instance.id) > 0
        assert instance.tasks == []
        assert instance.judgment_escalations == []
        assert instance.sla_violations == 0

    def test_instance_with_tasks(self):
        """Test instance with associated tasks."""
        instance = OnboardingInstance(employee_id="EMP001")

        task1 = Task(type=TaskType.CREATE_EMPLOYEE_RECORD)
        task2 = Task(type=TaskType.IT_PROVISIONING_REQUEST)

        instance.tasks = [task1, task2]

        assert len(instance.tasks) == 2
        assert instance.tasks[0].type == TaskType.CREATE_EMPLOYEE_RECORD
        assert instance.tasks[1].type == TaskType.IT_PROVISIONING_REQUEST

    def test_uuid_generation(self):
        """Test that IDs are valid UUIDs."""
        instance = OnboardingInstance(employee_id="EMP001")

        # Should be able to parse as UUID
        uuid_obj = UUID(instance.id)
        assert str(uuid_obj) == instance.id


class TestTask:
    """Test cases for Task model."""

    def test_task_creation(self):
        """Test creating a valid task."""
        due_date = datetime.utcnow() + timedelta(days=1)

        task = Task(
            type=TaskType.CREATE_EMPLOYEE_RECORD,
            system_source=System.WORKDAY,
            assigned_to=Assignee.AGENT,
            due_date=due_date,
        )

        assert task.type == TaskType.CREATE_EMPLOYEE_RECORD
        assert task.system_source == System.WORKDAY
        assert task.assigned_to == Assignee.AGENT
        assert task.status == TaskStatus.PENDING
        assert task.due_date == due_date
        assert task.retry_count == 0
        assert task.completed_at is None

    def test_task_mark_complete(self):
        """Test marking a task as complete."""
        task = Task(type=TaskType.CREATE_EMPLOYEE_RECORD)

        # Initially pending
        assert task.status == TaskStatus.PENDING
        assert task.completed_at is None

        # Mark complete
        task.mark_complete({"result": "success"})

        assert task.status == TaskStatus.COMPLETE
        assert task.completed_at is not None
        assert task.output == {"result": "success"}

    def test_task_with_output(self):
        """Test task completion with output data."""
        task = Task(type=TaskType.IT_PROVISIONING_REQUEST)

        output_data = {
            "ticket_id": "INC001234",
            "status": "approved",
            "equipment": ["laptop", "monitor"]
        }

        task.mark_complete(output_data)

        assert task.output == output_data
        assert task.status == TaskStatus.COMPLETE


class TestEscalation:
    """Test cases for Escalation model."""

    def test_escalation_creation(self):
        """Test creating a valid escalation."""
        escalation_data = SAMPLE_ESCALATIONS[0]

        escalation = Escalation(
            task_id=escalation_data["task_id"],
            escalation_type=escalation_data["escalation_type"],
            description=escalation_data["description"],
            context=escalation_data["context"],
            options_considered=escalation_data["options_considered"],
            recommended_action=escalation_data["recommended_action"],
        )

        assert escalation.task_id == "task_001"
        assert escalation.escalation_type == "UNKNOWN_JURISDICTION"
        assert escalation.description == "Employee jurisdiction 'XX' not recognized"
        assert escalation.context == {"jurisdiction": "XX", "employment_type": "full-time"}
        assert escalation.options_considered == ["Standard US", "International"]
        assert escalation.recommended_action == "HR Ops to select appropriate compliance track"
        assert escalation.resolved_at is None
        assert escalation.resolved_by is None

    def test_escalation_resolution(self):
        """Test resolving an escalation."""
        escalation = Escalation(
            task_id="task_001",
            escalation_type="UNKNOWN_JURISDICTION"
        )

        # Initially unresolved
        assert escalation.resolved_at is None
        assert escalation.resolution is None

        # Resolve it
        resolution_time = datetime.utcnow()
        escalation.resolved_at = resolution_time
        escalation.resolution = "approved"
        escalation.resolved_by = "hr_manager"

        assert escalation.resolved_at == resolution_time
        assert escalation.resolution == "approved"
        assert escalation.resolved_by == "hr_manager"


class TestAPIEventModels:
    """Test cases for API event models."""

    def test_new_hire_event(self):
        """Test NewHireEvent model."""
        event_data = {
            "employee_id": "EMP001",
            "email": "john.doe@company.com",
            "name": "John Doe",
            "hire_date": "2024-01-15",
            "employment_type": "full-time",
            "jurisdiction": "US",
            "department": "Engineering",
            "job_level": "3",
        }

        event = NewHireEvent(**event_data)

        assert event.employee_id == "EMP001"
        assert event.email == "john.doe@company.com"
        assert event.name == "John Doe"
        assert event.hire_date == "2024-01-15"
        assert event.employment_type == "full-time"
        assert event.jurisdiction == "US"
        assert event.department == "Engineering"
        assert event.job_level == "3"

    def test_task_update_event(self):
        """Test TaskUpdateEvent model."""
        event = TaskUpdateEvent(
            task_id="task_123",
            status="completed",
            output={"result": "success"}
        )

        assert event.task_id == "task_123"
        assert event.status == "completed"
        assert event.output == {"result": "success"}

    def test_escalation_resolution(self):
        """Test EscalationResolution model."""
        resolution = EscalationResolution(
            resolution="approved",
            output={"compliance_track": "Standard US"},
            resolved_by="hr_ops_user"
        )

        assert resolution.resolution == "approved"
        assert resolution.output == {"compliance_track": "Standard US"}
        assert resolution.resolved_by == "hr_ops_user"


class TestEnumValues:
    """Test enum value validation."""

    def test_onboarding_states(self):
        """Test all onboarding states are defined."""
        states = [
            OnboardingState.NEW_HIRE,
            OnboardingState.IT_PROVISIONING,
            OnboardingState.COMPLIANCE_SETUP,
            OnboardingState.BUDDY_ASSIGN,
            OnboardingState.MATERIALS_SHIP,
            OnboardingState.MANAGER_HANDOFF,
            OnboardingState.DAY_30_SCHEDULED,
            OnboardingState.COMPLETE,
        ]

        assert len(states) == 8
        for state in states:
            assert isinstance(state.value, str)

    def test_task_types(self):
        """Test all task types are defined."""
        task_types = [
            TaskType.CREATE_EMPLOYEE_RECORD,
            TaskType.BENEFITS_ENROLLMENT,
            TaskType.IT_PROVISIONING_REQUEST,
            TaskType.EQUIPMENT_REQUEST,
            TaskType.COMPLIANCE_TRAINING_ASSIGN,
            TaskType.TRAINING_COMPLETION_TRACK,
            TaskType.WELCOME_MATERIALS,
            TaskType.BUDDY_MATCHING,
            TaskType.I9_DOCUMENT_COLLECTION,
            TaskType.BACKGROUND_CHECK,
            TaskType.MANAGER_HANDOFF,
            TaskType.DAY_30_CHECKPOINT,
        ]

        assert len(task_types) == 12
        for task_type in task_types:
            assert isinstance(task_type.value, str)

    def test_systems(self):
        """Test all systems are defined."""
        systems = [
            System.WORKDAY,
            System.SERVICENOW,
            System.LMS,
            System.EMAIL,
            System.SYSTEM_5,
            System.SYSTEM_6,
        ]

        assert len(systems) == 6
        for system in systems:
            assert isinstance(system.value, str)

    def test_assignees(self):
        """Test all assignees are defined."""
        assignees = [
            Assignee.AGENT,
            Assignee.HR_OPS,
            Assignee.IT,
            Assignee.MANAGER,
        ]

        assert len(assignees) == 4
        for assignee in assignees:
            assert isinstance(assignee.value, str)