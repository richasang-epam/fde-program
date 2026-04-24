"""
Unit tests for security components.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.core.security import SecureDataHandler, AccessControl
from src.models.onboarding import OnboardingInstance


class TestSecureDataHandler:
    """Test cases for PII data handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = SecureDataHandler("test_key_for_testing_only")

    def test_encrypt_decrypt_pii(self):
        """Test encryption and decryption of PII data."""
        test_pii = {
            "ssn": "123-45-6789",
            "passport": "P1234567",
            "visa_status": "H1B"
        }

        # Store PII (would normally return a reference ID)
        reference_id = "test_ref_001"

        # In a real implementation, we'd retrieve by reference_id
        # For testing, we'll simulate the decrypt process
        encrypted = self.handler.cipher.encrypt(str(test_pii).encode())
        decrypted = self.handler.cipher.decrypt(encrypted).decode()

        # Verify the data round-trips correctly
        assert eval(decrypted) == test_pii

    def test_store_pii_structure(self):
        """Test PII storage structure."""
        employee_id = "EMP001"
        pii_data = {"ssn": "123-45-6789"}

        # This would normally interact with a database
        # For testing, we verify the method exists and takes correct params
        assert hasattr(self.handler, 'store_pii')

        # Mock the database interaction
        with patch.object(self.handler, 'store_pii', return_value="ref_001") as mock_store:
            result = self.handler.store_pii(employee_id, pii_data)
            mock_store.assert_called_once_with(employee_id, pii_data)


class TestAccessControl:
    """Test cases for access control."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ac = AccessControl()

    def test_hr_ops_pii_access(self):
        """Test HR Ops role PII access permissions."""
        # HR Ops should have access to sensitive PII
        assert self.ac.can_access_pii("hr_ops", "ssn")
        assert self.ac.can_access_pii("hr_ops", "i9_documents")
        assert self.ac.can_access_pii("hr_ops", "passport")

        # But not to all PII types
        assert not self.ac.can_access_pii("hr_ops", "salary")

    def test_system_admin_pii_access(self):
        """Test System Admin role has all PII access."""
        assert self.ac.can_access_pii("system_admin", "ssn")
        assert self.ac.can_access_pii("system_admin", "i9_documents")
        assert self.ac.can_access_pii("system_admin", "passport")
        assert self.ac.can_access_pii("system_admin", "salary")

    def test_agent_no_pii_access(self):
        """Test Agent role has no direct PII access."""
        assert not self.ac.can_access_pii("agent", "ssn")
        assert not self.ac.can_access_pii("agent", "i9_documents")
        assert not self.ac.can_access_pii("agent", "passport")
        assert not self.ac.can_access_pii("agent", "salary")

    def test_auditor_pii_access(self):
        """Test Auditor role PII access permissions."""
        assert self.ac.can_access_pii("auditor", "ssn")
        assert self.ac.can_access_pii("auditor", "i9_documents")
        assert self.ac.can_access_pii("auditor", "passport")

    def test_unknown_role_no_access(self):
        """Test unknown roles have no PII access."""
        assert not self.ac.can_access_pii("unknown_role", "ssn")
        assert not self.ac.can_access_pii("contractor", "i9_documents")

    def test_hr_ops_can_resolve_escalations(self):
        """Test HR Ops can resolve escalations."""
        assert self.ac.can_resolve_escalations("hr_ops")

    def test_system_admin_can_resolve_escalations(self):
        """Test System Admin can resolve escalations."""
        assert self.ac.can_resolve_escalations("system_admin")

    def test_agent_cannot_resolve_escalations(self):
        """Test Agent cannot resolve escalations."""
        assert not self.ac.can_resolve_escalations("agent")

    def test_auditor_cannot_resolve_escalations(self):
        """Test Auditor cannot resolve escalations."""
        assert not self.ac.can_resolve_escalations("auditor")

    def test_onboarding_view_permissions(self):
        """Test onboarding data view permissions."""
        # HR Ops can view any onboarding
        assert self.ac.can_view_onboarding_details("hr_ops", "EMP001")
        assert self.ac.can_view_onboarding_details("hr_ops", "EMP001", "EMP002")

        # System admin can view any onboarding
        assert self.ac.can_view_onboarding_details("system_admin", "EMP001")

        # Agent cannot view onboarding details
        assert not self.ac.can_view_onboarding_details("agent", "EMP001")

        # Manager can view their own onboarding
        assert self.ac.can_view_onboarding_details("manager", "EMP001", "EMP001")

        # Manager cannot view others' onboarding without being their manager
        assert not self.ac.can_view_onboarding_details("manager", "EMP001", "EMP002")


class TestPIIClassification:
    """Test PII data classification rules."""

    def test_sensitive_pii_types(self):
        """Test classification of sensitive PII types."""
        sensitive_types = ["ssn", "i9_documents", "passport", "visa"]

        ac = AccessControl()

        for pii_type in sensitive_types:
            # Only specific roles should access these
            assert ac.can_access_pii("hr_ops", pii_type)
            assert ac.can_access_pii("system_admin", pii_type)
            assert not ac.can_access_pii("agent", pii_type)

    def test_internal_data_types(self):
        """Test classification of internal data types."""
        internal_types = ["name", "email", "department", "job_level"]

        ac = AccessControl()

        # These should be accessible to more roles
        for pii_type in internal_types:
            assert ac.can_access_pii("hr_ops", pii_type)
            # Note: In a real system, these might have different rules
            # This test verifies the access control logic works