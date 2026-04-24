"""
Webhook endpoints for external system integrations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime
from typing import Dict, Any

from ..core.database import get_db
from ..models.onboarding import NewHireEvent, TaskUpdateEvent
from ..agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/workday/new-hire")
async def workday_new_hire(
    event: NewHireEvent,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle new hire events from Workday.

    Triggers the onboarding workflow for a new employee.
    """
    try:
        logger.info(f"Received new hire event for employee {event.employee_id}")

        # Create orchestrator agent
        orchestrator = OrchestratorAgent(db=db)

        # Convert event to employee data dict
        employee_data = {
            "employee_id": event.employee_id,
            "email": event.email,
            "name": event.name,
            "hire_date": datetime.fromisoformat(event.hire_date),
            "employment_type": event.employment_type,
            "jurisdiction": event.jurisdiction,
            "department": event.department,
            "job_level": event.job_level,
        }

        # Process in background to avoid blocking webhook response
        background_tasks.add_task(orchestrator.handle_new_hire, employee_data)

        return {"status": "accepted", "message": f"Onboarding initiated for {event.employee_id}"}

    except Exception as e:
        logger.error(f"Error processing new hire event: {e}")
        raise HTTPException(status_code=500, detail="Failed to process new hire event")


@router.post("/servicenow/task-update")
async def servicenow_task_update(
    event: TaskUpdateEvent,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle task completion updates from ServiceNow.
    """
    try:
        logger.info(f"Received task update for task {event.task_id}: {event.status}")

        # Create orchestrator agent
        orchestrator = OrchestratorAgent(db=db)

        # Process task completion in background
        if event.status == "completed":
            background_tasks.add_task(
                orchestrator.handle_task_completion,
                event.task_id,
                event.output or {}
            )
        elif event.status == "failed":
            # Handle task failure - could trigger retry or escalation
            background_tasks.add_task(
                orchestrator.handle_task_failure,
                event.task_id,
                event.output or {}
            )

        return {"status": "accepted", "message": f"Task update processed for {event.task_id}"}

    except Exception as e:
        logger.error(f"Error processing task update: {e}")
        raise HTTPException(status_code=500, detail="Failed to process task update")


@router.post("/lms/completion-update")
async def lms_completion_update(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle training completion updates from LMS.
    """
    try:
        logger.info(f"Received LMS completion update: {payload}")

        # Extract relevant data from LMS payload
        # This would depend on the specific LMS webhook format
        task_id = payload.get("task_id")
        completion_status = payload.get("status")

        if task_id and completion_status == "completed":
            orchestrator = OrchestratorAgent(db=db)
            background_tasks.add_task(
                orchestrator.handle_task_completion,
                task_id,
                {"completion_data": payload}
            )

        return {"status": "accepted", "message": "LMS update processed"}

    except Exception as e:
        logger.error(f"Error processing LMS update: {e}")
        raise HTTPException(status_code=500, detail="Failed to process LMS update")