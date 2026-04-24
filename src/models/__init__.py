"""
Data models package for HR Onboarding Agent.
"""

from .onboarding import (
    OnboardingState,
    TaskType,
    System,
    TaskStatus,
    Assignee,
    Task,
    Escalation,
    OnboardingInstance,
    NewHireEvent,
    TaskUpdateEvent,
    EscalationResolution,
)

__all__ = [
    "OnboardingState",
    "TaskType",
    "System",
    "TaskStatus",
    "Assignee",
    "Task",
    "Escalation",
    "OnboardingInstance",
    "NewHireEvent",
    "TaskUpdateEvent",
    "EscalationResolution",
]