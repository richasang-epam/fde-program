"""
REST API endpoints for the HR Onboarding Agent.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.security import access_control
from ..models.onboarding import EscalationResolution
from ..agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.get("/onboarding/{employee_id}")
async def get_onboarding_status(
    employee_id: str,
    user_role: str = Query(..., description="User role for access control"),
    user_employee_id: Optional[str] = Query(None, description="User's employee ID for manager access"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get onboarding status for an employee.
    """
    try:
        # Access control check
        if not access_control.can_view_onboarding_details(user_role, employee_id, user_employee_id):
            raise HTTPException(status_code=403, detail="Access denied")

        orchestrator = OrchestratorAgent(db=db)
        instance = await orchestrator.get_onboarding_instance(employee_id)

        if not instance:
            raise HTTPException(status_code=404, detail="Onboarding instance not found")

        # Convert to API response format
        response = {
            "id": instance.id,
            "employee_id": instance.employee_id,
            "status": instance.status.value,
            "hire_date": instance.hire_date.isoformat(),
            "employment_type": instance.employment_type,
            "jurisdiction": instance.jurisdiction,
            "department": instance.department,
            "job_level": instance.job_level,
            "created_at": instance.created_at.isoformat(),
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "tasks": [
                {
                    "id": task.id,
                    "type": task.type.value,
                    "status": task.status.value,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }
                for task in instance.tasks
            ],
            "escalations": [
                {
                    "id": esc.id,
                    "task_id": esc.task_id,
                    "escalation_type": esc.escalation_type,
                    "description": esc.description,
                    "recommended_action": esc.recommended_action,
                    "created_at": esc.created_at.isoformat(),
                    "resolved_at": esc.resolved_at.isoformat() if esc.resolved_at else None,
                    "resolved_by": esc.resolved_by,
                }
                for esc in instance.judgment_escalations
            ]
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting onboarding status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get onboarding status")


@router.post("/escalations/{escalation_id}/resolve")
async def resolve_escalation(
    escalation_id: str,
    resolution: EscalationResolution,
    user_role: str = Query(..., description="User role for access control"),
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve a human-reviewed escalation.
    """
    try:
        # Access control check
        if not access_control.can_resolve_escalations(user_role):
            raise HTTPException(status_code=403, detail="Access denied - insufficient permissions")

        orchestrator = OrchestratorAgent(db=db)
        success = await orchestrator.resolve_escalation(
            escalation_id,
            resolution.resolution,
            resolution.output,
            resolution.resolved_by
        )

        if not success:
            raise HTTPException(status_code=404, detail="Escalation not found or already resolved")

        return {"status": "success", "message": "Escalation resolved"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving escalation: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve escalation")


@router.get("/escalations/pending")
async def get_pending_escalations(
    user_role: str = Query(..., description="User role for access control"),
    limit: int = Query(50, description="Maximum number of escalations to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending escalations for review.
    """
    try:
        # Access control check
        if not access_control.can_resolve_escalations(user_role):
            raise HTTPException(status_code=403, detail="Access denied - insufficient permissions")

        orchestrator = OrchestratorAgent(db=db)
        escalations = await orchestrator.get_pending_escalations(limit)

        # Convert to API response format
        response = [
            {
                "id": esc.id,
                "task_id": esc.task_id,
                "escalation_type": esc.escalation_type,
                "description": esc.description,
                "context": esc.context,
                "options_considered": esc.options_considered,
                "recommended_action": esc.recommended_action,
                "created_at": esc.created_at.isoformat(),
            }
            for esc in escalations
        ]

        return {"escalations": response, "count": len(response)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending escalations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending escalations")


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "timestamp": "2024-01-15T10:00:00Z"}