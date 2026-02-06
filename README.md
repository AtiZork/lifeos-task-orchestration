# LifeOS Task Orchestration Service

> **Cloud-native FastAPI backend for task and workflow execution**  
> Part of the LifeOS ecosystem - an operating system for unified tool orchestration

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00C7B7?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/run)

---

## Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [System Design](#-system-design)
- [API Documentation](#-api-documentation)
- [Local Development](#-local-development)
- [GCP Deployment](#-gcp-deployment)
- [Project Structure](#-project-structure)
- [Design Decisions](#-design-decisions)

---

## Overview

The **LifeOS Task Orchestration Service** is a production-ready backend service that demonstrates:

- **Agent-oriented architecture**: Intelligent routing through classifier, planner, and executor agents
- **Cloud-native design**: Stateless, horizontally scalable, built for GCP Cloud Run
- **Async-first processing**: Non-blocking I/O with background task execution
- **Production-grade**: Structured logging, error handling, validation, observability

### Primary Use Case

A **Task and Workflow Execution API** that accepts user intent, intelligently processes it through modular agents, and executes multi-step workflows. This service represents a foundational building block of Akaion's LifeOS platform.

### Example Workflow

```
User Request → API Gateway → Classifier Agent → Planner Agent → Executor Agent → Result
     ↓              ↓              ↓                  ↓               ↓            ↓
"Create task"   Validate     Classify          Generate        Execute      Return
"for email"     & Parse      intent           workflow         steps        status
```

---

## Architecture

### High-Level System Design

```
┌──────────────────────────────────────────────────────────────────┐
│                       Client Applications                        │
│              (Mobile Apps, Web UI, External Services)            │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    GCP Cloud Load Balancer                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Cloud Run Service                           │
│                    (Auto-scaling instances)                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application Container                 │  │
│  │                                                            │  │
│  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │  │           API Layer (Routers)                       │   │  │
│  │  │  • /api/v1/tasks      - Task management             │   │  │
│  │  │  • /api/v1/workflows  - Workflow execution          │   │  │
│  │  │  • /health            - Health checks               │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  │                          │                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │  │        Service Layer (Business Logic)               │   │  │
│  │  │  • TaskService      - Task CRUD & state mgmt        │   │  │
│  │  │  • WorkflowService  - Workflow orchestration        │   │  │
│  │  │  • AgentService     - Agent coordination            │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  │                          │                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │  │      Agent Layer (Intelligence Engine)              │   │  │
│  │  │  • ClassifierAgent  - Intent classification         │   │  │
│  │  │  • PlannerAgent     - Workflow planning             │   │  │
│  │  │  • ExecutorAgent    - Action execution              │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  │                          │                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │  │       Persistence Layer (Data Access)               │   │  │
│  │  │  • WorkflowRepository  - Workflow storage           │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
        ┌───────────────────┐   ┌──────────────┐
        │   Cloud Firestore │   │ Cloud Logging│
        │   (Optional)      │   │ & Monitoring │
        └───────────────────┘   └──────────────┘
```

### Execution Flow

```
1. Request Ingestion
   ├─ Client sends HTTP request
   ├─ API router validates with Pydantic models
   └─ Structured logging begins (correlation ID assigned)

2. Service Layer Processing
   ├─ TaskService/WorkflowService receives request
   ├─ Business logic validation
   └─ Delegates to AgentService

3. Agent Orchestration
   ├─ ClassifierAgent analyzes user intent
   │  └─ Returns: category, confidence, suggested workflow
   ├─ PlannerAgent generates execution plan
   │  └─ Returns: step-by-step workflow with dependencies
   └─ ExecutorAgent runs workflow steps
      ├─ Executes in background (async)
      ├─ Updates task status
      └─ Returns execution results

4. Response & Persistence
   ├─ Results stored in repository
   ├─ HTTP response returned to client
   └─ Logs aggregated in Cloud Logging
```

---

## System Design

### Core Principles

1. **Separation of Concerns**
   - Each layer has a single, well-defined responsibility
   - Routers handle HTTP, Services handle business logic, Agents handle intelligence

2. **Async-First**
   - All I/O operations use `async/await`
   - Background tasks via FastAPI's `BackgroundTasks`
   - Non-blocking request handling

3. **Stateless Design**
   - No in-memory state between requests
   - Horizontal scaling ready
   - Container-friendly

4. **Agent-Oriented Architecture**
   - Modular agents with clear interfaces
   - Easy to add new agents (e.g., OptimizerAgent, NotificationAgent)
   - Pluggable workflow system

5. **Cloud-Native**
   - Environment-based configuration (12-factor app)
   - Health checks for orchestration platforms
   - Structured JSON logging for aggregation

### Technology Stack

| Layer         | Technology              | Purpose                           |
|---------------|-------------------------|-----------------------------------|
| API Framework | FastAPI 0.109+          | Modern async Python web framework |
| Runtime       | Python 3.11+            | Latest stable Python runtime      |
| Validation    | Pydantic v2             | Request/response validation       |
| Logging       | Python logging + JSON   | Structured observability          |
| HTTP Client   | httpx (async)           | Non-blocking external API calls   |
| Container     | Docker (multi-stage)    | Optimized production images       |
| Platform      | GCP Cloud Run           | Serverless container platform     |
| Optional DB   | Cloud Firestore         | NoSQL document database           |
| Optional Jobs | Cloud Tasks/Pub/Sub     | Async job processing              |

---

## API Documentation

### Base URL (Production)
```
https://lifeos-task-service-<hash>.run.app
```

### Base URL (Local)
```
http://localhost:8080
```

### Interactive Documentation

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`
- **OpenAPI JSON**: `http://localhost:8080/openapi.json`

### Endpoints

#### Health Check
```http
GET /health
```

**Response (200)**
```json
{
  "status": "healthy",
  "service": "lifeos-task-orchestration",
  "version": "1.0.0",
  "timestamp": "2026-02-06T12:00:00Z"
}
```

#### Create Task
```http
POST /api/v1/tasks
Content-Type: application/json
```

**Request Body**
```json
{
  "title": "Clean up inbox",
  "description": "Archive emails older than 30 days",
  "priority": "high",
  "metadata": {
    "category": "email_automation",
    "user_id": "user_123"
  }
}
```

**Response (201)**
```json
{
  "task_id": "task_abc123",
  "status": "pending",
  "classification": {
    "category": "email_automation",
    "confidence": 0.95,
    "suggested_workflow": "inbox_cleanup_workflow"
  },
  "created_at": "2026-02-06T12:00:00Z",
  "estimated_completion": "2026-02-06T12:05:00Z"
}
```

#### Get Task Status
```http
GET /api/v1/tasks/{task_id}
```

**Response (200)**
```json
{
  "task_id": "task_abc123",
  "title": "Clean up inbox",
  "status": "in_progress",
  "progress": 45,
  "current_step": "archiving_emails",
  "created_at": "2026-02-06T12:00:00Z",
  "updated_at": "2026-02-06T12:02:30Z"
}
```

#### Execute Workflow
```http
POST /api/v1/workflows/execute
Content-Type: application/json
```

**Request Body**
```json
{
  "workflow_name": "inbox_cleanup_workflow",
  "parameters": {
    "days_threshold": 30,
    "archive_folder": "Old Emails"
  },
  "async_execution": true
}
```

**Response (202)**
```json
{
  "execution_id": "exec_xyz789",
  "workflow_name": "inbox_cleanup_workflow",
  "status": "queued",
  "steps_planned": 5,
  "estimated_duration_seconds": 120
}
```

#### List Workflows
```http
GET /api/v1/workflows
```

**Response (200)**
```json
{
  "workflows": [
    {
      "name": "inbox_cleanup_workflow",
      "description": "Automate email archival based on age",
      "steps": 5,
      "avg_duration_seconds": 120
    },
    {
      "name": "task_prioritization_workflow",
      "description": "Intelligently prioritize tasks based on context",
      "steps": 3,
      "avg_duration_seconds": 30
    }
  ]
}
```

### Error Responses

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://lifeos.akaion.dev/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid priority value",
  "instance": "/api/v1/tasks",
  "errors": [
    {
      "field": "priority",
      "message": "Must be one of: low, medium, high, urgent"
    }
  ]
}
```

---

## Local Development

### Prerequisites

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Docker** ([Install](https://docs.docker.com/get-docker/))
- **Git** ([Install](https://git-scm.com/downloads))

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/akaion/lifeos-task-orchestration.git
   cd lifeos-task-orchestration
   ```

2. **Set up Python virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

6. **Access the application**
   - API: http://localhost:8080
   - Swagger UI: http://localhost:8080/docs
   - Health Check: http://localhost:8080/health

### Development with Docker

```bash
# Build the Docker image
docker build -t lifeos-task-service:dev .

# Run the container
docker run -p 8080:8080 --env-file .env lifeos-task-service:dev

# Access at http://localhost:8080
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

---

## GCP Deployment

### Prerequisites

- **GCP Account** with billing enabled
- **gcloud CLI** ([Install](https://cloud.google.com/sdk/docs/install))
- **Docker** installed locally
- **Project ID** created in GCP Console

### Step 1: Configure GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export SERVICE_NAME="lifeos-task-orchestration"

# Authenticate with GCP
gcloud auth login

# Set the active project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

### Step 2: Build and Push Docker Image

```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker

# Build the image for Cloud Run
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest
```

### Step 3: Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars="ENVIRONMENT=production" \
  --set-env-vars="LOG_LEVEL=INFO"

# Get the service URL
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)'
```

### Step 4: Verify Deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test task creation
curl -X POST $SERVICE_URL/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "description": "Verify deployment",
    "priority": "medium"
  }'
```

### Optional: Set up Cloud Firestore

```bash
# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Create Firestore database (Native mode)
gcloud firestore databases create \
  --location=$REGION \
  --type=firestore-native

# Update Cloud Run deployment with Firestore
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars="USE_FIRESTORE=true" \
  --set-env-vars="FIRESTORE_PROJECT=$PROJECT_ID"
```

### Optional: Set up Cloud Pub/Sub for Async Processing

```bash
# Create a topic for background tasks
gcloud pubsub topics create workflow-execution-tasks

# Create a subscription
gcloud pubsub subscriptions create workflow-execution-sub \
  --topic workflow-execution-tasks

# Update Cloud Run with Pub/Sub configuration
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars="USE_PUBSUB=true" \
  --set-env-vars="PUBSUB_TOPIC=workflow-execution-tasks"
```

### CI/CD with Cloud Build

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME:$COMMIT_SHA', '.']

  # Push the image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/$SERVICE_NAME:$COMMIT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - '$SERVICE_NAME'
      - '--image=gcr.io/$PROJECT_ID/$SERVICE_NAME:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'

images:
  - 'gcr.io/$PROJECT_ID/$SERVICE_NAME:$COMMIT_SHA'
```

Trigger build:
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Monitoring and Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --limit 50 \
  --format json

# Set up log-based metrics
gcloud logging metrics create task_creation_count \
  --description="Count of task creation requests" \
  --log-filter='resource.type="cloud_run_revision" AND textPayload=~"Task created"'
```

---

## Project Structure

```
lifeos-task-orchestration/
│
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration management
│   │
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   ├── v1/                   # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── tasks.py          # Task endpoints
│   │   │   ├── workflows.py      # Workflow endpoints
│   │   │   └── health.py         # Health check endpoints
│   │   └── dependencies.py       # Shared API dependencies
│   │
│   ├── services/                 # Service layer (business logic)
│   │   ├── __init__.py
│   │   ├── task_service.py       # Task management logic
│   │   ├── workflow_service.py   # Workflow orchestration
│   │   └── agent_service.py      # Agent coordination
│   │
│   ├── agents/                   # Agent layer (intelligence)
│   │   ├── __init__.py
│   │   ├── base.py               # Base agent interface
│   │   ├── classifier.py         # Intent classification agent
│   │   ├── planner.py            # Workflow planning agent
│   │   └── executor.py           # Execution agent
│   │
│   ├── models/                   # Pydantic models
│   │   ├── __init__.py
│   │   ├── task.py               # Task models
│   │   ├── workflow.py           # Workflow models
│   │   └── agent.py              # Agent models
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py               # Base repository interface
│   │   ├── task_repository.py    # Task persistence
│   │   └── workflow_repository.py # Workflow persistence
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── logger.py             # Structured logging
│       ├── exceptions.py         # Custom exceptions
│       └── helpers.py            # Helper functions
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── test_api/                 # API tests
│   ├── test_services/            # Service tests
│   ├── test_agents/              # Agent tests
│   └── test_integration/         # Integration tests
│
├── .env.example                  # Example environment variables
├── .gitignore                    # Git ignore patterns
├── .dockerignore                 # Docker ignore patterns
├── Dockerfile                    # Production Docker image
├── cloudbuild.yaml               # GCP Cloud Build configuration
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
├── pyproject.toml                # Python project metadata
└── README.md                     # This file
```

---

## Design Decisions

### 1. Why FastAPI?

- **Async-native**: Built on Starlette for async request handling
- **Type safety**: Leverages Python type hints for validation
- **Auto-documentation**: OpenAPI/Swagger generated automatically
- **Performance**: Comparable to Node.js and Go
- **Developer experience**: Minimal boilerplate, intuitive API design

### 2. Why Agent-Based Architecture?

- **Modularity**: Easy to add/remove agents without touching core logic
- **Testability**: Each agent can be unit tested independently
- **Scalability**: Agents can be extracted into separate microservices later
- **Intelligence**: Clear separation between "thinking" (classification/planning) and "doing" (execution)
- **Future-proof**: Aligns with LifeOS vision of AI agent orchestration

### 3. Why Cloud Run?

- **Serverless**: No infrastructure management
- **Auto-scaling**: Scales to zero when idle, scales up on demand
- **Cost-effective**: Pay only for actual usage
- **Stateless-friendly**: Designed for containerized stateless apps
- **Built-in load balancing**: Automatic request distribution
- **Fast deployment**: New versions live in <1 minute

### 4. Stateless vs Stateful

**Decision**: Stateless design with optional external persistence

**Rationale**:
- Enables horizontal scaling without session affinity
- Container restarts don't lose data (stored externally)
- Simplifies deployment and fault tolerance
- Trade-off: Requires external storage for task state (Firestore/Cloud SQL)

### 5. Async Background Tasks vs Cloud Tasks/Pub/Sub

**Decision**: Start with FastAPI BackgroundTasks, provide Pub/Sub integration path

**Rationale**:
- BackgroundTasks sufficient for short-lived workflows (<5 min)
- No additional GCP service costs for initial deployment
- Easy migration path: Agent executor can publish to Pub/Sub
- Trade-off: Long-running tasks (>5 min) should use Cloud Tasks

### 6. Repository Pattern

**Decision**: Abstract persistence behind repository interfaces

**Rationale**:
- Swap in-memory storage for Firestore/SQL without changing business logic
- Easier to mock for testing
- Cleaner service layer code
- Trade-off: Additional abstraction layer

### 7. Structured Logging

**Decision**: JSON-formatted logs with correlation IDs

**Rationale**:
- Cloud Logging parses JSON automatically
- Correlation IDs enable request tracing across services
- Structured data enables powerful log queries
- Trade-off: Less human-readable locally (but can format for dev)

### 8. Error Handling

**Decision**: RFC 7807 Problem Details format

**Rationale**:
- Standard format for HTTP API errors
- Machine-readable and human-readable
- Extensible for additional error context
- Better than generic `{"error": "message"}` responses

---

## Security Considerations

- **Environment variables**: Secrets stored in GCP Secret Manager (not in .env)
- **Authentication**: Ready to integrate with Firebase Auth, Cloud Identity
- **Rate limiting**: Can add middleware for per-IP rate limits
- **Input validation**: All inputs validated via Pydantic models
- **CORS**: Configurable allowed origins
- **Health checks**: No sensitive data exposed

---

## Future Enhancements

- [ ] Firebase Authentication integration
- [ ] Cloud Tasks for long-running workflows
- [ ] Cloud Scheduler for recurring tasks
- [ ] Firestore for persistent task storage
- [ ] OpenTelemetry tracing
- [ ] Prometheus metrics endpoint
- [ ] GraphQL API layer
- [ ] WebSocket support for real-time updates
- [ ] Multi-region deployment
- [ ] A/B testing for agent strategies

---

## License

This is a technical assessment project for Akaion.

---

## Author

Built as part of Akaion's Software Engineer assessment by [Your Name]

---

## Support

For questions about this implementation:
- **Architecture decisions**: See [Design Decisions](#-design-decisions)
- **Deployment issues**: See [GCP Deployment](#-gcp-deployment)
- **API usage**: See [API Documentation](#-api-documentation)

---

**Note**: This is a production-ready backend service demonstrating cloud-native thinking, agent-oriented design, and strong backend fundamentals as a core building block of Akaion's LifeOS platform.
