"""
Data models for the HR Onboarding Agent system.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


# =============================================================================
# Enums
# =============================================================================

class OnboardingState(str, Enum):
    """State machine states for onboarding lifecycle."""
    NEW_HIRE = "NEW_HIRE"
    IT_PROVISIONING = "IT_PROVISIONING"
    COMPLIANCE_SETUP = "COMPLIANCE_SETUP"
    BUDDY_ASSIGN = "BUDDY_ASSIGN"
    MATERIALS_SHIP = "MATERIALS_SHIP"
    MANAGER_HANDOFF = "MANAGER_HANDOFF"
    DAY_30_SCHEDULED = "DAY_30_SCHEDULED"
    COMPLETE = "COMPLETE"


class TaskType(str, Enum):
    """Task types within onboarding workflow."""
    CREATE_EMPLOYEE_RECORD = "CREATE_EMPLOYEE_RECORD"
    BENEFITS_ENROLLMENT = "BENEFITS_ENROLLMENT"
    IT_PROVISIONING_REQUEST = "IT_PROVISIONING_REQUEST"
    EQUIPMENT_REQUEST = "EQUIPMENT_REQUEST"
    COMPLIANCE_TRAINING_ASSIGN = "COMPLIANCE_TRAINING_ASSIGN"
    TRAINING_COMPLETION_TRACK = "TRAINING_COMPLETION_TRACK"
    WELCOME_MATERIALS = "WELCOME_MATERIALS"
    BUDDY_MATCHING = "BUDDY_MATCHING"
    I9_DOCUMENT_COLLECTION = "I9_DOCUMENT_COLLECTION"
    BACKGROUND_CHECK = "BACKGROUND_CHECK"
    MANAGER_HANDOFF = "MANAGER_HANDOFF"
    DAY_30_CHECKPOINT = "DAY_30_CHECKPOINT"


class System(str, Enum):
    """Source systems for tasks."""
    WORKDAY = "WORKDAY"
    SERVICENOW = "SERVICENOW"
    LMS = "LMS"
    EMAIL = "EMAIL"
    SYSTEM_5 = "SYSTEM_5"
    SYSTEM_6 = "SYSTEM_6"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    ESCALATED = "escalated"


class Assignee(str, Enum):
    """Task assignment targets."""
    AGENT = "agent"
    HR_OPS = "hr-ops"
    IT = "it"
    MANAGER = "manager"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Task:
    """Individual task within an onboarding instance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType = TaskType.CREATE_EMPLOYEE_RECORD
    system_source: System = System.WORKDAY
    assigned_to: Assignee = Assignee.AGENT
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def mark_complete(self, output: Optional[Dict[str, Any]] = None):
        self.status = TaskStatus.COMPLETE
        self.completed_at = datetime.utcnow()
        if output:
            self.output = output


@dataclass
class Escalation:
    """Escalation record for human review."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    escalation_type: str = ""
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    options_considered: List[str] = field(default_factory=list)
    recommended_action: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None


@dataclass
class OnboardingInstance:
    """Complete onboarding workflow instance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str = ""
    employee_email: str = ""
    employee_name: str = ""
    hire_date: datetime = field(default_factory=datetime.utcnow)
    employment_type: str = "full-time"  # full-time, contractor, intern
    jurisdiction: str = "US"
    department: str = ""
    job_level: str = ""
    status: OnboardingState = OnboardingState.NEW_HIRE
    tasks: List[Task] = field(default_factory=list)
    judgment_escalations: List[Escalation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # SLA tracking
    sla_violations: int = 0
    last_state_change: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# API Models
# =============================================================================

@dataclass
class NewHireEvent:
    """Webhook payload for new hire events."""
    employee_id: str
    email: str
    name: str
    hire_date: str  # ISO date string
    employment_type: str
    jurisdiction: str
    department: str
    job_level: str


@dataclass
class TaskUpdateEvent:
    """Webhook payload for task completion updates."""
    task_id: str
    status: str  # "completed" or "failed"
    output: Optional[Dict[str, Any]] = None


@dataclass
class EscalationResolution:
    """Payload for resolving escalations."""
    resolution: str  # "approved", "rejected", "manual_override"
    resolved_by: str
    output: Optional[Dict[str, Any]] = None


# Import uuid here to avoid circular imports
import uuid