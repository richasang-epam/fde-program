# Missing Sections — Additions to HR Onboarding Agent Spec

> **Insert Location**: These sections should be added after Section 3 (Agent Specification) and before Section 4 (Validation Design)

---

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

