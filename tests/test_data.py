"""
Test data fixtures for HR Onboarding Agent testing.
"""

from datetime import datetime, timedelta
from src.models.onboarding import (
    OnboardingInstance,
    Task,
    Escalation,
    OnboardingState,
    TaskType,
    System,
    TaskStatus,
    Assignee,
)


# Sample employee data
TEST_EMPLOYEES = [
    {
        "employee_id": "EMP001",
        "email": "john.doe@company.com",
        "name": "John Doe",
        "hire_date": datetime(2024, 1, 15),
        "employment_type": "full-time",
        "jurisdiction": "US",
        "department": "Engineering",
        "job_level": "3",
    },
    {
        "employee_id": "EMP002",
        "email": "jane.smith@company.com",
        "name": "Jane Smith",
        "hire_date": datetime(2024, 1, 16),
        "employment_type": "contractor",
        "jurisdiction": "CA",
        "department": "Marketing",
        "job_level": "2",
    },
    {
        "employee_id": "EMP003",
        "email": "bob.johnson@company.com",
        "name": "Bob Johnson",
        "hire_date": datetime(2024, 1, 17),
        "employment_type": "intern",
        "jurisdiction": "UK",
        "department": "HR",
        "job_level": "1",
    },
]


# Sample tasks for different onboarding states
TASK_TEMPLATES = {
    OnboardingState.NEW_HIRE: [
        {
            "type": TaskType.CREATE_EMPLOYEE_RECORD,
            "system_source": System.WORKDAY,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(hours=2),
        }
    ],
    OnboardingState.IT_PROVISIONING: [
        {
            "type": TaskType.IT_PROVISIONING_REQUEST,
            "system_source": System.SERVICENOW,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(days=1),
        },
        {
            "type": TaskType.EQUIPMENT_REQUEST,
            "system_source": System.SERVICENOW,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(days=1),
        },
    ],
    OnboardingState.COMPLIANCE_SETUP: [
        {
            "type": TaskType.COMPLIANCE_TRAINING_ASSIGN,
            "system_source": System.LMS,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(days=2),
        },
        {
            "type": TaskType.WELCOME_MATERIALS,
            "system_source": System.EMAIL,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(days=1),
        },
    ],
    OnboardingState.BUDDY_ASSIGN: [
        {
            "type": TaskType.BUDDY_MATCHING,
            "system_source": System.WORKDAY,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(days=3),
        },
    ],
    OnboardingState.MATERIALS_SHIP: [
        {
            "type": TaskType.WELCOME_MATERIALS,
            "system_source": System.EMAIL,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(days=1),
        },
    ],
    OnboardingState.MANAGER_HANDOFF: [
        {
            "type": TaskType.MANAGER_HANDOFF,
            "system_source": System.EMAIL,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(days=5),
        },
    ],
    OnboardingState.DAY_30_SCHEDULED: [
        {
            "type": TaskType.DAY_30_CHECKPOINT,
            "system_source": System.EMAIL,
            "assigned_to": Assignee.AGENT,
            "due_date": lambda hire_date: hire_date + timedelta(days=30),
        },
    ],
}


# Sample escalations
SAMPLE_ESCALATIONS = [
    {
        "task_id": "task_001",
        "escalation_type": "UNKNOWN_JURISDICTION",
        "description": "Employee jurisdiction 'XX' not recognized",
        "context": {"jurisdiction": "XX", "employment_type": "full-time"},
        "options_considered": ["Standard US", "International"],
        "recommended_action": "HR Ops to select appropriate compliance track",
    },
    {
        "task_id": "task_002",
        "escalation_type": "SENIORITY_CROSS_NORM",
        "description": "Buddy assignment crosses seniority norms",
        "context": {"employee_level": 1, "buddy_level": 5},
        "options_considered": ["Find peer-level buddy", "Get manager approval"],
        "recommended_action": "HR Ops approval required for cross-level assignment",
    },
    {
        "task_id": "task_003",
        "escalation_type": "E_VERIFY_DELAY",
        "description": "E-Verify process delayed beyond 5 days",
        "context": {"days_pending": 7, "i9_submitted": True},
        "options_considered": ["Wait additional time", "Escalate to legal"],
        "recommended_action": "Escalate to Legal team for review",
    },
]


def create_sample_onboarding_instance(employee_data: dict) -> OnboardingInstance:
    """Create a sample onboarding instance with tasks."""
    instance = OnboardingInstance(
        employee_id=employee_data["employee_id"],
        employee_email=employee_data["email"],
        employee_name=employee_data["name"],
        hire_date=employee_data["hire_date"],
        employment_type=employee_data["employment_type"],
        jurisdiction=employee_data["jurisdiction"],
        department=employee_data["department"],
        job_level=employee_data["job_level"],
    )

    # Add tasks based on current state
    if instance.status in TASK_TEMPLATES:
        for task_template in TASK_TEMPLATES[instance.status]:
            task = Task(
                type=task_template["type"],
                system_source=task_template["system_source"],
                assigned_to=task_template["assigned_to"],
                due_date=task_template["due_date"](instance.hire_date),
            )
            instance.tasks.append(task)

    return instance


def create_sample_tasks_for_instance(instance: OnboardingInstance) -> list[Task]:
    """Create all tasks for a complete onboarding workflow."""
    all_tasks = []

    for state, task_templates in TASK_TEMPLATES.items():
        for task_template in task_templates:
            task = Task(
                type=task_template["type"],
                system_source=task_template["system_source"],
                assigned_to=task_template["assigned_to"],
                due_date=task_template["due_date"](instance.hire_date),
            )
            all_tasks.append(task)

    return all_tasks


# API test data
SAMPLE_WEBHOOK_PAYLOADS = {
    "new_hire": {
        "employee_id": "EMP001",
        "email": "john.doe@company.com",
        "name": "John Doe",
        "hire_date": "2024-01-15",
        "employment_type": "full-time",
        "jurisdiction": "US",
        "department": "Engineering",
        "job_level": "3",
    },
    "task_update": {
        "task_id": "task_123",
        "status": "completed",
        "output": {"result": "success", "details": "Equipment provisioned"}
    },
    "escalation_resolution": {
        "resolution": "approved",
        "output": {"compliance_track": "Standard US Compliance"},
        "resolved_by": "hr_ops_user"
    }
}


# Mock external API responses
MOCK_API_RESPONSES = {
    "workday_create_employee": {
        "status": "success",
        "employee_id": "WD_12345",
        "message": "Employee record created"
    },
    "servicenow_create_ticket": {
        "status": "success",
        "ticket_id": "INC001234",
        "message": "IT provisioning ticket created"
    },
    "lms_assign_course": {
        "status": "success",
        "course_id": "COMP_001",
        "message": "Compliance training assigned"
    },
    "email_send": {
        "status": "success",
        "message_id": "email_123",
        "message": "Welcome email sent"
    }
}