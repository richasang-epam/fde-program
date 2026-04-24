# HR Onboarding Agent

An AI-powered system that automates 85% of HR onboarding tasks while maintaining human oversight for judgment-critical decisions.

## Overview

This system coordinates onboarding workflows across multiple enterprise systems including Workday, ServiceNow, LMS, and others. It uses AI agents to handle routine tasks while escalating complex decisions to human reviewers.

## Features

- **Automated Task Coordination**: Handles 12 different task types across 6 systems
- **AI-Powered Judgment**: Makes intelligent decisions on compliance tracks, buddy matching, and I-9 timing
- **Human-in-the-Loop**: Escalates edge cases to HR Ops with full context and recommendations
- **State Machine**: Tracks onboarding progress through 8 distinct phases
- **Secure PII Handling**: Encrypts sensitive data with role-based access control
- **RESTful API**: Webhook integration with external systems
- **Monitoring & Logging**: Comprehensive observability with structured logging

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for queuing)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hr-onboarding-agent
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start with Docker Compose (recommended):
```bash
cd docker
docker-compose up -d
```

Or run locally:
```bash
# Start PostgreSQL and Redis separately
python src/main.py
```

## API Documentation

### Webhook Endpoints

- `POST /webhooks/workday/new-hire` - Receive new hire events
- `POST /webhooks/servicenow/task-update` - Receive task completion updates
- `POST /webhooks/lms/completion-update` - Receive training completion updates

### REST API Endpoints

- `GET /api/v1/onboarding/{employee_id}` - Get onboarding status
- `POST /api/v1/escalations/{escalation_id}/resolve` - Resolve escalations
- `GET /api/v1/escalations/pending` - Get pending escalations
- `GET /api/v1/health` - Health check

## Configuration

See `.env.example` for all configuration options. Key settings:

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for AI agents
- `ENCRYPTION_KEY`: 32-byte key for PII encryption
- External API keys for Workday, ServiceNow, etc.

## Development

### Running Tests

```bash
pytest tests/
```

### Core Validation

A lightweight validation script is available to check the base onboarding logic without requiring external integration dependencies.

```bash
python validate_core.py
```

### Full Test Runner

A comprehensive test runner has been added to execute syntax validation, import checks, unit tests, integration tests, end-to-end tests, and coverage analysis.

```bash
python run_tests.py
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
```

## Current Status

- Core onboarding models, workflow state machine, and security layers are implemented.
- A basic FastAPI API surface is defined for webhook handling and onboarding status lookup.
- The test suite includes unit tests for models, core validation, and planned integration workflows.
- The `validate_core.py` script currently passes for core logic and data model validation.

## Architecture

### Core Components

1. **Orchestrator Agent**: Manages end-to-end workflow lifecycle
2. **Task Router Agent**: Classifies tasks and determines handlers
3. **Judgment Agent**: Evaluates edge cases and makes recommendations
4. **System Adapter Agent**: Abstracts integrations with external systems

### Data Flow

1. New hire event received via webhook
2. Orchestrator creates onboarding instance and generates tasks
3. Task Router assigns tasks to appropriate handlers
4. Agents execute tasks or escalate for human review
5. State machine advances as tasks complete
6. Process completes when all tasks finished

## Security

- PII data is encrypted at rest using AES-256
- Role-based access control for all endpoints
- Audit logging for all PII access
- JWT authentication for API access

## Monitoring

- Structured JSON logging
- Prometheus metrics endpoint
- Health checks for all dependencies
- SLA violation alerts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[License information]
