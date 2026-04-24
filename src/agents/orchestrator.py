"""
Orchestrator Agent - Manages end-to-end onboarding workflow lifecycle.

This agent handles:
- State machine transitions for onboarding instances
- Dependency graph resolution between tasks
- SLA tracking and overdue task escalation
- Coordination with Task Router, System Adapter, and Judgment Agent
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid


# =============================================================================
# Enums and Constants
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
# Data Models
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
# Task Dependencies - Define what must complete before what
# =============================================================================

TASK_DEPENDENCIES: Dict[TaskType, List[TaskType]] = {
    TaskType.IT_PROVISIONING_REQUEST: [],
    TaskType.EQUIPMENT_REQUEST: [TaskType.IT_PROVISIONING_REQUEST],
    TaskType.COMPLIANCE_TRAINING_ASSIGN: [],
    TaskType.BUDDY_MATCHING: [],  # Can run in parallel with compliance
    TaskType.WELCOME_MATERIALS: [],
    TaskType.I9_DOCUMENT_COLLECTION: [],
    TaskType.BACKGROUND_CHECK: [],
    TaskType.MANAGER_HANDOFF: [
        TaskType.COMPLIANCE_TRAINING_ASSIGN,
        TaskType.IT_PROVISIONING_REQUEST,
    ],
    TaskType.DAY_30_CHECKPOINT: [TaskType.MANAGER_HANDOFF],
}

# SLA windows in hours for each task type
SLA_WINDOWS: Dict[TaskType, int] = {
    TaskType.CREATE_EMPLOYEE_RECORD: 24,
    TaskType.IT_PROVISIONING_REQUEST: 72,
    TaskType.EQUIPMENT_REQUEST: 96,
    TaskType.COMPLIANCE_TRAINING_ASSIGN: 48,
    TaskType.BUDDY_MATCHING: 72,
    TaskType.WELCOME_MATERIALS: 48,
    TaskType.I9_DOCUMENT_COLLECTION: 72,  # 3 days for I-9
    TaskType.BACKGROUND_CHECK: 120,
    TaskType.MANAGER_HANDOFF: 168,  # 7 days
    TaskType.DAY_30_CHECKPOINT: 720,  # 30 days
}


# =============================================================================
# Orchestrator Agent Class
# =============================================================================

class OrchestratorAgent:
    """
    Central orchestrator for HR onboarding workflow.
    
    Responsibilities:
    - Create onboarding instances from new hire events
    - Manage state machine transitions
    - Resolve task dependencies
    - Track SLA compliance
    - Coordinate with sub-agents via message passing
    """
    
    def __init__(self, task_router, system_adapter, judgment_agent, db):
        self.task_router = task_router
        self.system_adapter = system_adapter
        self.judgment_agent = judgment_agent
        self.db = db  # Database interface for persistence
        
        # State machine transition rules
        self.state_transitions = {
            OnboardingState.NEW_HIRE: [OnboardingState.IT_PROVISIONING],
            OnboardingState.IT_PROVISIONING: [OnboardingState.COMPLIANCE_SETUP],
            OnboardingState.COMPLIANCE_SETUP: [OnboardingState.BUDDY_ASSIGN],
            OnboardingState.BUDDY_ASSIGN: [OnboardingState.MATERIALS_SHIP],
            OnboardingState.MATERIALS_SHIP: [OnboardingState.MANAGER_HANDOFF],
            OnboardingState.MANAGER_HANDOFF: [OnboardingState.DAY_30_SCHEDULED],
            OnboardingState.DAY_30_SCHEDULED: [OnboardingState.COMPLETE],
            OnboardingState.COMPLETE: [],
        }
    
    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    
    def create_onboarding(self, employee_data: Dict[str, Any]) -> OnboardingInstance:
        """
        Create a new onboarding instance from a new hire event.
        
        Args:
            employee_data: Dict with keys like employee_id, email, name, 
                          hire_date, employment_type, jurisdiction, department, job_level
        
        Returns:
            Created OnboardingInstance
        """
        instance = OnboardingInstance(
            employee_id=employee_data["employee_id"],
            employee_email=employee_data.get("employee_email", ""),
            employee_name=employee_data.get("employee_name", ""),
            hire_date=employee_data.get("hire_date", datetime.utcnow()),
            employment_type=employee_data.get("employment_type", "full-time"),
            jurisdiction=employee_data.get("jurisdiction", "US"),
            department=employee_data.get("department", ""),
            job_level=employee_data.get("job_level", ""),
        )
        
        # Generate initial task list based on employment type
        instance.tasks = self._generate_initial_tasks(instance)
        
        # Persist to database
        self.db.save_onboarding(instance)
        
        # Trigger first workflow step
        self._advance_state(instance, OnboardingState.IT_PROVISIONING)
        
        return instance
    
    def process_task_result(self, instance_id: str, task_id: str, 
                           result: Dict[str, Any]) -> OnboardingInstance:
        """
        Handle the result of a completed task.
        
        Args:
            instance_id: Onboarding instance ID
            task_id: Completed task ID
            result: Task execution result
        
        Returns:
            Updated OnboardingInstance
        """
        instance = self.db.get_onboarding(instance_id)
        task = next((t for t in instance.tasks if t.id == task_id), None)
        
        if not task:
            raise ValueError(f"Task {task_id} not found in instance {instance_id}")
        
        # Mark task complete
        task.mark_complete(result)
        
        # Check if all tasks in current state are complete
        if self._is_state_complete(instance):
            next_state = self._get_next_state(instance.status)
            if next_state:
                self._advance_state(instance, next_state)
        
        # Check for blocked tasks (dependencies unmet)
        self._check_blocked_tasks(instance)
        
        # Persist updates
        self.db.save_onboarding(instance)
        
        return instance
    
    def check_overdue_tasks(self) -> List[Dict[str, Any]]:
        """
        Daily scan for overdue tasks that need escalation.
        
        Returns:
            List of overdue task dictionaries with instance context
        """
        overdue = []
        now = datetime.utcnow()
        
        all_instances = self.db.get_active_onboardings()
        
        for instance in all_instances:
            for task in instance.tasks:
                if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                    if task.due_date and now > task.due_date:
                        overdue.append({
                            "instance_id": instance.id,
                            "employee_id": instance.employee_id,
                            "employee_name": instance.employee_name,
                            "task_id": task.id,
                            "task_type": task.type.value,
                            "due_date": task.due_date.isoformat(),
                            "hours_overdue": (now - task.due_date).total_seconds() / 3600,
                        })
        
        return overdue
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """
        Get current status of an onboarding instance.
        
        Returns:
            Status dict with state, progress, escalations
        """
        instance = self.db.get_onboarding(instance_id)
        
        return {
            "id": instance.id,
            "employee_id": instance.employee_id,
            "employee_name": instance.employee_name,
            "status": instance.status.value,
            "progress": self._calculate_progress(instance),
            "tasks": [
                {
                    "id": t.id,
                    "type": t.type.value,
                    "status": t.status.value,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                }
                for t in instance.tasks
            ],
            "escalations": len(instance.judgment_escalations),
            "sla_violations": instance.sla_violations,
        }
    
    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------
    
    def _generate_initial_tasks(self, instance: OnboardingInstance) -> List[Task]:
        """Generate the initial task list for a new onboarding."""
        tasks = []
        base_date = instance.hire_date
        
        # Always include these core tasks
        tasks.append(Task(
            type=TaskType.CREATE_EMPLOYEE_RECORD,
            system_source=System.WORKDAY,
            due_date=base_date + timedelta(hours=SLA_WINDOWS[TaskType.CREATE_EMPLOYEE_RECORD]),
        ))
        
        tasks.append(Task(
            type=TaskType.IT_PROVISIONING_REQUEST,
            system_source=System.SERVICENOW,
            due_date=base_date + timedelta(hours=SLA_WINDOWS[TaskType.IT_PROVISIONING_REQUEST]),
        ))
        
        tasks.append(Task(
            type=TaskType.COMPLIANCE_TRAINING_ASSIGN,
            system_source=System.LMS,
            due_date=base_date + timedelta(hours=SLA_WINDOWS[TaskType.COMPLIANCE_TRAINING_ASSIGN]),
        ))
        
        tasks.append(Task(
            type=TaskType.BUDDY_MATCHING,
            system_source=System.EMAIL,
            due_date=base_date + timedelta(hours=SLA_WINDOWS[TaskType.BUDDY_MATCHING]),
        ))
        
        tasks.append(Task(
            type=TaskType.WELCOME_MATERIALS,
            system_source=System.EMAIL,
            due_date=base_date + timedelta(hours=SLA_WINDOWS[TaskType.WELCOME_MATERIALS]),
        ))
        
        # I-9 for US employees
        if instance.jurisdiction == "US":
            tasks.append(Task(
                type=TaskType.I9_DOCUMENT_COLLECTION,
                system_source=System.SYSTEM_5,
                due_date=base_date + timedelta(hours=SLA_WINDOWS[TaskType.I9_DOCUMENT_COLLECTION]),
            ))
        
        # Add manager handoff and day 30 checkpoint
        tasks.append(Task(
            type=TaskType.MANAGER_HANDOFF,
            system_source=System.EMAIL,
            due_date=base_date + timedelta(hours=SLA_WINDOWS[TaskType.MANAGER_HANDOFF]),
        ))
        
        tasks.append(Task(
            type=TaskType.DAY_30_CHECKPOINT,
            system_source=System.WORKDAY,
            due_date=base_date + timedelta(hours=SLA_WINDOWS[TaskType.DAY_30_CHECKPOINT]),
        ))
        
        return tasks
    
    def _advance_state(self, instance: OnboardingInstance, new_state: OnboardingState):
        """Transition to a new workflow state."""
        instance.status = new_state
        instance.last_state_change = datetime.utcnow()
        
        # Route pending tasks for this state to appropriate handlers
        for task in instance.tasks:
            if task.status == TaskStatus.PENDING:
                self._route_task(instance, task)
        
        self.db.save_onboarding(instance)
    
    def _route_task(self, instance: OnboardingInstance, task: Task):
        """Route a task to the appropriate handler (Task Router)."""
        route_decision = self.task_router.route(
            task_type=task.type,
            system_source=task.system_source,
            instance_context={
                "employment_type": instance.employment_type,
                "jurisdiction": instance.jurisdiction,
                "department": instance.department,
                "job_level": instance.job_level,
            }
        )
        
        task.assigned_to = route_decision["assignee"]
        
        if route_decision["requires_judgment"]:
            # Send to Judgment Agent for decision
            judgment_result = self.judgment_agent.evaluate(
                task_type=task.type,
                context=route_decision["context"]
            )
            
            if judgment_result["should_escalate"]:
                task.status = TaskStatus.ESCALATED
                escalation = Escalation(
                    task_id=task.id,
                    escalation_type=judgment_result["escalation_type"],
                    description=judgment_result["description"],
                    context=judgment_result["context"],
                    options_considered=judgment_result["options_considered"],
                    recommended_action=judgment_result["recommended_action"],
                )
                instance.judgment_escalations.append(escalation)
            else:
                # Execute with judgment output
                task.status = TaskStatus.IN_PROGRESS
                self._execute_task(instance, task, judgment_result["output"])
        else:
            # Direct to System Adapter
            task.status = TaskStatus.IN_PROGRESS
            self._execute_task(instance, task, {})
    
    def _execute_task(self, instance: OnboardingInstance, task: Task, 
                     context: Dict[str, Any]):
        """Execute a task via System Adapter."""
        try:
            result = self.system_adapter.execute(
                system=task.system_source,
                operation=task.type.value,
                payload={
                    "employee_id": instance.employee_id,
                    "employee_email": instance.employee_email,
                    "employee_name": instance.employee_name,
                    **context,
                }
            )
            self.process_task_result(instance.id, task.id, result)
        except Exception as e:
            task.error_message = str(e)
            task.retry_count += 1
            if task.retry_count >= 3:
                task.status = TaskStatus.ESCALATED
                # Create escalation for failure
                escalation = Escalation(
                    task_id=task.id,
                    escalation_type="TASK_EXECUTION_FAILURE",
                    description=f"Task failed after 3 retries: {str(e)}",
                    recommended_action="Manual intervention required",
                )
                instance.judgment_escalations.append(escalation)
            self.db.save_onboarding(instance)
    
    def _is_state_complete(self, instance: OnboardingInstance) -> bool:
        """Check if all tasks for the current state are complete."""
        state_task_map = {
            OnboardingState.NEW_HIRE: [TaskType.CREATE_EMPLOYEE_RECORD],
            OnboardingState.IT_PROVISIONING: [TaskType.IT_PROVISIONING_REQUEST],
            OnboardingState.COMPLIANCE_SETUP: [TaskType.COMPLIANCE_TRAINING_ASSIGN],
            OnboardingState.BUDDY_ASSIGN: [TaskType.BUDDY_MATCHING],
            OnboardingState.MATERIALS_SHIP: [TaskType.WELCOME_MATERIALS],
            OnboardingState.MANAGER_HANDOFF: [TaskType.MANAGER_HANDOFF],
            OnboardingState.DAY_30_SCHEDULED: [TaskType.DAY_30_CHECKPOINT],
        }
        
        task_types = state_task_map.get(instance.status, [])
        return all(t.status == TaskStatus.COMPLETE for t in instance.tasks if t.type in task_types)
    
    def _get_next_state(self, current_state: OnboardingState) -> Optional[OnboardingState]:
        """Get the next state in the workflow."""
        return self.state_transitions.get(current_state, [None])[0]
    
    def _check_blocked_tasks(self, instance: OnboardingInstance):
        """Identify tasks blocked by incomplete dependencies."""
        for task in instance.tasks:
            if task.status == TaskStatus.PENDING:
                dependencies = TASK_DEPENDENCIES.get(task.type, [])
                dep_tasks = [t for t in instance.tasks if t.type in dependencies]
                if any(t.status != TaskStatus.COMPLETE for t in dep_tasks):
                    task.status = TaskStatus.BLOCKED
    
    def _calculate_progress(self, instance: OnboardingInstance) -> float:
        """Calculate completion percentage."""
        if not instance.tasks:
            return 0.0
        completed = sum(1 for t in instance.tasks if t.status == TaskStatus.COMPLETE)
        return (completed / len(instance.tasks)) * 100


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Mock dependencies for demonstration
    class MockTaskRouter:
        def route(self, task_type, system_source, instance_context):
            return {
                "assignee": Assignee.AGENT,
                "requires_judgment": task_type in [
                    TaskType.COMPLIANCE_TRAINING_ASSIGN,
                    TaskType.BUDDY_MATCHING,
                    TaskType.I9_DOCUMENT_COLLECTION,
                ],
                "context": instance_context,
            }
    
    class MockSystemAdapter:
        def execute(self, system, operation, payload):
            return {"status": "success", "system": system.value, "operation": operation}
    
    class MockJudgmentAgent:
        def evaluate(self, task_type, context):
            return {
                "should_escalate": False,
                "output": {},
                "escalation_type": None,
            }
    
    class MockDB:
        def __init__(self):
            self.instances = {}
        
        def save_onboarding(self, instance):
            self.instances[instance.id] = instance
        
        def get_onboarding(self, instance_id):
            return self.instances[instance_id]
        
        def get_active_onboardings(self):
            return [i for i in self.instances.values() if i.status != OnboardingState.COMPLETE]
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent(
        task_router=MockTaskRouter(),
        system_adapter=MockSystemAdapter(),
        judgment_agent=MockJudgmentAgent(),
        db=MockDB(),
    )
    
    # Create a new hire onboarding
    new_hire = orchestrator.create_onboarding({
        "employee_id": "EMP-4492",
        "employee_email": "john.doe@company.com",
        "employee_name": "John Doe",
        "hire_date": datetime(2026, 4, 15),
        "employment_type": "full-time",
        "jurisdiction": "US",
        "department": "Engineering",
        "job_level": "L4",
    })
    
    print(f"Created onboarding: {new_hire.id}")
    print(f"Initial status: {new_hire.status.value}")
    print(f"Tasks created: {len(new_hire.tasks)}")
    
    # Check status
    status = orchestrator.get_instance_status(new_hire.id)
    print(f"Progress: {status['progress']}%")