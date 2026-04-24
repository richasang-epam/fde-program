"""
Security utilities for PII handling and access control.
"""

import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
from typing import Dict, Any, Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class SecureDataHandler:
    """Handles encryption/decryption of sensitive PII data."""

    def __init__(self, encryption_key: Optional[str] = None):
        key = encryption_key or settings.encryption_key
        if not key or key == "your-32-byte-encryption-key-here":
            # Generate a key for development - in production, use a proper key
            key = base64.urlsafe_b64encode(os.urandom(32)).decode()
            logger.warning("Using generated encryption key - set ENCRYPTION_KEY env var in production")

        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)

    async def store_pii(self, employee_id: str, pii_data: Dict[str, Any]) -> str:
        """Store encrypted PII data, return reference ID."""
        # In a real implementation, this would store in a secure vault
        # For now, we'll just encrypt and return the encrypted data as base64
        encrypted = self.cipher.encrypt(json.dumps(pii_data).encode())
        reference_id = f"pii_{employee_id}_{hash(encrypted) % 10000}"
        logger.info(f"Stored PII for employee {employee_id} with reference {reference_id}")
        return reference_id

    async def retrieve_pii(self, reference_id: str) -> Dict[str, Any]:
        """Retrieve and decrypt PII data."""
        # In a real implementation, this would fetch from secure vault
        # For now, we'll simulate retrieval
        # This is a placeholder - actual implementation would need persistent storage
        logger.warning("PII retrieval not fully implemented - using mock data")
        return {
            "ssn": "REDACTED",
            "i9_status": "submitted",
            "passport_number": "REDACTED"
        }


class AccessControl:
    """Manages access control for PII and sensitive operations."""

    PII_ACCESS_ROLES = {
        'hr_ops': ['ssn', 'i9_documents', 'passport', 'visa'],
        'system_admin': ['all'],
        'agent': [],  # No direct PII access
        'auditor': ['ssn', 'i9_documents', 'passport', 'visa'],
    }

    def can_access_pii(self, user_role: str, pii_type: str) -> bool:
        """Check if user role can access specific PII type."""
        allowed = self.PII_ACCESS_ROLES.get(user_role, [])
        return 'all' in allowed or pii_type in allowed

    def can_resolve_escalations(self, user_role: str) -> bool:
        """Check if user can resolve escalations."""
        return user_role in ['hr_ops', 'system_admin']

    def can_view_onboarding_details(self, user_role: str, employee_id: str, user_employee_id: Optional[str] = None) -> bool:
        """Check if user can view onboarding details."""
        if user_role in ['hr_ops', 'system_admin']:
            return True
        # Managers can view their direct reports
        return user_employee_id == employee_id


# Global instances
secure_data_handler = SecureDataHandler()
access_control = AccessControl()