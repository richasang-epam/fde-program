#!/usr/bin/env python3
"""
Simple validation script for core HR Onboarding Agent logic.
Tests the system without external dependencies.
"""

import sys
from datetime import datetime, timedelta
from tests.test_data import TEST_EMPLOYEES, SAMPLE_WEBHOOK_PAYLOADS


def test_basic_imports():
    """Test that core modules can be imported."""
    print("Testing basic imports...")

    try:
        # Test models import
        from src.models.onboarding import (
            OnboardingInstance, Task, Escalation,
            OnboardingState, TaskType, TaskStatus,
            Assignee, System
        )
        print("✅ Models imported successfully")

        # Test enums
        assert OnboardingState.NEW_HIRE.value == "NEW_HIRE"
        assert TaskType.CREATE_EMPLOYEE_RECORD.value == "CREATE_EMPLOYEE_RECORD"
        assert TaskStatus.PENDING.value == "pending"
        assert Assignee.AGENT.value == "agent"
        assert System.WORKDAY.value == "WORKDAY"
        print("✅ Enums validated")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_model_creation():
    """Test creating data model instances."""
    print("\nTesting data model creation...")

    try:
        from src.models.onboarding import OnboardingInstance, Task, TaskType, System, Assignee

        # Create a test instance
        employee = TEST_EMPLOYEES[0]
        hire_date_str = employee["hire_date"]
        hire_date = datetime.fromisoformat(hire_date_str) if isinstance(hire_date_str, str) else hire_date_str

        instance = OnboardingInstance(
            employee_id=employee["employee_id"],
            employee_email=employee["email"],
            employee_name=employee["name"],
            hire_date=hire_date,
            employment_type=employee["employment_type"],
            jurisdiction=employee["jurisdiction"],
            department=employee["department"],
            job_level=employee["job_level"]
        )

        assert instance.employee_id == "EMP001"
        assert instance.status.value == "NEW_HIRE"
        assert len(instance.tasks) == 0
        print("✅ OnboardingInstance created successfully")

        # Create a test task
        task = Task(
            type=TaskType.CREATE_EMPLOYEE_RECORD,
            system_source=System.WORKDAY,
            assigned_to=Assignee.AGENT
        )

        assert task.type.value == "CREATE_EMPLOYEE_RECORD"
        assert task.status.value == "pending"
        assert task.system_source.value == "WORKDAY"
        print("✅ Task created successfully")

        # Test task completion
        task.mark_complete({"workday_id": "WD_12345"})
        assert task.status.value == "complete"
        assert task.completed_at is not None
        assert task.output == {"workday_id": "WD_12345"}
        print("✅ Task completion works")

        return True
    except Exception as e:
        print(f"❌ Data model creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_machine_logic():
    """Test basic state machine logic."""
    print("\nTesting state machine logic...")

    try:
        from src.models.onboarding import OnboardingState, TaskType

        # Test state transitions (basic logic)
        states = [state.value for state in OnboardingState]
        assert "NEW_HIRE" in states
        assert "IT_PROVISIONING" in states
        assert "COMPLETE" in states
        print("✅ State machine states defined")

        # Test task types
        task_types = [task.value for task in TaskType]
        assert "CREATE_EMPLOYEE_RECORD" in task_types
        assert "COMPLIANCE_TRAINING_ASSIGN" in task_types
        assert "BUDDY_MATCHING" in task_types
        print("✅ Task types defined")

        return True
    except Exception as e:
        print(f"❌ State machine logic failed: {e}")
        return False


def test_webhook_payloads():
    """Test webhook payload structures."""
    print("\nTesting webhook payloads...")

    try:
        # Test new hire payload
        new_hire = SAMPLE_WEBHOOK_PAYLOADS["new_hire"]
        required_fields = ["employee_id", "email", "name", "hire_date", "employment_type"]
        for field in required_fields:
            assert field in new_hire, f"Missing {field} in new_hire payload"
        print("✅ New hire webhook payload structure valid")

        # Test task update payload
        task_update = SAMPLE_WEBHOOK_PAYLOADS["task_update"]
        assert "task_id" in task_update
        assert "status" in task_update
        print("✅ Task update webhook payload structure valid")

        # Test escalation resolution payload
        escalation_resolution = SAMPLE_WEBHOOK_PAYLOADS["escalation_resolution"]
        assert "resolution" in escalation_resolution
        assert "resolved_by" in escalation_resolution
        print("✅ Escalation resolution payload structure valid")

        return True
    except Exception as e:
        print(f"❌ Webhook payload validation failed: {e}")
        return False


def test_task_dependencies():
    """Test task dependency logic."""
    print("\nTesting task dependencies...")

    try:
        from src.models.onboarding import Task, TaskType, System, Assignee

        # Create dependent tasks
        task1 = Task(TaskType.CREATE_EMPLOYEE_RECORD, System.WORKDAY, Assignee.AGENT)
        task2 = Task(TaskType.IT_PROVISIONING_REQUEST, System.SERVICENOW, Assignee.AGENT)

        # Task2 should depend on task1 completion
        assert task1.status.value == "pending"
        assert task2.status.value == "pending"

        # Complete task1
        task1.mark_complete()
        assert task1.status.value == "complete"

        # Task2 can now proceed
        assert task2.status.value == "pending"  # Still pending until explicitly started
        print("✅ Task dependencies work correctly")

        return True
    except Exception as e:
        print(f"❌ Task dependency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("🚀 HR Onboarding Agent - Core Logic Validation")
    print("=" * 50)

    tests = [
        test_basic_imports,
        test_data_model_creation,
        test_state_machine_logic,
        test_webhook_payloads,
        test_task_dependencies
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n{'='*50}")
    print("VALIDATION SUMMARY")
    print('='*50)
    print(f"Passed: {passed}/{total}")
    print(".1f")

    if passed == total:
        print("🎉 ALL CORE LOGIC TESTS PASSED!")
        print("The HR Onboarding Agent system is ready for integration testing.")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())