# HR Onboarding Agent Build Specification

## Overview

This build specification outlines the technical implementation requirements for the HR Onboarding Coordination Agent system as described in the solution deliverables. The system automates 85% of onboarding tasks while maintaining human oversight for judgment-critical decisions.

## 1. Technology Stack

### Core Framework
- **Language**: Python 3.11+
- **Framework**: LangChain for agent orchestration
- **Async Runtime**: asyncio for concurrent task processing
- **Web Framework**: FastAPI for REST APIs and webhooks

### Infrastructure
- **Database**: PostgreSQL 15+ with asyncpg driver
- **Message Queue**: Redis for task queuing and state management
- **Cache**: Redis for session state and API response caching
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for local development

### External Integrations
- **Workday**: REST API client
- **ServiceNow**: REST API client
- **LMS**: SCIM + REST API client
- **Email**: Microsoft Graph API
- **I-9 System**: REST API client
- **Background Check**: REST API client

### Security & Monitoring
- **Authentication**: OAuth 2.0 / JWT tokens
- **Encryption**: AES-256 for PII data
- **Logging**: Structured JSON logging with loguru
- **Monitoring**: Prometheus metrics + Grafana dashboards
- **Tracing**: OpenTelemetry for distributed tracing

## 2. Project Structure

```
hr-onboarding-agent/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── task_router.py
│   │   ├── judgment_agent.py
│   │   └── system_adapter.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── onboarding.py
│   │   ├── task.py
│   │   └── escalation.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── webhooks.py
│   │   ├── endpoints.py
│   │   └── middleware.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── workday.py
│   │   ├── servicenow.py
│   │   ├── lms.py
│   │   ├── email.py
│   │   ├── i9_system.py
│   │   └── bg_check.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── state_machine.py
│   └── utils/
│       ├── __init__.py
│       ├── sla.py
│       ├── retry.py
│       └── validation.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── api/
│   └── deployment/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── README.md
└── .env.example
```

## 3. Dependencies

### Core Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
redis[hiredis]==5.0.1
langchain==0.1.0
langchain-openai==0.0.5
openai==1.3.7
httpx==0.25.2
loguru==0.7.2
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Development Dependencies
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
mypy==1.7.1
pre-commit==3.5.0
```

## 4. Database Schema

### Tables

#### onboarding_instances
```sql
CREATE TABLE onboarding_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    hire_date DATE NOT NULL,
    employment_type VARCHAR(20) NOT NULL,
    jurisdiction VARCHAR(50) NOT NULL,
    department VARCHAR(100),
    job_level VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'INITIATED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

#### tasks
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    onboarding_instance_id UUID NOT NULL REFERENCES onboarding_instances(id),
    task_type VARCHAR(50) NOT NULL,
    system_source VARCHAR(50) NOT NULL,
    assigned_to VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    output JSONB,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### escalations
```sql
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id),
    escalation_type VARCHAR(50) NOT NULL,
    description TEXT,
    options_considered JSONB,
    recommended_action TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution TEXT,
    resolved_by VARCHAR(100)
);
```

#### task_dependencies
```sql
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(50) NOT NULL,
    depends_on VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 5. API Specifications

### Webhook Endpoints

#### POST /webhooks/workday/new-hire
**Purpose**: Receives new hire events from Workday
**Request Body**:
```json
{
  "employee_id": "string",
  "email": "string",
  "name": "string",
  "hire_date": "2024-01-15",
  "employment_type": "full-time|contractor|intern",
  "jurisdiction": "US|CA|UK",
  "department": "string",
  "job_level": "1-5"
}
```
**Response**: 202 Accepted

#### POST /webhooks/servicenow/task-update
**Purpose**: Receives task completion updates from ServiceNow
**Request Body**:
```json
{
  "task_id": "uuid",
  "status": "completed|failed",
  "output": {}
}
```

### REST API Endpoints

#### GET /api/v1/onboarding/{employee_id}
**Purpose**: Get onboarding status
**Response**:
```json
{
  "id": "uuid",
  "employee_id": "string",
  "status": "INITIATED|IT_PROVISIONING|COMPLIANCE_SETUP|ACTIVE|COMPLETE|ON_HOLD",
  "tasks": [
    {
      "id": "uuid",
      "type": "CREATE_EMPLOYEE_RECORD",
      "status": "completed",
      "due_date": "2024-01-16T00:00:00Z"
    }
  ],
  "escalations": []
}
```

#### POST /api/v1/escalations/{escalation_id}/resolve
**Purpose**: Resolve human-reviewed escalations
**Request Body**:
```json
{
  "resolution": "approved|rejected|manual_override",
  "output": {},
  "resolved_by": "hr_ops_user"
}
```

## 6. Agent Implementation Details

### Orchestrator Agent

**Class Structure**:
```python
class OrchestratorAgent:
    def __init__(self, db: Database, task_router: TaskRouter, system_adapter: SystemAdapter):
        self.db = db
        self.task_router = task_router
        self.system_adapter = system_adapter
        self.state_machine = OnboardingStateMachine()

    async def handle_new_hire(self, employee_data: dict) -> OnboardingInstance:
        # Create instance
        instance = await self.db.create_onboarding_instance(employee_data)
        
        # Generate task list
        tasks = self.generate_task_list(employee_data)
        
        # Route initial tasks
        for task in tasks:
            await self.route_task(task, instance)
        
        return instance

    async def handle_task_completion(self, task_id: str, output: dict):
        # Update task status
        task = await self.db.update_task_status(task_id, 'completed', output)
        
        # Check state transition
        instance = await self.db.get_onboarding_instance(task.onboarding_instance_id)
        new_state = self.state_machine.transition(instance.status, task)
        
        if new_state != instance.status:
            await self.db.update_instance_status(instance.id, new_state)
            await self.process_state_change(instance.id, new_state)
```

### Task Router Agent

**Routing Logic**:
```python
class TaskRouter:
    ROUTING_RULES = {
        'CREATE_EMPLOYEE_RECORD': {'assignee': 'agent', 'requires_judgment': False},
        'COMPLIANCE_TRAINING_ASSIGN': {'assignee': 'agent', 'requires_judgment': True},
        'BUDDY_MATCHING': {'assignee': 'agent', 'requires_judgment': True},
        # ... other rules
    }

    async def route_task(self, task: Task, context: dict) -> RoutingDecision:
        rule = self.ROUTING_RULES.get(task.type, {'assignee': 'hr-ops', 'requires_judgment': True})
        
        if rule['requires_judgment']:
            judgment = await self.judgment_agent.evaluate(task.type, context)
            if judgment.should_escalate:
                return RoutingDecision(assignee='hr-ops', escalation=judgment)
        
        return RoutingDecision(assignee=rule['assignee'])
```

### Judgment Agent

**Decision Engine**:
```python
class JudgmentAgent:
    async def evaluate(self, task_type: str, context: dict) -> JudgmentResult:
        if task_type == 'COMPLIANCE_TRAINING_ASSIGN':
            return await self.evaluate_compliance_track(context)
        elif task_type == 'BUDDY_MATCHING':
            return await self.evaluate_buddy_match(context)
        elif task_type == 'I9_DOCUMENT_COLLECTION':
            return await self.evaluate_i9_timing(context)
        
        return JudgmentResult(should_escalate=True, escalation_type='UNKNOWN_TASK_TYPE')

    async def evaluate_compliance_track(self, context: dict) -> JudgmentResult:
        employment_type = context.get('employment_type')
        jurisdiction = context.get('jurisdiction')
        
        if employment_type == 'contractor':
            return JudgmentResult(
                should_escalate=False,
                output={'track': 'Contractor Compliance'}
            )
        
        if jurisdiction not in self.KNOWN_JURISDICTIONS:
            return JudgmentResult(
                should_escalate=True,
                escalation_type='UNKNOWN_JURISDICTION',
                options_considered=['Standard US', 'International'],
                recommended_action='HR Ops to select track manually'
            )
        
        return JudgmentResult(
            should_escalate=False,
            output={'track': f'Standard {jurisdiction} Compliance'}
        )
```

## 7. State Machine Implementation

```python
from enum import Enum

class OnboardingState(Enum):
    NEW_HIRE = "NEW_HIRE"
    IT_PROVISIONING = "IT_PROVISIONING"
    COMPLIANCE_SETUP = "COMPLIANCE_SETUP"
    BUDDY_ASSIGN = "BUDDY_ASSIGN"
    MATERIALS_SHIP = "MATERIALS_SHIP"
    MANAGER_HANDOFF = "MANAGER_HANDOFF"
    DAY_30_SCHEDULED = "DAY_30_SCHEDULED"
    COMPLETE = "COMPLETE"

class OnboardingStateMachine:
    TRANSITIONS = {
        OnboardingState.NEW_HIRE: [OnboardingState.IT_PROVISIONING],
        OnboardingState.IT_PROVISIONING: [OnboardingState.COMPLIANCE_SETUP],
        OnboardingState.COMPLIANCE_SETUP: [OnboardingState.BUDDY_ASSIGN],
        OnboardingState.BUDDY_ASSIGN: [OnboardingState.MATERIALS_SHIP],
        OnboardingState.MATERIALS_SHIP: [OnboardingState.MANAGER_HANDOFF],
        OnboardingState.MANAGER_HANDOFF: [OnboardingState.DAY_30_SCHEDULED],
        OnboardingState.DAY_30_SCHEDULED: [OnboardingState.COMPLETE],
        OnboardingState.COMPLETE: []
    }

    def transition(self, current_state: OnboardingState, completed_task: Task) -> OnboardingState:
        # Logic to determine next state based on completed task and current state
        if current_state == OnboardingState.NEW_HIRE:
            if completed_task.type == TaskType.CREATE_EMPLOYEE_RECORD:
                return OnboardingState.IT_PROVISIONING
        
        # ... implement other transition logic based on task completion
        
        return current_state
```

## 8. Security Implementation

### PII Handling
```python
class SecureDataHandler:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key)

    async def store_pii(self, employee_id: str, pii_data: dict) -> str:
        """Store encrypted PII data, return reference ID"""
        encrypted = self.cipher.encrypt(json.dumps(pii_data).encode())
        reference_id = await self.db.store_encrypted_pii(employee_id, encrypted)
        return reference_id

    async def retrieve_pii(self, reference_id: str) -> dict:
        """Retrieve and decrypt PII data"""
        encrypted = await self.db.get_encrypted_pii(reference_id)
        decrypted = self.cipher.decrypt(encrypted).decode()
        return json.loads(decrypted)
```

### Access Control
```python
class AccessControl:
    PII_ACCESS_ROLES = {
        'hr_ops': ['ssn', 'i9_documents', 'passport'],
        'system_admin': ['all'],
        'agent': []  # No direct PII access
    }

    def can_access_pii(self, user_role: str, pii_type: str) -> bool:
        allowed = self.PII_ACCESS_ROLES.get(user_role, [])
        return 'all' in allowed or pii_type in allowed
```

## 9. Testing Strategy

### Unit Tests
- Agent decision logic
- State machine transitions
- Data validation
- Security controls

### Integration Tests
- API endpoint functionality
- Database operations
- External system integrations
- Message queue processing

### End-to-End Tests
- Complete onboarding workflow
- Escalation handling
- Error recovery scenarios
- Performance under load

### Test Coverage Requirements
- Minimum 85% code coverage
- All critical paths tested
- Security controls validated
- Performance benchmarks met

## 10. Deployment Architecture

### Container Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

EXPOSE 8000

CMD ["uvicorn", "api.endpoints:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/onboarding

# External APIs
WORKDAY_API_KEY=...
SERVICENOW_API_KEY=...
OPENAI_API_KEY=...

# Security
ENCRYPTION_KEY=...
JWT_SECRET_KEY=...

# Monitoring
PROMETHEUS_PORT=9090
```

### Health Checks
- Database connectivity
- External API availability
- Queue processing status
- Memory/CPU usage

## 11. Monitoring & Observability

### Metrics
- Onboarding completion rate
- Task automation percentage
- Escalation response time
- System uptime
- Error rates by component

### Alerts
- SLA violations
- Failed external API calls
- High escalation queue
- Database connection issues
- Security incidents

### Logging
- Structured JSON logs
- PII redaction
- Trace correlation IDs
- Audit trails for all PII access

## 12. Implementation Phases

### Phase 1: Core Infrastructure (2 weeks)
- Project setup and basic structure
- Database schema and models
- Basic API endpoints
- Docker configuration

### Phase 2: Agent Framework (3 weeks)
- Orchestrator agent implementation
- Task router logic
- Basic system adapter stubs
- State machine implementation

### Phase 3: Judgment Engine (2 weeks)
- Judgment agent implementation
- Escalation handling
- Human-in-the-loop workflows

### Phase 4: Integrations (4 weeks)
- Workday integration
- ServiceNow integration
- LMS integration
- Email integration
- I-9 and background check systems

### Phase 5: Security & Compliance (2 weeks)
- PII encryption and access controls
- Audit logging
- Security testing
- Compliance validation

### Phase 6: Testing & Deployment (3 weeks)
- Comprehensive testing suite
- Performance optimization
- Production deployment
- Monitoring setup

## 13. Success Criteria

### Functional Requirements
- [ ] All 12 task types automated according to delegation matrix
- [ ] State machine transitions working correctly
- [ ] Escalation workflow functional
- [ ] External system integrations operational

### Performance Requirements
- [ ] Process 220 hires/year with <4 hour escalation resolution
- [ ] 99.9% uptime for core services
- [ ] <5 second response time for API calls
- [ ] <1% error rate for automated tasks

### Security Requirements
- [ ] Zero PII data breaches
- [ ] All access logged and auditable
- [ ] Encryption standards met
- [ ] Compliance with relevant regulations

### Quality Requirements
- [ ] 85%+ test coverage
- [ ] All critical bugs resolved
- [ ] Documentation complete
- [ ] Code review standards met