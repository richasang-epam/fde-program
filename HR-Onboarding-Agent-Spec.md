# HR Onboarding Coordination Agent — Solution Specification

## 1. Problem Decomposition

### Current State Analysis

| Dimension | Current Reality |
|-----------|-----------------|
| **Volume** | 220+ hires/year × 40 tasks = ~8,800 task instances |
| **Team Capacity** | 3 HR Ops staff — estimated 1,500+ hours/year on manual coordination |
| **System Landscape** | Workday (HR), ServiceNow (IT), LMS (compliance), email (ad hoc), + 2 unnamed systems |
| **Failure Mode** | Edge cases (15%) cause downstream breaks; automation scripts can't handle variability |

### Root Cause

The 15% judgment-heavy tasks create a **brittleness paradox**: rules-based automation works for the 85% routine, but the 15% edge cases cascade into failures that require manual rescue — defeating the automation ROI.

---

## 2. Agentic Solution Architecture

### Core Design Principle

**Hybrid Agent Model**: A central orchestrator delegates to specialized sub-agents, with a judgment layer that knows when to escalate to humans. The agent doesn't replace HR Ops — it absorbs the 85% routine so humans focus only on the 15% that actually need judgment.

### Agent Roles

| Agent | Responsibility | Handles |
|-------|----------------|---------|
| **Orchestrator** | End-to-end workflow management, dependency resolution, SLA tracking | Timeline, sequencing, blocked task detection |
| **Task Router** | Classify incoming tasks, determine handler, apply routing rules | Task categorization, priority assignment |
| **System Adapter** | Execute CRUD operations across 6 systems, handle API quirks | Workday, ServiceNow, LMS, email, custom APIs |
| **Judgment Agent** | Evaluate edge cases against policy, decide or escalate | Compliance track selection, buddy matching, I-9 holds |

---

## 3. Detailed Specification

### 3.1 Orchestrator Agent

**Purpose**: Manage the lifecycle of each onboarding from hire date to 30-day checkpoint.

**State Machine**:

```
NEW_HIRE → IT_PROVISIONING → COMPLIANCE_SETUP → BUDDY_ASSIGN → 
MATERIALS_SHIP → MANAGER_HANDOFF → DAY_30_SCHEDULED → COMPLETE
```

**Key Behaviors**:
- On new hire event (Workday trigger), create onboarding instance with hire date
- Build dependency graph: IT provisioning must complete before laptop shipping; compliance track must be assigned before training launch
- Daily scan for overdue tasks → escalate to Task Router
- Track SLA windows (e.g., IT provisioning = 72h from hire)

**Data Model**:
```typescript
interface OnboardingInstance {
  id: string;
  employeeId: string;
  hireDate: Date;
  employmentType: 'full-time' | 'contractor' | 'intern';
  jurisdiction: string;
  status: OnboardingState;
  tasks: Task[];
  judgmentEscalations: Escalation[];
  createdAt: Date;
  completedAt?: Date;
}

interface Task {
  id: string;
  type: TaskType;
  systemSource: System;
  assignedTo: 'agent' | 'hr-ops' | 'it' | 'manager';
  status: 'pending' | 'in-progress' | 'blocked' | 'complete' | 'escalated';
  dueDate: Date;
  completedAt?: Date;
  output?: any;
}
```

---

### 3.2 Task Router Agent

**Purpose**: Classify each task from the 6 system sources and determine handling path.

**Routing Logic**:

| Task Source | Task Type | Default Handler | Judgment Required? |
|-------------|-----------|-----------------|-------------------|
| Workday | Create employee record | System Adapter | No |
| Workday | Benefits enrollment trigger | System Adapter | No |
| ServiceNow | IT provisioning request | System Adapter | No |
| ServiceNow | Equipment request | System Adapter | No |
| LMS | Compliance training assignment | System Adapter | **Yes** — employment type → track mapping |
| LMS | Training completion tracking | System Adapter | No |
| Email | Welcome materials request | System Adapter | No |
| Email | Buddy matching request | Judgment Agent | **Yes** — seniority compatibility |
| Custom System 1 | I-9 document collection | Judgment Agent | **Yes** — timing trigger hold |
| Custom System 2 | Background check status | System Adapter | No |

---

### 3.3 Judgment Agent

**Purpose**: Handle the 15% of tasks that require contextual reasoning. This is the core differentiator — it replaces brittle if-then rules with a reasoning model that can handle novel edge cases.

**Decision Categories**:

#### A. Compliance Track Selection (Employment Type → Training Track)
- Contractor → "Contractor Compliance Track" (no benefits, different I-9)
- Full-time, US → "Standard US Compliance" (I-9, W-4, harassment training)
- Full-time, international → "International Onboarding" (local labor law modules)
- Intern → "Intern Safety & Ethics" (abbreviated)
- **Escalation Trigger**: jurisdiction not in known list → HR Ops review

#### B. Buddy Assignment Compatibility
- Score each potential buddy: proximity in seniority (+), same team (+), previous buddy history (- if failed), availability (calendar check)
- If no buddy scores > threshold → escalate to HR Ops
- Flag if buddy is > 2 levels senior (crosses norm) → HR Ops approval

#### C. I-9 Timing Hold Trigger
- Calculate days since hire
- If > 3 days and no documents → trigger "I-9 Hold" status
- If documents received after Day 3 → log as "Late I-9" with timestamp
- If E-Verify case pending > 5 days → escalate

**Escalation Protocol**:
- Judgment Agent never guesses — when confidence < threshold, it escalates with:
  - Summary of the decision context
  - Options considered
  - Recommended action
  - Relevant data snapshots

---

### 3.4 System Adapter Agent

**Purpose**: Abstract the 6-system integration into a unified interface.

| System | Integration Method | Key Operations |
|--------|-------------------|----------------|
| Workday | REST API (Worker, Benefits, Organization) | Create worker, enroll benefits, read org structure |
| ServiceNow | REST API (Incident, Request, Catalog) | Create IT request, poll fulfillment status |
| LMS | SCIM + REST API (Courses, Assignments, Completions) | Assign course, read completion status |
| Email | SMTP/IMAP or Microsoft Graph API | Send welcome email, parse incoming requests |
| System 5 (TBD) | REST API | Custom per system |
| System 6 (TBD) | REST API | Custom per system |

**Error Handling**:
- Transient failures → retry with exponential backoff (3 attempts)
- Auth failures → alert HR Ops, log for manual intervention
- Schema mismatches → log raw payload, escalate to integration maintainer

---

## 4. Human-in-the-Loop Interface

### Escalation UI (for HR Ops)

The 3-person team needs a lightweight dashboard to handle escalations:

```
┌────────────────────────────────────────────────────────────┐
│  PENDING ESCALATIONS (3)                                  │
├────────────────────────────────────────────────────────────┤
│  [1] Buddy Assignment — Seniority Cross                  │
│  New hire: L4 Data Analyst, Dept: Analytics               │
│  Suggested buddy: L6 Senior Manager (2-level gap)         │
│  [Approve] [Reject + Suggest Alternative]                 │
├────────────────────────────────────────────────────────────┤
│  [2] I-9 Late Trigger — Employee #4492                    │
│  Hire date: Apr 15, No documents received (Day 6)         │
│  [Send Reminder] [Escalate to Legal]                      │
├────────────────────────────────────────────────────────────┤
│  [3] Compliance Track Unknown — Contractor #8821         │
│  Jurisdiction: Qatar (not in known list)                  │
│  [Select Track] [Defer to Manager]                        │
└────────────────────────────────────────────────────────────┘
```

### Approval Workflow

- HR Ops actions on escalations are recorded and fed back to Judgment Agent as training signals
- Over time, the agent learns org-specific preferences (e.g., "we always pair L4s with L5s, not L6s")

---

## 5. Implementation Phases

| Phase | Timeline | Focus |
|-------|----------|-------|
| 1 | Weeks 1-4 | Deploy Orchestrator with simple linear workflow; Connect Workday and ServiceNow adapters; Implement basic task routing (85% auto, 15% → manual queue) |
| 2 | Weeks 5-8 | Implement Judgment Agent with rule-based reasoning; Add escalation UI for HR Ops; Connect LMS adapter |
| 3 | Weeks 9-12 | Capture HR Ops decisions as feedback; Refine judgment thresholds based on escalation patterns; Add email and remaining system adapters |
| 4 | Weeks 13-16 | SLA monitoring and alerting; Audit logging for compliance; Performance tuning |

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Task automation rate | >85% of tasks handled without human touch |
| Escalation accuracy | <10% of escalations returned as "wrong routing" |
| On-time completion | >95% of onboarding tasks completed within SLA |
| HR Ops time savings | >60% reduction in manual coordination hours |
| Mean time to resolve escalation | <4 hours during business hours |

---

## 7. Technical Stack Recommendation

| Component | Technology |
|-----------|------------|
| Agent Framework | LangChain or AutoGen (for multi-agent orchestration) |
| LLM | GPT-4 or Claude (for judgment agent reasoning) |
| Workflow State | Temporal or Prefect (for durable state management) |
| API Gateway | AWS API Gateway or Kong |
| Database | PostgreSQL (onboarding instance state, audit logs) |
| Observability | LangSmith or similar for agent trace debugging |

---

## 8. Risk Mitigations

| Risk | Mitigation |
|------|------------|
| LLM produces wrong compliance advice | Always require human approval for compliance track decisions; log all outputs |
| System API changes break adapters | Versioned adapter contracts; integration test suite |
| Data privacy (PII in onboarding) | PII masking in logs; role-based access to escalation UI |
| Single point of failure | Orchestrator stateless + database-backed; graceful degradation to manual |