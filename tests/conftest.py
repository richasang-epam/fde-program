"""
Test configuration and fixtures.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock

# Try to import optional dependencies
try:
    from src.core.config import Settings
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing."""
    orchestrator = AsyncMock()
    orchestrator.handle_new_hire.return_value = AsyncMock()
    orchestrator.handle_task_completion.return_value = None
    orchestrator.get_onboarding_instance.return_value = AsyncMock()
    orchestrator.resolve_escalation.return_value = True
    orchestrator.get_pending_escalations.return_value = []
    return orchestrator


@pytest.fixture
def test_settings():
    """Test settings fixture."""
    if not CORE_AVAILABLE:
        pytest.skip("Core modules not available")
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        debug=True,
        openai_api_key="test_key",
        encryption_key="test_encryption_key_32_chars_long_",
        jwt_secret_key="test_jwt_secret_key"
    )


# Mock external API responses
@pytest.fixture
def mock_workday_api():
    """Mock Workday API responses."""
    return {
        "create_employee": {"status": "success", "id": "WD_12345"},
        "get_employee": {"status": "success", "data": {"name": "John Doe"}},
        "enroll_benefits": {"status": "success", "plan_id": "BEN_001"}
    }


@pytest.fixture
def mock_servicenow_api():
    """Mock ServiceNow API responses."""
    return {
        "create_incident": {"status": "success", "number": "INC001234"},
        "get_incident": {"status": "success", "state": "resolved"},
        "create_request": {"status": "success", "number": "REQ005678"}
    }


@pytest.fixture
def mock_lms_api():
    """Mock LMS API responses."""
    return {
        "assign_course": {"status": "success", "assignment_id": "ASS_001"},
        "get_completion": {"status": "completed", "score": 95},
        "get_courses": {"status": "success", "courses": ["COMP_001"]}
    }


@pytest.fixture
def mock_email_api():
    """Mock Email API responses."""
    return {
        "send_email": {"status": "success", "message_id": "MSG_001"},
        "get_status": {"status": "delivered"}
    }
    orchestrator.resolve_escalation.return_value = True
    orchestrator.get_pending_escalations.return_value = []
    return orchestrator


@pytest.fixture
def test_settings():
    """Test settings fixture."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        debug=True,
        openai_api_key="test_key",
        encryption_key="test_encryption_key_32_chars_long_",
        jwt_secret_key="test_jwt_secret_key"
    )


# Mock external API responses
@pytest.fixture
def mock_workday_api():
    """Mock Workday API responses."""
    return {
        "create_employee": {"status": "success", "id": "WD_12345"},
        "get_employee": {"status": "success", "data": {"name": "John Doe"}},
        "enroll_benefits": {"status": "success", "plan_id": "BEN_001"}
    }


@pytest.fixture
def mock_servicenow_api():
    """Mock ServiceNow API responses."""
    return {
        "create_incident": {"status": "success", "number": "INC001234"},
        "get_incident": {"status": "success", "state": "resolved"},
        "create_request": {"status": "success", "number": "REQ005678"}
    }


@pytest.fixture
def mock_lms_api():
    """Mock LMS API responses."""
    return {
        "assign_course": {"status": "success", "assignment_id": "ASS_001"},
        "get_completion": {"status": "completed", "score": 95},
        "get_courses": {"status": "success", "courses": ["COMP_001"]}
    }


@pytest.fixture
def mock_email_api():
    """Mock Email API responses."""
    return {
        "send_email": {"status": "success", "message_id": "MSG_001"},
        "get_status": {"status": "delivered"}
    }