# Scenario 1: HR Onboarding Coordination — Solution Deliverables

> **Scenario**: A regional professional-services firm (1,200 employees, 220+ hires/year) runs new-hire onboarding through a 3-person HR Ops team. Each onboarding spans ~40 tasks across 2 weeks: IT provisioning, benefits enrolment, compliance training assignment, buddy matching, welcome materials, 30-day checkpoint scheduling, and manager handoff. Tasks originate from 6 different systems. Roughly 15% require judgment calls — which compliance track applies to a contractor versus a full employee, whether a buddy assignment crosses seniority norms, whether a late I-9 triggers a hold.

> **Client Quote**: "Most of this is paperwork my team should not be touching, but every time we try to automate, something falls through the cracks because the edge cases never look the same twice."

---

## 1. Problem Statement & Success Metrics

### 1.1 User Problem Statement

**From the HR Ops team perspective:**
- **Pain**: Manual coordination of ~8,800 task instances per year (220 hires × 40 tasks) consumes 1,500+ hours annually — time that could be spent on strategic HR work
- **Pain**: Every automation attempt breaks on the 15% of edge cases that don't fit rigid if-then logic, requiring manual rescue that defeats the automation ROI
- **Pain**: No visibility into onboarding bottlenecks until something fails; reactive firefighting rather than proactive management

**From the business perspective:**
- **Risk**: Inconsistent onboarding experience affects new hire productivity and retention
- **Risk**: Compliance training gaps create regulatory exposure (I-9, harassment training)
- **Cost**: 3 FTEs spent on coordination tasks that don't require human judgment

### 1.2 Success Metrics

| Metric | Current Baseline | Target | Justification |
|--------|------------------|--------|---------------|
| **Task automation rate** | 0% (all manual) | >85% handled without human touch | Absorbs routine 85%, freeing HR Ops for judgment work |
| **Escalation accuracy** | N/A (no agent) | <10% returned as "wrong routing" | Ensures agent isn't flooding HR Ops with misrouted tasks |
| **On-time completion** | Unknown (manual tracking) | >95% within SLA | Replaces ad hoc with systematic SLA enforcement |
| **HR Ops time savings** | 0 hours saved | >60% reduction in coordination hours | Justifies investment; 900+ hours reclaimed annually |
| **Mean time to resolve escalation** | Unknown | <4 hours during business hours | Prevents escalations from stalling |
| **Onboarding completion rate** | Unknown | >90% completed within 14 days | Ensures agent doesn't create new delays |

### 1.3 Investment Justification

- **Annual HR Ops hours reclaimed**: 1,500 × 60% = **900 hours**
- **Fully loaded cost of HR Ops**: Assume $50/hr = **$45,000/year** in reclaimed capacity
- **Avoided risk**: I-9 compliance failures, missed training deadlines
- **Scalability**: Agent handles 220 or 400 hires without adding headcount

---

## 2. Delegation Analysis

### 2.1 Workflow Decomposition

| Task Category | Task Type | Frequency | Judgment Required? | Delegation Decision | Justification |
|---------------|-----------|-----------|--------------------|---------------------|---------------|
| **Employee Record** | Create in Workday | Per hire | No | **Fully Agentic** | Deterministic CRUD; no contextual judgment |
| **Benefits** | Enroll in benefits plan | Per hire (FT/contractor) | No | **Fully Agentic** | Rule-based eligibility mapping; no ambiguity |
| **IT Provisioning** | Create ServiceNow ticket | Per hire | No | **Fully Agentic** | Standard catalog request; deterministic |
| **Equipment** | Laptop, monitor, access | Per hire | No | **Fully Agentic** | Standard equipment matrix by role |
| **Compliance Training** | Assign training track | Per hire | **Yes** — employment type → track mapping | **Agent-Led + Human Oversight** | Judgment required on contractor vs. FT vs. intern track selection; escalate unknown jurisdictions |
| **Training Completion** | Track completion status | Per hire | No | **Fully Agentic** | Polling LMS API; deterministic pass/fail |
| **Buddy Matching** | Assign onboarding buddy | Per hire | **Yes** — seniority compatibility, team proximity, availability | **Agent-Led + Human Oversight** | Score-based matching with threshold; escalate cross-norm assignments (e.g., >2 level gap) |
| **Welcome Materials** | Send welcome email/package | Per hire | No | **Fully Agentic** | Template-based; deterministic |
| **I-9 Document Collection** | Collect I-9 forms | US hires only | **Yes** — timing trigger (Day 3 hold), late I-9 logging | **Agent-Led + Human Oversight** | Agent monitors timing, triggers hold, but human reviews documents |
| **Background Check** | Initiate/track BG check | Per hire | No | **Fully Agentic** | API polling; deterministic status |
| **Manager Handoff** | Notify manager, schedule 1:1 | Per hire | No | **Fully Agentic** | Template notification; deterministic |
| **Day 30 Checkpoint** | Schedule 30-day review | Per hire | No | **Fully Agentic** | Calendar scheduling; deterministic |

### 2.2 Delegation Boundary Justification

**Fully Agentic (85% of tasks):**
- Tasks where input → output is deterministic
- No contextual reasoning required
- Failure mode is retryable (transient API failures)
- No regulatory or reputational risk if agent errs

**Agent-Led + Human Oversight (15% of tasks):**
- Tasks where agent makes recommendation but human must approve
- Clear escalation triggers defined (unknown jurisdiction, seniority cross-norm, confidence threshold)
- Agent provides context, options considered, and recommendation — human makes final call
- Human decisions fed back to agent as training signals

**Why not fully agentic on judgment tasks?**
- **Compliance**: Wrong training track = regulatory exposure (harassment training gaps)
- **Social**: Bad buddy match = new hire isolation, manager complaints
- **Legal**: I-9 errors = immigration compliance violations
- **Trust**: HR Ops won't adopt system they don't verify

### 2.3 Human-in-the-Loop Design

```
┌─────────────────────────────────────────────────────────────┐
│                    DELEGATION MATRIX                        │
├─────────────────────────────────────────────────────────────┤
│  Fully Agentic          │  Agent-Led + Oversight  │ Human  │
│  ─────────────────      │  ─────────────────────  │ ─────  │
│  • Employee create      │  • Compliance track     │ (none) │
│  • Benefits enroll      │  • Buddy matching       │        │
│  • IT ticket create     │  • I-9 timing holds     │        │
│  • Equipment request    │  • Unknown jurisdiction │        │
│  • Training assign      │  • Cross-norm buddy     │        │
│  • Completion tracking  │                         │        │
│  • BG check poll        │                         │        │
│  • Welcome email        │                         │        │
│  • Manager notify       │                         │        │
│  • 30-day schedule      │                         │        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Specification

### 3.1 Architecture Overview

```
                    ┌──────────────────┐
                    │  Orchestrator    │
                    │    Agent         │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│  Task Router    │  │ System       │  │  Judgment       │
│  Agent          │  │ Adapter      │  │  Agent          │
└─────────────────┘  └──────────────┘  └─────────────────┘
```

### 3.2 Orchestrator Agent

**Purpose**: End-to-end workflow management, state machine transitions, dependency resolution, SLA tracking.

**Inputs**:
- New hire event (Workday webhook or polling)
- Employee data: `employee_id`, `email`, `name`, `hire_date`, `employment_type`, `jurisdiction`, `department`, `job_level`

**Outputs**:
- Onboarding instance with task list
- State transitions logged
- SLA violation alerts

**Decision Logic**:
```
1. On new hire event → create OnboardingInstance
2. Generate task list based on employment_type + jurisdiction
3. For each task:
   a. Check dependencies (TASK_DEPENDENCIES graph)
   b. If dependencies met → route to Task Router
   c. If dependencies unmet → mark BLOCKED
4. On task completion:
   a. Mark complete
   b. If all tasks in state complete → advance state
   c. Check for newly unblocked tasks
5. Daily: scan for overdue tasks → escalate to Task Router
```

**OnboardingInstance State Machine**:
- `INITIATED` → `IT_PROVISIONING`: when the instance is created and IT/system access provisioning begins.
- `IT_PROVISIONING` → `COMPLIANCE_SETUP`: when core IT provisioning tasks are complete and compliance assignment can start.
- `COMPLIANCE_SETUP` → `ACTIVE`: when required compliance training, I-9 collection, and buddy matching are either complete or safely delegated to in-flight processes.
- `ACTIVE` → `COMPLETE`: when all onboarding tasks are finished and the employee is fully onboarded.
- Any state → `ON_HOLD`: when a blocker is detected, such as missing I-9 documentation, unknown jurisdiction, or a required human escalation.
- `ON_HOLD` → previous active state: when the blocker is resolved and the instance can resume normal progress.

**State Transition Conditions**:
- `INITIATED` to `IT_PROVISIONING`: triggered by new hire creation and initial task generation.
- `IT_PROVISIONING` to `COMPLIANCE_SETUP`: triggered when IT-related tasks (access, equipment, accounts) reach completion or are in a safe pending state.
- `COMPLIANCE_SETUP` to `ACTIVE`: triggered when compliance onboarding tasks either complete successfully or enter approved exception workflows.
- `ACTIVE` to `COMPLETE`: triggered when the remaining task set is empty and all SLA-guarded checks are satisfied.
- `ON_HOLD` entry: triggered by a hard blocker, manual hold request, or unresolved judgment escalation.
- `ON_HOLD` exit: triggered when the underlying blocker is cleared and task processing can resume.

**Escalation Triggers**:
- Task overdue > SLA window → escalate to HR Ops
- Task failed after 3 retries → escalate to HR Ops

**Integration Points**:
- Task Router: `route(task_type, system_source, context)`
- System Adapter: `execute(system, operation, payload)`
- Judgment Agent: `evaluate(task_type, context)`
- Database: persist OnboardingInstance, Task, Escalation

### 3.3 Task Router Agent

**Purpose**: Classify tasks, determine handler, apply routing rules.

**Inputs**:
- `task_type`: TaskType enum
- `system_source`: System enum
- `instance_context`: `{employment_type, jurisdiction, department, job_level}`

**Outputs**:
```python
{
    "assignee": Assignee,  # agent | hr-ops | it | manager
    "requires_judgment": bool,
    "context": dict,  # passed to judgment agent if needed
}
```

**Routing Rules**:

| Task Type | Default Handler | Requires Judgment? |
|-----------|-----------------|--------------------|
| CREATE_EMPLOYEE_RECORD | AGENT | No |
| BENEFITS_ENROLLMENT | AGENT | No |
| IT_PROVISIONING_REQUEST | AGENT | No |
| EQUIPMENT_REQUEST | AGENT | No |
| COMPLIANCE_TRAINING_ASSIGN | AGENT | **Yes** — context includes employment_type |
| TRAINING_COMPLETION_TRACK | AGENT | No |
| WELCOME_MATERIALS | AGENT | No |
| BUDDY_MATCHING | AGENT | **Yes** — context includes job_level, department |
| I9_DOCUMENT_COLLECTION | AGENT | **Yes** — context includes hire_date |
| BACKGROUND_CHECK | AGENT | No |
| MANAGER_HANDOFF | AGENT | No |
| DAY_30_CHECKPOINT | AGENT | No |

### 3.4 Judgment Agent

**Purpose**: Evaluate edge cases, make recommendations or escalate.

**Inputs**:
- `task_type`: TaskType
- `context`: `{employment_type, jurisdiction, department, job_level, hire_date, ...}`

**Outputs**:
```python
{
    "should_escalate": bool,
    "escalation_type": str | None,  # e.g., "UNKNOWN_JURISDICTION", "SENIORITY_CROSS_NORM"
    "description": str,
    "options_considered": List[str],
    "recommended_action": str,
    "output": dict,  # if not escalating
}
```

**Decision Logic**:

**A. Compliance Track Selection**:
```
IF employment_type == "contractor" → track = "Contractor Compliance"
ELSE IF employment_type == "intern" → track = "Intern Safety & Ethics"
ELSE IF jurisdiction not in KNOWN_JURISDICTIONS → should_escalate = TRUE
    escalation_type = "UNKNOWN_JURISDICTION"
    options_considered = ["Standard US", "International (if known)"]
    recommended_action = "HR Ops to select track manually"
ELSE → track = "Standard " + jurisdiction + " Compliance"
```

**B. Buddy Matching**:
```
FOR each potential buddy:
    score = 0
    IF same_team → score += 2
    IF level_gap <= 2 → score += 1
    IF level_gap > 2 → score -= 1  (penalty for cross-norm)
    IF previous_buddy_failed → score -= 2
    IF calendar_available → score += 1

IF max(score) < THRESHOLD (3) → should_escalate = TRUE
    escalation_type = "NO_COMPATIBLE_BUDDY"
ELSE IF best_buddy.level - hire.level > 2 → should_escalate = TRUE
    escalation_type = "SENIORITY_CROSS_NORM"
    recommended_action = "HR Ops approval required"
ELSE → output = {"buddy_id": best_buddy.id}
```

**C. I-9 Timing Hold**:
```
days_since_hire = (now - hire_date).days

IF days_since_hire > 3 AND no_documents_received:
    status = "I9_HOLD"
    should_escalate = FALSE  (agent can trigger hold autonomously)
    output = {"status": "hold", "reason": "Day 3 threshold passed"}

IF documents_received AND days_since_hire > 3:
    output = {"status": "late_i9", "days_late": days_since_hire - 3}
    should_escalate = FALSE  (log but don't escalate)

IF e_verify_pending > 5 days:
    should_escalate = TRUE
    escalation_type = "E_VERIFY_DELAY"
    recommended_action = "Escalate to Legal"
```

**Confidence Threshold**:
- If agent confidence < 0.7 → always escalate
- Log all decisions (human-approved or not) for feedback loop

### 3.5 System Adapter Agent

**Purpose**: Abstract 6-system integration into unified interface.

**Inputs**:
- `system`: System enum (WORKDAY, SERVICENOW, LMS, EMAIL, SYSTEM_5, SYSTEM_6)
- `operation`: str (e.g., "create_worker", "create_incident")
- `payload`: dict

**Outputs**:
```python
{
    "status": "success" | "error",
    "output": dict,
    "error_message": str | None,
}
```

**Integration Matrix**:

| System | Method | Key Operations |
|--------|--------|----------------|
| Workday | REST API | `create_worker`, `enroll_benefits`, `read_org_structure` |
| ServiceNow | REST API | `create_request`, `poll_fulfillment_status` |
| LMS | SCIM + REST | `assign_course`, `read_completion_status` |
| Email | Graph API | `send_email`, `parse_incoming` |
| System 5 (I-9) | REST API | `submit_document`, `check_status` |
| System 6 (BG) | REST API | `initiate_check`, `get_result` |

**Error Handling**:
- Transient failures (timeout, 503) → retry with exponential backoff (3 attempts)
- Auth failures (401, 403) → alert HR Ops, log for manual intervention
- Schema mismatches → log raw payload, escalate to integration maintainer

### 3.6 Data Models

```python
class OnboardingInstance:
    id: str
    employee_id: str
    hire_date: datetime
    employment_type: str  # full-time, contractor, intern
    jurisdiction: str
    status: OnboardingState  # NEW_HIRE → ... → COMPLETE
    tasks: List[Task]
    judgment_escalations: List[Escalation]
    created_at: datetime
    completed_at: datetime | None

class Task:
    id: str
    type: TaskType
    system_source: System
    assigned_to: Assignee
    status: TaskStatus  # pending, in-progress, blocked, complete, escalated
    due_date: datetime
    completed_at: datetime | None
    output: dict | None
    retry_count: int

class Escalation:
    id: str
    task_id: str
    escalation_type: str
    description: str
    options_considered: List[str]
    recommended_action: str
    created_at: datetime
    resolved_at: datetime | None
    resolution: str | None
    resolved_by: str | None
```

## 3.7 Security & Compliance Architecture

### 3.7.1 PII Data Classification

| Data Element | Classification | Storage Requirements | Access Control |
|--------------|----------------|---------------------|----------------|
| SSN | Sensitive PII | Encrypted at rest (AES-256), never logged | HR Ops + System Admin only |
| I-9 Documents | Sensitive PII | Encrypted at rest, 3-year retention minimum | HR Ops + Audit only |
| Passport/Visa | Sensitive PII | Encrypted at rest, jurisdiction-specific retention | HR Ops + Legal only |
| Name, Email | Standard PII | Encrypted at rest | Agent + HR Ops + IT |
| Job Level | Internal | Standard database security | Agent + HR Ops + Manager |
| Buddy Assignment | Internal | Standard database security | Agent + HR Ops + Assigned Buddy |

### 3.7.2 Data Handling Rules

**Agent Access Restrictions**:
- Agent CANNOT read SSN or I-9 documents directly
- Agent can only write metadata: `{i9_status: "submitted", submission_date: "2026-04-15"}`
- Agent CANNOT send PII via email unless encrypted or through secure portal link
- Agent logs MUST redact PII: log `employee_id=12345` not `ssn=123-45-6789`

**Storage Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│                   Agent Database                        │
│  ┌───────────────────────────────────────────────┐     │
│  │  OnboardingInstance (Standard Encryption)     │     │
│  │  - employee_id, hire_date, status             │     │
│  │  - NO SSN, NO documents                       │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                          │
                          │ API call with employee_id
                          ▼
┌─────────────────────────────────────────────────────────┐
│            Secure PII Vault (Separate System)          │
│  ┌───────────────────────────────────────────────┐     │
│  │  PII Records (AES-256 + Key Rotation)         │     │
│  │  - SSN, I-9 scans, passport data              │     │
│  │  - Access logged to immutable audit trail     │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 3.7.3 Compliance Requirements

**GDPR (for international hires)**:
- Data processing agreement with all 6 system vendors
- Right to erasure: when employee terminates, PII purge within 30 days
- Data portability: employee can request full onboarding data export
- Consent tracking: log when/where employee consented to data processing

**I-9 Compliance**:
- Form I-9 retention: 3 years after hire date OR 1 year after termination (whichever is later)
- Agent CANNOT auto-reject I-9 documents — always escalate to human
- Audit trail: who viewed I-9, when, and why

**SOC2 Type II**:
- All agent decisions logged with timestamp, input context, and output
- Logs immutable (append-only, no deletion)
- Access control: role-based permissions for HR Ops, IT, System Admin
- Secret rotation: API keys rotated every 90 days

### 3.7.4 Secret Management

**Architecture**:
- All API credentials stored in **HashiCorp Vault** or **Azure Key Vault**
- Agent retrieves credentials at runtime (never hardcoded)
- Credentials expire after 12 hours (short-lived tokens)
- Failed auth attempts trigger alert after 3 failures

**Credential Rotation**:
```
1. Every 90 days: Generate new API key in source system
2. Store new key in Vault with version tag
3. Agent fetches both old + new keys for 24-hour grace period
4. After 24 hours: revoke old key
5. Alert if old key still in use (indicates stale deployment)
```

### 3.7.5 Audit Trail Requirements

**Every agent action logs**:
```json
{
    "timestamp": "2026-04-23T14:32:15Z",
    "agent_id": "judgment-agent-v2.1",
    "action": "COMPLIANCE_TRACK_SELECTION",
    "employee_id": "EMP-12345",  // NOT name/SSN
    "input_context": {
        "employment_type": "contractor",
        "jurisdiction": "US"
    },
    "output": {
        "track": "Contractor Compliance",
        "confidence": 0.92
    },
    "escalated": false,
    "human_override": null
}
```

**Retention**: 7 years (legal requirement for employment records)

---

## 3.8 Error Recovery & Rollback Strategy

### 3.8.1 Failure Modes & Compensations

| Failure Scenario | Impact | Compensation Strategy | Manual Fallback |
|------------------|--------|----------------------|-----------------|
| **Workday create succeeds, ServiceNow ticket fails** | Employee exists but no IT provisioning | Retry ServiceNow 3x, then escalate to IT Ops with employee_id | HR Ops manually creates ticket |
| **Benefits enrollment fails after employee created** | Employee has no benefits | Mark task as `FAILED`, alert HR Ops, retry after 1 hour | HR Ops manually enrolls |
| **LMS assign succeeds, but course unavailable** | Training assigned but can't be completed | Agent polls LMS every 6 hours, escalates if >48 hours | HR Ops assigns alternate course |
| **Buddy match created, buddy quits before start date** | New hire has invalid buddy | Agent detects buddy status change, re-runs matching | HR Ops manually reassigns |
| **Email send fails (welcome materials)** | New hire didn't receive welcome info | Retry via secondary email address (personal), escalate if both fail | HR Ops calls new hire |
| **Manager handoff notification sent, manager OOO** | Manager doesn't respond to new hire | Agent detects no calendar response after 48 hours, escalates to manager's manager | HR Ops contacts skip-level |

### 3.8.2 Idempotency Design

**Problem**: If agent retries a failed operation, does it create duplicates?

**Solution**: All system adapters MUST implement idempotency keys.

**Example — ServiceNow Ticket Creation**:
```python
def create_servicenow_ticket(employee_id, request_type):
    idempotency_key = f"onboarding-{employee_id}-{request_type}"
    
    # Check if ticket already exists with this key
    existing = servicenow.query(
        f"short_description CONTAINS '{idempotency_key}'"
    )
    if existing:
        return {"status": "success", "ticket_id": existing.id, "created": False}
    
    # Create new ticket with key in description
    ticket = servicenow.create({
        "short_description": f"[{idempotency_key}] IT Provisioning for {employee_id}",
        "requested_for": employee_id,
        "catalog_item": "new_hire_laptop"
    })
    return {"status": "success", "ticket_id": ticket.id, "created": True}
```

**Key Pattern**: `{workflow}-{unique_id}-{operation}`

### 3.8.3 Distributed Transaction Pattern (Saga)

**Problem**: Onboarding spans 6 systems. If step 4 fails, steps 1-3 are already committed.

**Solution**: Implement saga pattern with compensating transactions.

**Example Workflow — Benefits Enrollment**:
```
Step 1: Create Workday employee record
  Compensation: Mark employee as "inactive" (don't delete — audit trail)

Step 2: Enroll in benefits (System X)
  Compensation: Cancel enrollment, refund deductions

Step 3: Send benefits welcome email
  Compensation: Send "disregard previous email" (can't un-send)

Step 4: Log benefits election in HR system
  Compensation: Delete log entry
```

**Saga Execution**:
```python
class BenefitsEnrollmentSaga:
    def execute(self, employee_id):
        state = SagaState(employee_id)
        
        try:
            # Step 1
            workday_result = self.create_employee(employee_id)
            state.log_step("CREATE_EMPLOYEE", workday_result)
            
            # Step 2
            benefits_result = self.enroll_benefits(employee_id)
            state.log_step("ENROLL_BENEFITS", benefits_result)
            
            # Step 3
            email_result = self.send_email(employee_id)
            state.log_step("SEND_EMAIL", email_result)
            
            state.mark_complete()
            return {"status": "success"}
            
        except Exception as e:
            # Rollback in reverse order
            for step in reversed(state.completed_steps):
                self.compensate(step)
            
            state.mark_failed()
            return {"status": "failed", "error": str(e)}
    
    def compensate(self, step):
        if step.name == "CREATE_EMPLOYEE":
            workday.update_employee(step.employee_id, status="inactive")
        elif step.name == "ENROLL_BENEFITS":
            benefits_system.cancel_enrollment(step.employee_id)
        elif step.name == "SEND_EMAIL":
            # Can't un-send, log correction
            self.send_email(step.employee_id, template="correction")
```

### 3.8.4 Circuit Breaker Pattern

**Problem**: If ServiceNow is down, agent retries every task, wasting resources.

**Solution**: Circuit breaker that stops calling failed systems.

**States**:
```
CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing) → CLOSED
```

**Logic**:
```python
class SystemAdapterCircuitBreaker:
    def __init__(self, system_name, failure_threshold=5, timeout=300):
        self.system_name = system_name
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.state = "CLOSED"
        self.last_failure_time = None
        self.timeout = timeout  # seconds
    
    def call(self, operation, payload):
        if self.state == "OPEN":
            # Check if timeout elapsed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError(f"{self.system_name} circuit open")
        
        try:
            result = self._execute(operation, payload)
            
            # Success: reset counter
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failure_count = 0
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                alert_ops(f"{self.system_name} circuit breaker opened")
            
            raise e
```

**Escalation**: When circuit opens, agent escalates ALL tasks for that system to HR Ops.

### 3.8.5 Manual Fallback Procedures

**When agent fails completely** (e.g., agent service crashes):

1. **Detection**: Health check endpoint fails 3 consecutive times (90 seconds)
2. **Alert**: PagerDuty alert to on-call engineer + email to HR Ops
3. **Fallback**: HR Ops receives email with:
   - List of in-flight onboardings (employee names, hire dates)
   - Current status of each onboarding
   - Link to manual checklist (Google Doc) for each hire
4. **Recovery**: When agent restarts, it resumes from last checkpoint (no duplicate work)

**Manual Checklist Example** (generated by agent before failure):
```
Onboarding for: Jane Smith (EMP-12345)
Hire Date: 2026-04-28
Status as of 2026-04-23 14:32 UTC:

✅ COMPLETE:
  - Workday employee record created
  - ServiceNow IT ticket #INC123456 submitted
  - Benefits enrollment submitted

⏳ IN PROGRESS:
  - Compliance training assignment (waiting for jurisdiction clarification)
  - Buddy matching (escalated due to seniority gap)

❌ NOT STARTED:
  - Welcome email (blocked by compliance training)
  - Manager handoff (blocked by IT provisioning)
  - 30-day checkpoint scheduling (blocked by welcome email)

📌 NEXT ACTIONS:
  1. HR Ops: Resolve compliance training escalation
  2. HR Ops: Approve buddy match (Jane L4 → Bob L6)
  3. Agent will auto-resume once escalations resolved
```

---

## 3.9 State Machine & Workflow Orchestration

### 3.9.1 Complete State Diagram

```
┌─────────────┐
│  NEW_HIRE   │  Trigger: Workday webhook or daily poll
└──────┬──────┘
       │
       │ Generate task list based on employment_type + jurisdiction
       ▼
┌─────────────────┐
│  PROVISIONING   │  Tasks: Workday create, IT ticket, equipment, benefits
└──────┬──────────┘
       │
       │ All provisioning tasks complete
       ▼
┌──────────────────┐
│ COMPLIANCE_SETUP │  Tasks: Assign training, I-9 collection, BG check
└──────┬───────────┘
       │
       │ All compliance tasks complete OR escalated + approved
       ▼
┌──────────────────┐
│ WELCOME_OUTREACH │  Tasks: Welcome email, buddy match, manager handoff
└──────┬───────────┘
       │
       │ All welcome tasks complete
       ▼
┌──────────────────┐
│   MONITORING     │  Tasks: Track Day 30 checkpoint
└──────┬───────────┘
       │
       │ Day 30 checkpoint complete
       ▼
┌──────────────────┐
│    COMPLETE      │  Final state
└──────────────────┘

ALTERNATE PATHS:
┌──────────────────┐
│     BLOCKED      │  Entered when: task dependencies unmet, escalation pending
└──────┬───────────┘
       │
       │ Blocker resolved
       ▼
   (return to previous state)

┌──────────────────┐
│     FAILED       │  Entered when: unrecoverable error (e.g., employee data invalid)
└──────────────────┘  Requires manual intervention to restart
```

### 3.9.2 State Transition Rules

| From State | To State | Condition | Can Skip? |
|------------|----------|-----------|-----------|
| NEW_HIRE | PROVISIONING | Always | No |
| PROVISIONING | COMPLIANCE_SETUP | All provisioning tasks `status=COMPLETE` | No |
| PROVISIONING | BLOCKED | Any task `status=ESCALATED` pending >24 hours | No (temporary) |
| COMPLIANCE_SETUP | WELCOME_OUTREACH | All compliance tasks complete OR approved escalations | No |
| COMPLIANCE_SETUP | BLOCKED | I-9 missing >3 days, BG check delayed | No (temporary) |
| WELCOME_OUTREACH | MONITORING | All welcome tasks complete | No |
| MONITORING | COMPLETE | Day 30 checkpoint scheduled + completed | No |
| Any state | FAILED | Unrecoverable error (invalid employee_id, system auth failure) | N/A |
| BLOCKED | Previous state | Escalation resolved | N/A |

### 3.9.3 Task Skip Logic (Employment Type Variations)

**Full-Time US Employee** (all tasks):
- ✅ Workday create
- ✅ Benefits enrollment
- ✅ I-9 collection
- ✅ Background check
- ✅ Compliance training (Standard US)
- ✅ Buddy matching
- ✅ IT provisioning
- ✅ Welcome materials
- ✅ Manager handoff
- ✅ Day 30 checkpoint

**Contractor**:
- ✅ Workday create
- ❌ Benefits enrollment (skip)
- ❌ I-9 collection (skip — handles own tax paperwork)
- ✅ Background check
- ✅ Compliance training (Contractor track)
- ✅ Buddy matching
- ✅ IT provisioning
- ✅ Welcome materials
- ✅ Manager handoff
- ✅ Day 30 checkpoint

**Intern**:
- ✅ Workday create
- ❌ Benefits enrollment (skip)
- ✅ I-9 collection (if US intern)
- ❌ Background check (skip — typically not required)
- ✅ Compliance training (Intern Safety & Ethics)
- ✅ Buddy matching
- ✅ IT provisioning
- ✅ Welcome materials
- ✅ Manager handoff
- ❌ Day 30 checkpoint (skip — short-term role)

**International (Non-US)**:
- ✅ Workday create
- ✅ Benefits enrollment (jurisdiction-specific)
- ❌ I-9 collection (skip — US-only)
- ✅ Background check (jurisdiction-specific vendor)
- ✅ Compliance training (escalate for jurisdiction mapping)
- ✅ Buddy matching
- ✅ IT provisioning
- ✅ Welcome materials
- ✅ Manager handoff
- ✅ Day 30 checkpoint

### 3.9.4 Task Dependency Graph

```
┌──────────────────┐
│ Workday Create   │  (no dependencies)
└────────┬─────────┘
         │
         ├──────────────────────────────┐
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│ IT Provisioning  │          │ Benefits Enroll  │
└────────┬─────────┘          └────────┬─────────┘
         │                              │
         │                              │
         ▼                              │
┌──────────────────┐                   │
│ Equipment Request│                   │
└────────┬─────────┘                   │
         │                              │
         └──────────────┬───────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Compliance Setup │
               │ (parallel tasks) │
               └────────┬─────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
┌─────────────┐  ┌──────────┐  ┌──────────────┐
│ I-9 Check   │  │ Training │  │ BG Check     │
└─────────────┘  └──────────┘  └──────────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Welcome Outreach │
               │ (parallel tasks) │
               └────────┬─────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
┌─────────────┐  ┌──────────┐  ┌──────────────┐
│ Buddy Match │  │ Welcome  │  │ Manager      │
│             │  │ Email    │  │ Handoff      │
└─────────────┘  └──────────┘  └──────────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Day 30 Checkpoint│
               └──────────────────┘
```

**Parallel vs Sequential**:
- **Parallel** (can run simultaneously):
  - I-9 check + Training assignment + BG check
  - Buddy match + Welcome email + Manager handoff
- **Sequential** (must wait):
  - Benefits enrollment MUST wait for Workday create
  - Welcome email MUST wait for IT provisioning (so email address is active)

### 3.9.5 Handling Dynamic Changes

**Scenario 1: Manager leaves during onboarding**
- Agent detects: Workday API returns `manager_id=null` or `manager_status=terminated`
- Action: Re-route manager handoff to skip-level manager
- Escalation: If no skip-level, escalate to HR Ops

**Scenario 2: Hire date postponed**
- Agent detects: Workday webhook with `hire_date_changed=true`
- Action: Pause all tasks, reschedule SLAs relative to new hire date
- Notification: Email new hire with updated timeline

**Scenario 3: Employment type changes (contractor → full-time)**
- Agent detects: Workday webhook with `employment_type_changed=true`
- Action: Add previously skipped tasks (benefits, I-9), recalculate dependencies
- Escalation: Alert HR Ops to verify compliance implications

---

## 3.10 Observability & Feedback Loops

### 3.10.1 Drift Detection

**Definition**: Are agent decisions diverging from human baseline over time?

**Measurement**:
```python
# Weekly calculation
human_override_rate = (escalations_overridden_by_human / total_escalations)

# Alert if trend increases
if human_override_rate_week_N > human_override_rate_week_1 * 1.5:
    alert("Agent drift detected: human override rate increased 50%")
```

**Root Cause Analysis**:
- Are new edge cases appearing (new jurisdiction, new employment type)?
- Has a system API changed behavior (LMS now returns different course codes)?
- Is agent confidence calibration outdated?

### 3.10.2 Feedback Loop Mechanism

**When human overrides agent decision:**

1. **Log override**:
```json
{
    "timestamp": "2026-04-23T15:00:00Z",
    "task_id": "TASK-789",
    "agent_recommendation": "buddy_id=EMP-111 (score=3.2)",
    "human_decision": "buddy_id=EMP-222",
    "human_reason": "EMP-111 on PTO during new hire start date",
    "overridden_by": "hr-ops-user-456"
}
```

2. **Adjust scoring model**:
   - Add PTO availability as scoring factor (weight: +2)
   - Retrain judgment model with new training signal

3. **Validate improvement**:
   - In next shadow mode run, verify that similar cases now route correctly
   - If accuracy improves, deploy updated model

### 3.10.3 Business Metric Correlation

**Question**: Does agent improve outcomes beyond task completion?

**Metrics to Track**:

| Business Metric | How to Measure | Target |
|-----------------|----------------|--------|
| **New hire retention** | % of hires still employed at 6 months | >85% |
| **Time to productivity** | Days until first code commit (eng) or first deal (sales) | <30 days |
| **New hire satisfaction** | NPS score from Day 30 survey | >50 |
| **Manager satisfaction** | Manager NPS on onboarding process | >40 |

**Correlation Analysis**:
- Do hires onboarded by agent have higher retention than manual onboardings?
- Is time-to-productivity faster when agent completes onboarding on-time?

**If correlation is negative**: Investigate whether agent optimization is sacrificing quality for speed.

---

## Validation Updates

### Additional Test Cases (Add to Section 4.2)

#### Error Recovery Tests

| Test Case | Scenario | Expected Outcome |
|-----------|----------|------------------|
| **Idempotency: duplicate ServiceNow ticket** | Create ticket, retry same operation | Second call returns existing ticket_id, no duplicate |
| **Saga rollback: benefits enrollment fails** | Workday succeeds, benefits fails | Workday employee marked inactive, escalation created |
| **Circuit breaker: LMS down** | LMS returns 503 for 5 consecutive calls | Circuit opens, all training tasks escalated to HR Ops |
| **Manual fallback: agent crashes** | Agent service crashes mid-onboarding | HR Ops receives email with manual checklist, agent resumes on restart |
| **Dynamic change: manager leaves** | Manager terminated after handoff task created | Manager handoff re-routed to skip-level, new hire notified |

#### Security Tests

| Test Case | Scenario | Expected Outcome |
|-----------|----------|------------------|
| **PII redaction: agent logs** | Agent logs compliance decision | Logs contain employee_id, NOT SSN or name |
| **Secret rotation: API key expires** | Workday API key rotated during onboarding | Agent fetches new key from Vault, no disruption |
| **Audit trail: human override** | HR Ops overrides buddy match | Override logged with timestamp, user_id, reason |
| **Access control: unauthorized read** | Non-HR user tries to read I-9 status | API returns 403 Forbidden |

---

## Updated Unknowns (Add to Section 5.2)

| # | Unknown | Why It Matters | How to Validate |
|---|---------|----------------|-----------------|
| **11** | **Does the client have a PII vault?** | Agent can't store SSN/I-9 docs in standard database. If no vault exists, must deploy one. | Ask: "Where do you store SSN and I-9 documents today?" |
| **12** | **What's the RTO for agent failure?** | If agent must recover within 1 hour, need hot standby. If 24 hours OK, cold start acceptable. | Ask: "If the agent stops working, how quickly must it be back online?" |
| **13** | **Are there jurisdiction-specific data residency rules?** | EU data can't leave EU, China data can't leave China. May need regional deployments. | Ask: "Any requirements about where employee data is stored geographically?" |
| **14** | **What's the existing audit retention policy?** | Spec says 7 years, but client may have different requirement. | Ask: "How long do you retain employee onboarding records?" |


---

## 4. Validation Design

### 4.1 Validation Philosophy

**What we're validating**:
1. **Functional correctness**: Agent produces correct outputs for given inputs
2. **Boundary handling**: Agent correctly identifies when to escalate vs. handle autonomously
3. **Integration health**: System adapters work end-to-end
4. **Business outcomes**: Onboarding completes on time, HR Ops time actually reduces

**What failure looks like**:
- Agent routes task to wrong handler
- Agent fails to escalate when it should (false negative)
- Agent escalates when it shouldn't (false positive)
- System adapter returns error, agent doesn't retry or escalate
- Onboarding stalls at a state, SLA violated

### 4.2 Test Categories

#### Unit Tests (Agent Logic)

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| **Task Router: deterministic task** | `task_type=IT_PROVISIONING_REQUEST` | `assignee=AGENT, requires_judgment=False` |
| **Task Router: judgment task** | `task_type=COMPLIANCE_TRAINING_ASSIGN` | `requires_judgment=True` |
| **Judgment: known jurisdiction** | `employment_type=full-time, jurisdiction=US` | `should_escalate=False, track=Standard US Compliance` |
| **Judgment: unknown jurisdiction** | `employment_type=full-time, jurisdiction=Qatar` | `should_escalate=True, escalation_type=UNKNOWN_JURISDICTION` |
| **Judgment: buddy score below threshold** | 5 candidates, all scores < 3 | `should_escalate=True, escalation_type=NO_COMPATIBLE_BUDDY` |
| **Judgment: seniority cross-norm** | hire=L4, best_buddy=L6 | `should_escalate=True, escalation_type=SENIORITY_CROSS_NORM` |
| **Judgment: I-9 Day 3 hold** | hire_date=6 days ago, no documents | `should_escalate=False, status=I9_HOLD` |
| **Orchestrator: state transition** | all IT_PROVISIONING tasks complete | `status=COMPLIANCE_SETUP` |
| **Orchestrator: blocked task detection** | task depends on incomplete dependency | `status=BLOCKED` |

#### Integration Tests (System Adapters)

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| **Workday: create worker** | valid employee payload | `status=success, worker_id returned` |
| **Workday: auth failure** | invalid token | `status=error, error_message contains auth` |
| **ServiceNow: create request** | valid IT request | `status=success, ticket_id returned` |
| **ServiceNow: retry on 503** | 503 response | retries up to 3 times, then escalates |
| **LMS: assign course** | valid course + user | `status=success` |
| **LMS: poll completion** | user_id, course_id | `status=success, completion_status returned` |

#### End-to-End Tests (Full Workflow)

| Test Case | Scenario | Expected Outcome |
|-----------|----------|------------------|
| **Happy path: full-time US hire** | New hire event, FT, US, Engineering, L4 | All tasks complete, status=COMPLETE within 14 days |
| **Edge case: contractor** | New hire, contractor, US | Compliance track = Contractor, no I-9 |
| **Edge case: international** | New hire, FT, Germany | Escalation: unknown jurisdiction |
| **Escalation flow: buddy cross-norm** | New hire L4, best buddy L6 | Escalation created, HR Ops approves, buddy assigned |
| **SLA violation: overdue task** | Task not completed within SLA | Overdue alert generated, escalation created |
| **Retry flow: transient failure** | System adapter returns 503 twice | Retries 3rd time, succeeds |

#### Business Outcome Tests

| Metric | Measurement | Target |
|--------|-------------|--------|
| **Automation rate** | (tasks handled by agent without human) / total tasks | >85% |
| **Escalation accuracy** | (escalations returned as wrong) / total escalations | <10% |
| **On-time completion** | % of tasks completed within SLA | >95% |
| **HR Ops time** | Hours spent on coordination per onboarding | <2 hours (vs. 6.8 hours baseline) |

### 4.3 Validation Execution

**Phase 1 — Mock Testing** (Weeks 1-2):
- Run unit tests against mock Task Router, System Adapter, Judgment Agent
- Validate state machine transitions in isolation

**Phase 2 — Integration Testing** (Weeks 3-4):
- Connect to sandbox environments for Workday, ServiceNow, LMS
- Run integration tests against real APIs (or mocks if sandboxes unavailable)

**Phase 3 — Shadow Mode** (Weeks 5-8):
- Run agent in parallel with manual process
- Log all decisions, compare agent vs. human outcomes
- No actions taken — human process continues

**Phase 4 — Pilot** (Weeks 9-12):
- Agent handles 10-20% of new hires
- HR Ops reviews all agent outputs before execution
- Measure accuracy, adjust thresholds

**Phase 5 — Production Rollout** (Week 13+):
- Full deployment with monitoring
- Continuous measurement against success metrics

### 4.4 Observability

**What to log**:
- Every task routing decision (input → output)
- Every judgment decision (context → recommendation → human override?)
- Every system adapter call (request → response time → success/failure)
- Every escalation (created → resolved → resolution)

**What to alert**:
- SLA breach (task overdue)
- Escalation queue > 5 items
- System adapter error rate > 5%
- Judgment agent confidence < 0.7

**Tools**:
- LangSmith or similar for agent trace debugging
- PostgreSQL for audit logs
- Grafana dashboards for metrics

---

## 5. Assumptions & Unknowns

### 5.1 Assumptions (What we're confident about)

1. **Workday API availability**: Client can provide API credentials and sandbox access for Workday REST API
2. **ServiceNow API availability**: IT team can provision ServiceNow service account with catalog request permissions
3. **LMS API exists**: Compliance LMS has REST or SCIM API for course assignment and completion tracking
4. **New hire data completeness**: Workday provides all required fields (employee_id, email, hire_date, employment_type, jurisdiction, department, job_level)
5. **HR Ops capacity for pilot**: 3-person team can dedicate 2-4 hours/week during pilot phase to review agent outputs

### 5.2 Unknowns (What we need to validate)

| # | Unknown | Why It Matters | How to Validate |
|---|---------|----------------|-----------------|
| **1** | **What are System 5 and System 6?** | Spec mentions 6 systems; we know 4 (Workday, ServiceNow, LMS, email). I-9 and background check are likely candidates, but we don't know vendor names or API capabilities. | Ask client: "What systems handle I-9 document collection and background checks?" |
| **2** | **Does LMS support bulk assignment API?** | Spec assumes LMS can assign courses via API. If LMS only supports manual assignment, compliance track selection can't be automated. | Test LMS API: `POST /courses/{id}/assignments` — does it accept bulk user list? |
| **3** | **What's the actual SLA for IT provisioning?** | Spec assumes 72 hours (from spec). Need to confirm with IT or validate against actual ServiceNow SLA. | Query ServiceNow: what's the average fulfillment time for hardware requests? |
| **4** | **Can HR Ops access escalation UI?** | Spec designs a dashboard, but we don't know their tooling. Do they have a ticket system? SharePoint? Nothing? | Ask: "How do you currently track exceptions or manual tasks?" |
| **5** | **What's the background check vendor?** | BG check may be third-party (Sterling, HireRight). Need API access or may need manual status polling. | Ask: "Who runs background checks? Do they have an API?" |
| **6** | **Is there a buddy program database?** | Spec assumes we can query potential buddies. Do they track buddy history? Is there a directory with job levels? | Ask: "Where do you store buddy assignments? Is there a list of available buddies?" |
| **7** | **What's the I-9 document workflow?** | Spec assumes System 5 handles I-9. Is it a dedicated I-9 system (e.g., I-9 Anywhere) or manual? | Ask: "How do you collect and store I-9 forms today?" |
| **8** | **Do you have email API access?** | Spec assumes Microsoft Graph API for email. Is this available? Or do we need SMTP? | Ask: "Can we send email via API, or do we need SMTP credentials?" |
| **9** | **What's the tolerance for false positive escalations?** | If agent escalates too aggressively, HR Ops ignores it. Need to tune threshold. | During shadow mode: measure false positive rate, adjust threshold |
| **10** | **Are there union or works council requirements?** | In some jurisdictions, onboarding steps require union notification. Agent may not know. | Ask: "Any union or works council requirements for new hire onboarding?" |

### 5.3 Pre-Build Validation Checklist

Before coding begins, validate:

- [ ] Confirm System 5 and System 6 identities and API availability
- [ ] Test Workday, ServiceNow, LMS API credentials in sandbox
- [ ] Confirm HR Ops escalation workflow (what tool?)
- [ ] Obtain buddy program data source
- [ ] Confirm email API access (Graph or SMTP)
- [ ] Document known jurisdictions list for compliance tracks
- [ ] Define SLA windows with IT and compliance teams

---

## Self-Diagnosis Note

**What I got right:**
- Delegation boundary between fully agentic (85%) and agent-led + oversight (15%) is defensible based on judgment complexity and risk
- Escalation triggers are specific enough (unknown jurisdiction, seniority gap >2 levels, confidence <0.7)
- State machine maps to actual onboarding phases

**What I'm less confident about:**
- The "2 unnamed systems" in the original spec were an assumption — I've flagged this as Unknown #1
- I assumed LMS has bulk assignment API — Unknown #2
- I assumed buddy matching data exists — Unknown #6
- The 60% time savings target is a guess; actual baseline may differ

**What would make this spec better:**
- Client interview to validate unknowns 1-8
- Shadow mode data to tune judgment thresholds
- Actual SLA data from ServiceNow rather than assumptions

The spec is precise enough for an AI coding agent to start building the **Orchestrator** and **Task Router** — those have deterministic logic. The **Judgment Agent** requires the unknowns to be resolved first, or at minimum, a shadow mode to calibrate thresholds.