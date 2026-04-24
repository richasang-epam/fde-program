"""
State machine implementation for onboarding workflow.
"""

from enum import Enum
from typing import Dict, List, Optional
import logging

from ..models.onboarding import OnboardingState, Task, TaskType

logger = logging.getLogger(__name__)


class OnboardingStateMachine:
    """Manages state transitions for onboarding instances."""

    TRANSITIONS: Dict[OnboardingState, List[OnboardingState]] = {
        OnboardingState.NEW_HIRE: [OnboardingState.IT_PROVISIONING],
        OnboardingState.IT_PROVISIONING: [OnboardingState.COMPLIANCE_SETUP],
        OnboardingState.COMPLIANCE_SETUP: [OnboardingState.BUDDY_ASSIGN],
        OnboardingState.BUDDY_ASSIGN: [OnboardingState.MATERIALS_SHIP],
        OnboardingState.MATERIALS_SHIP: [OnboardingState.MANAGER_HANDOFF],
        OnboardingState.MANAGER_HANDOFF: [OnboardingState.DAY_30_SCHEDULED],
        OnboardingState.DAY_30_SCHEDULED: [OnboardingState.COMPLETE],
        OnboardingState.COMPLETE: []
    }

    # Task completion triggers for state transitions
    STATE_TRIGGERS: Dict[OnboardingState, List[TaskType]] = {
        OnboardingState.NEW_HIRE: [TaskType.CREATE_EMPLOYEE_RECORD],
        OnboardingState.IT_PROVISIONING: [TaskType.IT_PROVISIONING_REQUEST, TaskType.EQUIPMENT_REQUEST],
        OnboardingState.COMPLIANCE_SETUP: [TaskType.COMPLIANCE_TRAINING_ASSIGN],
        OnboardingState.BUDDY_ASSIGN: [TaskType.BUDDY_MATCHING],
        OnboardingState.MATERIALS_SHIP: [TaskType.WELCOME_MATERIALS],
        OnboardingState.MANAGER_HANDOFF: [TaskType.MANAGER_HANDOFF],
        OnboardingState.DAY_30_SCHEDULED: [TaskType.DAY_30_CHECKPOINT],
    }

    def can_transition(self, current_state: OnboardingState, new_state: OnboardingState) -> bool:
        """Check if transition from current to new state is allowed."""
        return new_state in self.TRANSITIONS.get(current_state, [])

    def get_next_state(self, current_state: OnboardingState, completed_task: Task) -> Optional[OnboardingState]:
        """Determine next state based on completed task."""
        trigger_tasks = self.STATE_TRIGGERS.get(current_state, [])

        # Check if the completed task is a trigger for this state
        if completed_task.type in trigger_tasks:
            # Find the next state in the transition chain
            transitions = self.TRANSITIONS.get(current_state, [])
            if transitions:
                next_state = transitions[0]  # Take first allowed transition
                logger.info(f"State transition triggered: {current_state} -> {next_state} (task: {completed_task.type})")
                return next_state

        return None

    def is_final_state(self, state: OnboardingState) -> bool:
        """Check if state is a final state."""
        return state == OnboardingState.COMPLETE

    def get_all_states(self) -> List[OnboardingState]:
        """Get all possible states."""
        return list(OnboardingState)

    def validate_state_sequence(self, states: List[OnboardingState]) -> bool:
        """Validate that a sequence of states is valid."""
        for i in range(len(states) - 1):
            current = states[i]
            next_state = states[i + 1]
            if not self.can_transition(current, next_state):
                logger.error(f"Invalid state transition: {current} -> {next_state}")
                return False
        return True