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