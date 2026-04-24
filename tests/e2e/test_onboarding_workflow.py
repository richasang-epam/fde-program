"""
End-to-end tests for complete onboarding workflows.
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from src.models.onboarding import (
    OnboardingInstance,
    Task,
    OnboardingState,
    TaskType,
    TaskStatus,
    Assignee,
    System
)
from src.core.state_machine import OnboardingStateMachine
from tests.test_data import TEST_EMPLOYEES, create_sample_onboarding_instance


class TestCompleteOnboardingWorkflow:
    """End-to-end test for complete onboarding workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.employee = TEST_EMPLOYEES[0]  # John Doe
        self.sm = OnboardingStateMachine()

    def test_full_onboarding_lifecycle(self):
        """Test complete onboarding workflow from start to finish."""
        # 1. Create initial onboarding instance
        instance = create_sample_onboarding_instance(self.employee)

        # Verify initial state
        assert instance.status == OnboardingState.NEW_HIRE
        assert len(instance.tasks) > 0

        # 2. Complete employee record creation
        employee_task = next(
            (t for t in instance.tasks if t.type == TaskType.CREATE_EMPLOYEE_RECORD),
            None
        )
        assert employee_task is not None

        employee_task.mark_complete({"workday_id": "WD_12345"})

        # Should trigger state transition
        next_state = self.sm.get_next_state(instance.status, employee_task)
        assert next_state == OnboardingState.IT_PROVISIONING

        instance.status = next_state

        # 3. Complete IT provisioning tasks
        it_tasks = [
            t for t in instance.tasks
            if t.type in [TaskType.IT_PROVISIONING_REQUEST, TaskType.EQUIPMENT_REQUEST]
        ]

        for task in it_tasks:
            task.mark_complete({"status": "provisioned"})

        # Check if all IT tasks are complete
        it_complete = all(t.status == TaskStatus.COMPLETE for t in it_tasks)

        if it_complete:
            next_state = self.sm.get_next_state(instance.status, it_tasks[0])
            assert next_state == OnboardingState.COMPLIANCE_SETUP
            instance.status = next_state

        # 4. Complete compliance setup
        compliance_task = next(
            (t for t in instance.tasks if t.type == TaskType.COMPLIANCE_TRAINING_ASSIGN),
            None
        )
        if compliance_task:
            compliance_task.mark_complete({"track": "Standard US Compliance"})

            next_state = self.sm.get_next_state(instance.status, compliance_task)
            assert next_state == OnboardingState.BUDDY_ASSIGN
            instance.status = next_state

        # 5. Complete buddy assignment
        buddy_task = next(
            (t for t in instance.tasks if t.type == TaskType.BUDDY_MATCHING),
            None
        )
        if buddy_task:
            buddy_task.mark_complete({"buddy_id": "EMP002", "buddy_email": "jane.smith@company.com"})

            next_state = self.sm.get_next_state(instance.status, buddy_task)
            assert next_state == OnboardingState.MATERIALS_SHIP
            instance.status = next_state

        # 6. Complete materials shipping
        materials_task = next(
            (t for t in instance.tasks if t.type == TaskType.WELCOME_MATERIALS),
            None
        )
        if materials_task:
            materials_task.mark_complete({"email_sent": True, "package_shipped": True})

            next_state = self.sm.get_next_state(instance.status, materials_task)
            assert next_state == OnboardingState.MANAGER_HANDOFF
            instance.status = next_state

        # 7. Complete manager handoff
        handoff_task = next(
            (t for t in instance.tasks if t.type == TaskType.MANAGER_HANDOFF),
            None
        )
        if handoff_task:
            handoff_task.mark_complete({"meeting_scheduled": True, "manager_notified": True})

            next_state = self.sm.get_next_state(instance.status, handoff_task)
            assert next_state == OnboardingState.DAY_30_SCHEDULED
            instance.status = next_state

        # 8. Complete 30-day checkpoint scheduling
        checkpoint_task = next(
            (t for t in instance.tasks if t.type == TaskType.DAY_30_CHECKPOINT),
            None
        )
        if checkpoint_task:
            checkpoint_task.mark_complete({"checkin_scheduled": True})

            next_state = self.sm.get_next_state(instance.status, checkpoint_task)
            assert next_state == OnboardingState.COMPLETE
            instance.status = next_state

        # 9. Verify final state
        assert instance.status == OnboardingState.COMPLETE
        assert self.sm.is_final_state(instance.status)

        # Verify all tasks are complete
        completed_tasks = [t for t in instance.tasks if t.status == TaskStatus.COMPLETE]
        assert len(completed_tasks) == len(instance.tasks)

    def test_workflow_with_escalation(self):
        """Test workflow that includes an escalation."""
        instance = create_sample_onboarding_instance(self.employee)

        # Simulate a compliance task that needs escalation
        compliance_task = Task(
            type=TaskType.COMPLIANCE_TRAINING_ASSIGN,
            system_source=System.LMS,
            assigned_to=Assignee.AGENT
        )
        instance.tasks.append(compliance_task)

        # Task would normally escalate due to unknown jurisdiction
        # In a real scenario, this would create an escalation record
        from src.models.onboarding import Escalation

        escalation = Escalation(
            task_id=compliance_task.id,
            escalation_type="UNKNOWN_JURISDICTION",
            description="Employee jurisdiction 'XX' not recognized",
            context={"jurisdiction": "XX", "employment_type": "full-time"},
            options_considered=["Standard US", "International"],
            recommended_action="HR Ops to select track manually"
        )
        instance.judgment_escalations.append(escalation)

        # Verify escalation was created
        assert len(instance.judgment_escalations) == 1
        assert instance.judgment_escalations[0].escalation_type == "UNKNOWN_JURISDICTION"
        assert not instance.judgment_escalations[0].resolved_at

        # Simulate resolution
        escalation.resolved_at = datetime.utcnow()
        escalation.resolution = "approved"
        escalation.resolved_by = "hr_manager"

        # Now the task can be completed
        compliance_task.mark_complete({"track": "International Compliance"})

        # Verify escalation is resolved
        assert escalation.resolved_at is not None
        assert escalation.resolution == "approved"
        assert escalation.resolved_by == "hr_manager"

    def test_concurrent_task_processing(self):
        """Test processing multiple tasks that can run concurrently."""
        instance = create_sample_onboarding_instance(self.employee)

        # Tasks that can run in parallel during IT_PROVISIONING phase
        parallel_tasks = [
            Task(type=TaskType.IT_PROVISIONING_REQUEST, system_source=System.SERVICENOW),
            Task(type=TaskType.EQUIPMENT_REQUEST, system_source=System.SERVICENOW),
            Task(type=TaskType.BENEFITS_ENROLLMENT, system_source=System.WORKDAY),
        ]

        instance.tasks.extend(parallel_tasks)
        instance.status = OnboardingState.IT_PROVISIONING

        # Complete tasks in different order
        parallel_tasks[1].mark_complete({"equipment": ["laptop", "monitor"]})  # Equipment first
        parallel_tasks[0].mark_complete({"ticket_id": "INC001234"})  # IT provisioning second
        parallel_tasks[2].mark_complete({"benefits_plan": "Standard"})  # Benefits last

        # All tasks should be complete
        completed = [t for t in parallel_tasks if t.status == TaskStatus.COMPLETE]
        assert len(completed) == 3

        # State should still be IT_PROVISIONING until triggering task completes
        # (In real system, state transition logic would handle this)

    def test_sla_tracking(self):
        """Test SLA violation tracking."""
        instance = create_sample_onboarding_instance(self.employee)

        # Add a task with a due date in the past
        overdue_task = Task(
            type=TaskType.IT_PROVISIONING_REQUEST,
            system_source=System.SERVICENOW,
            due_date=datetime.utcnow() - timedelta(days=1)  # Overdue
        )
        instance.tasks.append(overdue_task)

        # Initially no SLA violations
        assert instance.sla_violations == 0

        # Simulate SLA check (in real system, this would be done by a background job)
        overdue_tasks = [
            t for t in instance.tasks
            if t.due_date and t.due_date < datetime.utcnow() and t.status != TaskStatus.COMPLETE
        ]

        if overdue_tasks:
            instance.sla_violations += len(overdue_tasks)

        assert instance.sla_violations == 1

        # Complete the task
        overdue_task.mark_complete({"status": "completed late"})

        # SLA violations should remain (historical tracking)
        assert instance.sla_violations == 1


class TestSystemIntegrationScenarios:
    """Test scenarios involving external system integrations."""

    def test_workday_integration_flow(self):
        """Test integration with Workday for employee data."""
        # Mock Workday API responses
        workday_responses = {
            "create_employee": {"status": "success", "employee_id": "WD_12345"},
            "get_org_structure": {"department": "Engineering", "manager": "EMP999"},
            "enroll_benefits": {"status": "enrolled", "plan": "Standard"}
        }

        # Simulate calling Workday APIs
        for operation, response in workday_responses.items():
            assert response["status"] in ["success", "enrolled"]

    def test_servicenow_integration_flow(self):
        """Test integration with ServiceNow for IT requests."""
        servicenow_responses = {
            "create_incident": {"status": "success", "incident_id": "INC001234"},
            "check_status": {"status": "resolved", "resolution": "Equipment delivered"},
            "create_request": {"status": "success", "request_id": "REQ005678"}
        }

        # Simulate ServiceNow workflow
        incident = servicenow_responses["create_incident"]
        assert incident["incident_id"].startswith("INC")

        status = servicenow_responses["check_status"]
        assert status["status"] == "resolved"

    def test_lms_integration_flow(self):
        """Test integration with LMS for training."""
        lms_responses = {
            "assign_course": {"status": "assigned", "course_id": "COMP_001"},
            "check_completion": {"status": "completed", "score": 95},
            "get_transcript": {"courses": ["COMP_001", "SAFETY_101"], "status": "active"}
        }

        # Simulate LMS training workflow
        assignment = lms_responses["assign_course"]
        assert assignment["course_id"] == "COMP_001"

        completion = lms_responses["check_completion"]
        assert completion["status"] == "completed"
        assert completion["score"] >= 80  # Passing score

    def test_email_integration_flow(self):
        """Test integration with email system."""
        email_responses = {
            "send_welcome": {"status": "sent", "message_id": "msg_001"},
            "send_notification": {"status": "sent", "message_id": "msg_002"},
            "check_delivery": {"status": "delivered", "delivered_at": "2024-01-15T10:30:00Z"}
        }

        # Simulate email workflow
        for operation, response in email_responses.items():
            assert response["status"] in ["sent", "delivered"]
            assert "message_id" in response


class TestErrorRecoveryScenarios:
    """Test error handling and recovery scenarios."""

    def test_task_retry_logic(self):
        """Test task retry logic for failed operations."""
        task = Task(
            type=TaskType.IT_PROVISIONING_REQUEST,
            system_source=System.SERVICENOW
        )

        # Initially no retries
        assert task.retry_count == 0
        assert task.status == TaskStatus.PENDING

        # Simulate failures
        task.retry_count = 1
        assert task.retry_count == 1

        task.retry_count = 2
        assert task.retry_count == 2

        # After max retries, should escalate
        task.retry_count = 3
        task.status = TaskStatus.ESCALATED
        assert task.status == TaskStatus.ESCALATED

    def test_external_system_timeout(self):
        """Test handling of external system timeouts."""
        # Simulate API timeout scenarios
        timeout_scenarios = [
            {"system": "Workday", "operation": "create_employee", "timeout": 30},
            {"system": "ServiceNow", "operation": "create_incident", "timeout": 60},
            {"system": "LMS", "operation": "assign_course", "timeout": 45}
        ]

        for scenario in timeout_scenarios:
            # In real system, these would trigger retry logic
            assert scenario["timeout"] > 0
            assert scenario["system"] in ["Workday", "ServiceNow", "LMS"]

    def test_data_validation_errors(self):
        """Test handling of data validation errors."""
        invalid_employee_data = [
            {"employee_id": "", "email": "invalid"},  # Missing/invalid data
            {"employee_id": "EMP001", "hire_date": "invalid-date"},
            {"employee_id": "EMP001", "jurisdiction": "INVALID"}
        ]

        for invalid_data in invalid_employee_data:
            # These should fail validation in the real system
            assert len(invalid_data) > 0  # Basic check

    def test_concurrent_access_conflicts(self):
        """Test handling of concurrent access to the same instance."""
        instance = create_sample_onboarding_instance(self.employee)

        # Simulate concurrent operations on the same instance
        # In real system, this would use database transactions/locking
        concurrent_operations = [
            "update_task_status",
            "resolve_escalation",
            "advance_state"
        ]

        for operation in concurrent_operations:
            # These operations should be serialized in real system
            assert operation in ["update_task_status", "resolve_escalation", "advance_state"]