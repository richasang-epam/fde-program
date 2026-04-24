"""
Unit tests for the state machine component.
"""

import pytest
from datetime import datetime

from src.core.state_machine import OnboardingStateMachine
from src.models.onboarding import OnboardingState, Task, TaskType, TaskStatus
from tests.test_data import create_sample_onboarding_instance, TEST_EMPLOYEES


class TestOnboardingStateMachine:
    """Test cases for the onboarding state machine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sm = OnboardingStateMachine()
        self.employee = TEST_EMPLOYEES[0]
        self.instance = create_sample_onboarding_instance(self.employee)

    def test_initial_state(self):
        """Test that new instances start in NEW_HIRE state."""
        assert self.instance.status == OnboardingState.NEW_HIRE

    def test_valid_transitions(self):
        """Test that valid state transitions are allowed."""
        # NEW_HIRE -> IT_PROVISIONING
        assert self.sm.can_transition(OnboardingState.NEW_HIRE, OnboardingState.IT_PROVISIONING)

        # IT_PROVISIONING -> COMPLIANCE_SETUP
        assert self.sm.can_transition(OnboardingState.IT_PROVISIONING, OnboardingState.COMPLIANCE_SETUP)

        # COMPLIANCE_SETUP -> BUDDY_ASSIGN
        assert self.sm.can_transition(OnboardingState.COMPLIANCE_SETUP, OnboardingState.BUDDY_ASSIGN)

        # BUDDY_ASSIGN -> MATERIALS_SHIP
        assert self.sm.can_transition(OnboardingState.BUDDY_ASSIGN, OnboardingState.MATERIALS_SHIP)

        # MATERIALS_SHIP -> MANAGER_HANDOFF
        assert self.sm.can_transition(OnboardingState.MATERIALS_SHIP, OnboardingState.MANAGER_HANDOFF)

        # MANAGER_HANDOFF -> DAY_30_SCHEDULED
        assert self.sm.can_transition(OnboardingState.MANAGER_HANDOFF, OnboardingState.DAY_30_SCHEDULED)

        # DAY_30_SCHEDULED -> COMPLETE
        assert self.sm.can_transition(OnboardingState.DAY_30_SCHEDULED, OnboardingState.COMPLETE)

    def test_invalid_transitions(self):
        """Test that invalid state transitions are not allowed."""
        # Cannot jump states
        assert not self.sm.can_transition(OnboardingState.NEW_HIRE, OnboardingState.COMPLIANCE_SETUP)

        # Cannot go backwards
        assert not self.sm.can_transition(OnboardingState.COMPLIANCE_SETUP, OnboardingState.NEW_HIRE)

        # Cannot transition from COMPLETE
        assert not self.sm.can_transition(OnboardingState.COMPLETE, OnboardingState.NEW_HIRE)

    def test_final_state(self):
        """Test that COMPLETE is recognized as a final state."""
        assert self.sm.is_final_state(OnboardingState.COMPLETE)
        assert not self.sm.is_final_state(OnboardingState.NEW_HIRE)
        assert not self.sm.is_final_state(OnboardingState.IT_PROVISIONING)

    def test_state_transition_triggers(self):
        """Test that tasks trigger appropriate state transitions."""
        # Create a completed task for CREATE_EMPLOYEE_RECORD
        completed_task = Task(
            id="task_001",
            type=TaskType.CREATE_EMPLOYEE_RECORD,
            status=TaskStatus.COMPLETE,
            completed_at=datetime.utcnow()
        )

        # Should trigger NEW_HIRE -> IT_PROVISIONING
        next_state = self.sm.get_next_state(OnboardingState.NEW_HIRE, completed_task)
        assert next_state == OnboardingState.IT_PROVISIONING

    def test_no_transition_for_incomplete_task(self):
        """Test that incomplete tasks don't trigger transitions."""
        # Create an incomplete task
        incomplete_task = Task(
            id="task_001",
            type=TaskType.CREATE_EMPLOYEE_RECORD,
            status=TaskStatus.IN_PROGRESS
        )

        # Should not trigger transition
        next_state = self.sm.get_next_state(OnboardingState.NEW_HIRE, incomplete_task)
        assert next_state is None

    def test_all_states_list(self):
        """Test that all states are included in the states list."""
        states = self.sm.get_all_states()
        expected_states = [
            OnboardingState.NEW_HIRE,
            OnboardingState.IT_PROVISIONING,
            OnboardingState.COMPLIANCE_SETUP,
            OnboardingState.BUDDY_ASSIGN,
            OnboardingState.MATERIALS_SHIP,
            OnboardingState.MANAGER_HANDOFF,
            OnboardingState.DAY_30_SCHEDULED,
            OnboardingState.COMPLETE,
        ]

        assert len(states) == len(expected_states)
        for state in expected_states:
            assert state in states

    def test_state_sequence_validation(self):
        """Test validation of state sequences."""
        # Valid sequence
        valid_sequence = [
            OnboardingState.NEW_HIRE,
            OnboardingState.IT_PROVISIONING,
            OnboardingState.COMPLIANCE_SETUP,
            OnboardingState.BUDDY_ASSIGN,
            OnboardingState.MATERIALS_SHIP,
            OnboardingState.MANAGER_HANDOFF,
            OnboardingState.DAY_30_SCHEDULED,
            OnboardingState.COMPLETE,
        ]
        assert self.sm.validate_state_sequence(valid_sequence)

        # Invalid sequence (skipping states)
        invalid_sequence = [
            OnboardingState.NEW_HIRE,
            OnboardingState.COMPLIANCE_SETUP,  # Skips IT_PROVISIONING
        ]
        assert not self.sm.validate_state_sequence(invalid_sequence)

        # Invalid sequence (going backwards)
        backwards_sequence = [
            OnboardingState.COMPLIANCE_SETUP,
            OnboardingState.NEW_HIRE,
        ]
        assert not self.sm.validate_state_sequence(backwards_sequence)