# Architecture Deep Dive

## System Architecture

The LifeOS Task Orchestration Service follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│               (Mobile, Web, External Services)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / REST API
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                          │
│  ┌──────────────┬──────────────────┬──────────────────┐         │
│  │   /health    │    /api/v1/tasks │ /api/v1/workflows│         │
│  │              │                  │                  │         │
│  │  - Health    │  - Create Task   │ - Execute        │         │
│  │  - Ready     │  - Get Task      │ - Get Status     │         │
│  │              │  - List Tasks    │ - List Available │         │
│  └──────────────┴──────────────────┴──────────────────┘         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Dependency Injection
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Service Layer (Business Logic)                │
│  ┌──────────────────────┬─────────────────────────────┐         │
│  │   TaskService        │   WorkflowService           │         │
│  │                      │                             │         │
│  │  - Orchestrate task  │  - Orchestrate workflow     │         │
│  │    creation          │    execution                │         │
│  │  - Coordinate agents │  - Coordinate agents        │         │
│  │  - Manage state      │  - Manage execution state   │         │
│  └──────────────────────┴─────────────────────────────┘         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Agent Invocation
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│             Agent Layer (Core Logic)                            │
│  ┌─────────────┬──────────────────┬─────────────────┐           │
│  │Classifier   │  PlannerAgent    │ ExecutorAgent   │           │
│  │Agent        │                  │                 │           │
│  │             │                  │                 │           │
│  │- Classify   │- Generate        │- Execute steps  │           │
│  │  intent     │  workflow plan   │- Track progress │           │
│  │- Suggest    │- Define steps    │- Handle errors  │           │
│  │  workflow   │- Estimate time   │- Report results │           │
│  └─────────────┴──────────────────┴─────────────────┘           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Repository Pattern
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           Persistence Layer (Data Access)                       │
│  ┌──────────────────────┬─────────────────────────────┐         │
│  │ TaskRepository       │ WorkflowRepository          │         │
│  │                      │                             │         │
│  │ - CRUD operations    │ - CRUD operations           │         │
│  │ - In-memory storage  │ - Execution state           │         │
│  │ - Easy to swap       │ - Easy to swap              │         │
│  │   to Firestore/SQL   │   to Firestore/SQL          │         │
│  └──────────────────────┴─────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Design Patterns

### 1. Layered Architecture

**Purpose**: Separation of concerns and maintainability

- **API Layer**: HTTP request handling, validation, serialization
- **Service Layer**: Business logic, orchestration, coordination
- **Agent Layer**: Task classification, planning, and execution
- **Repository Layer**: Data persistence abstraction

**Benefits**:
- Easy to test each layer independently
- Clear dependencies (each layer depends only on the layer below)
- Easy to replace implementations (e.g., swap in-memory storage for Firestore)

### 2. Repository Pattern

**Purpose**: Abstract data persistence

```python
class BaseRepository(ABC):
    @abstractmethod
    async def create(self, entity_id: str, data: Dict) -> Dict
    async def get(self, entity_id: str) -> Optional[Dict]
    async def update(self, entity_id: str, data: Dict) -> Dict
    # ...
```

**Benefits**:
- Services don't know about storage implementation
- Easy to swap storage backends
- Easier to mock for testing

### 3. Dependency Injection

**Purpose**: Loose coupling and testability

```python
def get_task_service() -> TaskService:
    return TaskService(
        task_repository=get_task_repository(),
        classifier_agent=get_classifier_agent(),
    )

@router.post("/tasks")
async def create_task(
    request: TaskCreateRequest,
    service: TaskService = Depends(get_task_service),
):
    return await service.create_task(request)
```

**Benefits**:
- Easy to inject mocks for testing
- Clear dependencies
- Singleton pattern for shared resources

### 4. Agent Pattern

**Purpose**: Modular components for specific tasks

```python
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, input_data: Dict) -> Dict
```

**Benefits**:
- Easy to add new agents
- Each agent has single responsibility
- Agents can be chained or composed
- Future: Agents can be extracted into separate microservices

### 5. Async/Await Pattern

**Purpose**: Non-blocking I/O for better performance

```python
async def execute_workflow(request: WorkflowExecuteRequest):
    # All I/O operations are async
    planning_result = await planner_agent.execute(...)
    execution_result = await executor_agent.execute(...)
    return result
```

**Benefits**:
- Can handle many concurrent requests
- Better resource utilization
- FastAPI is built on async (ASGI)

## Data Flow

### Task Creation Flow

```
1. Client Request
   POST /api/v1/tasks
   {
     "title": "Clean up inbox",
     "description": "Archive old emails",
     "priority": "high"
   }
   
   ↓

2. API Layer (tasks.py)
   - Validate request with Pydantic
   - Inject TaskService
   
   ↓

3. Service Layer (TaskService)
   - Generate unique task ID
   - Invoke ClassifierAgent
   
   ↓

4. Agent Layer (ClassifierAgent)
   - Analyze text: "clean up inbox" + "archive old emails"
   - Match keywords: email, inbox, archive
   - Return classification:
     {
       "category": "email_automation",
       "confidence": 0.95,
       "suggested_workflow": "inbox_cleanup_workflow"
     }
   
   ↓

5. Service Layer (TaskService)
   - Build task entity
   - Store via TaskRepository
   
   ↓

6. Repository Layer (TaskRepository)
   - Persist to storage (in-memory, Firestore, SQL)
   
   ↓

7. API Layer
   - Return TaskResponse
   - HTTP 201 Created
```

### Workflow Execution Flow

```
1. Client Request
   POST /api/v1/workflows/execute
   {
     "workflow_name": "inbox_cleanup_workflow",
     "parameters": {"days_threshold": 30},
     "async_execution": false
   }
   
   ↓

2. Service Layer (WorkflowService)
   - Generate execution ID
   - Invoke PlannerAgent
   
   ↓

3. Agent Layer (PlannerAgent)
   - Load workflow template
   - Generate concrete plan:
     [
       {step: "connect_email", order: 0},
       {step: "fetch_emails", order: 1},
       {step: "filter_emails", order: 2},
       {step: "archive_emails", order: 3},
       {step: "send_summary", order: 4}
     ]
   
   ↓

4. Service Layer (WorkflowService)
   - Create execution record
   - Invoke ExecutorAgent
   
   ↓

5. Agent Layer (ExecutorAgent)
   - Execute steps sequentially
   - Update progress after each step
   - Handle failures
   - Return results
   
   ↓

6. Service Layer (WorkflowService)
   - Update execution record
   - Mark as completed/failed
   
   ↓

7. API Layer
   - Return WorkflowExecutionResponse
   - HTTP 202 Accepted (async) or 200 OK (sync)
```

## Agent Intelligence

### ClassifierAgent

**Responsibility**: Understand user intent

**Current Implementation**: Rule-based keyword matching
- Fast and deterministic
- No external dependencies
- Easy to understand and debug

**Production Enhancement**:
```python
# Replace with ML model or LLM API
async def _classify_text(self, text: str):
    # Option 1: Vertex AI
    prediction = await vertex_ai_client.predict(text)
    
    # Option 2: OpenAI API
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": "Classify user intent..."
        }]
    )
    
    return category, confidence, suggested_workflow
```

### PlannerAgent

**Responsibility**: Create execution plans

**Current Implementation**: Template-based planning
- Fast and predictable
- Easy to version control
- Supports dependencies

**Production Enhancement**:
```python
# Dynamic planning with AI
async def _generate_plan(self, workflow_name, parameters):
    # Use AI to optimize execution path
    # Consider resource availability
    # Parallelize independent steps
    # Estimate costs and time
    
    return optimized_plan
```

### ExecutorAgent

**Responsibility**: Execute workflow steps

**Current Implementation**: Sequential execution with simulation
- Demonstrates the pattern
- Easy to test
- Handles errors gracefully

**Production Enhancement**:
```python
async def _execute_single_step(self, step):
    # Real implementations
    if step["name"] == "connect_email":
        await gmail_api.authenticate()
    elif step["name"] == "archive_emails":
        await gmail_api.batch_archive(email_ids)
    
    # Or use cloud services
    await cloud_run_jobs.execute(step_config)
```

## Scalability Considerations

### Horizontal Scaling

Cloud Run automatically scales based on:
- Request volume
- CPU usage
- Memory usage
- Custom metrics

**Service is stateless**:
- No in-memory state shared between requests
- All state stored externally (Firestore, Cloud SQL)
- Can handle millions of requests across many instances

### Vertical Scaling

Can adjust per-instance resources:
- CPU: 1-8 vCPUs
- Memory: 128Mi - 32Gi
- More resources = faster cold starts

### Database Scaling

**In-Memory** (current): Good for demo, not production

**Cloud Firestore**: 
- Automatic scaling
- Global replication
- Pay per operation
- Best for: < 10K operations/second

**Cloud SQL**:
- Vertical scaling (read replicas)
- Good for relational data
- Best for: Complex queries, ACID transactions

**Cloud Spanner**:
- Horizontal scaling
- Global consistency
- Best for: Very high throughput, global distribution

### Async Processing

**Current**: FastAPI BackgroundTasks
- Good for < 5 minute tasks
- Limited by Cloud Run timeout (15 min max)

**Production**: Cloud Tasks or Pub/Sub
```python
# Publish to Pub/Sub instead of executing immediately
await pubsub_client.publish(
    topic="workflow-execution-tasks",
    data=execution_plan
)

# Separate worker service consumes messages
# No timeout limits
# Retry policies
# Dead letter queues
```

## Security Architecture

### Current State (Demo)

- Open CORS
- No authentication
- Public API

### Production Recommendations

1. **Authentication**:
   ```python
   from google.cloud import identity_platform
   
   async def verify_token(token: str):
       # Verify Firebase ID token
       decoded_token = auth.verify_id_token(token)
       return decoded_token["uid"]
   ```

2. **Authorization**:
   ```python
   @router.post("/tasks")
   async def create_task(
       request: TaskCreateRequest,
       user: User = Depends(get_current_user),
   ):
       # Check permissions
       if not user.has_permission("tasks:create"):
           raise HTTPException(403)
   ```

3. **Rate Limiting**:
   ```python
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @router.post("/tasks")
   @limiter.limit("10/minute")
   async def create_task(...):
       ...
   ```

4. **Secret Management**:
   ```python
   from google.cloud import secretmanager
   
   # Don't use .env in production
   client = secretmanager.SecretManagerServiceClient()
   api_key = client.access_secret_version(
       name=f"projects/{project_id}/secrets/api-key/versions/latest"
   )
   ```

## Observability

### Structured Logging

```python
logger.info(
    "Task created",
    extra={
        "task_id": task_id,
        "category": classification["category"],
        "confidence": classification["confidence"],
    }
)
```

**Benefits**:
- Machine-readable logs
- Easy to query in Cloud Logging
- Correlation IDs for request tracing

### Metrics

**Current**: Basic logging

**Production**: OpenTelemetry
```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
task_counter = meter.create_counter("tasks_created")

task_counter.add(1, {"category": category})
```

### Tracing

**Production**: Cloud Trace
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("create_task"):
    # Automatic trace propagation
    classification = await classifier_agent.execute(...)
```

## Error Handling

### RFC 7807 Problem Details

All errors follow a standard format:

```json
{
  "type": "https://lifeos.akaion.dev/errors/task-not-found",
  "title": "Task Not Found",
  "status": 404,
  "detail": "Task not found: task_abc123",
  "instance": "/api/v1/tasks/task_abc123"
}
```

**Benefits**:
- Machine-readable error types
- Human-readable titles and details
- Extensible for additional context
- Industry standard (RFC 7807)

### Exception Hierarchy

```python
LifeOSException (base)
├── TaskNotFoundException
├── WorkflowNotFoundException
├── ValidationException
├── AgentExecutionException
├── WorkflowExecutionException
└── TimeoutException
```

Each exception has:
- Custom error code
- Contextual information
- Proper HTTP status mapping

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
async def test_classifier_agent():
    agent = ClassifierAgent()
    result = await agent.execute({
        "title": "Clean inbox",
        "description": "Archive old emails"
    })
    assert result["category"] == "email_automation"
```

### Integration Tests

Test API endpoints end-to-end:

```python
async def test_create_task_integration(client):
    response = await client.post("/api/v1/tasks", json={...})
    assert response.status_code == 201
```

### Load Tests

Use `locust` or `k6` for load testing:

```python
from locust import HttpUser, task

class WorkflowUser(HttpUser):
    @task
    def execute_workflow(self):
        self.client.post("/api/v1/workflows/execute", json={...})
```

## Future Enhancements

### Multi-Tenancy

```python
class Task(BaseModel):
    task_id: str
    tenant_id: str  # Add tenant isolation
    # ...

# Filter by tenant
async def list_tasks(user: User):
    return await task_repo.list(filters={"tenant_id": user.tenant_id})
```

### Event Sourcing

```python
class TaskCreatedEvent:
    task_id: str
    timestamp: datetime
    data: dict

# Store events instead of state
await event_store.append("task_stream", TaskCreatedEvent(...))

# Rebuild state from events
task = Task.from_events(events)
```

### CQRS (Command Query Responsibility Segregation)

```python
# Separate write model (commands)
class CreateTaskCommand:
    async def execute(self):
        # Write to primary datastore
        ...

# Separate read model (queries)
class TaskQueryService:
    async def get_task(self, task_id):
        # Read from optimized read store
        ...
```

### GraphQL API

```python
import strawberry

@strawberry.type
class Task:
    task_id: str
    title: str
    status: str

@strawberry.type
class Query:
    @strawberry.field
    async def task(self, task_id: str) -> Task:
        return await task_service.get_task(task_id)
```

## Conclusion

This architecture demonstrates:

- **Clean architecture** with clear separation of concerns
- **Agent-oriented design** for task processing
- **Cloud-native thinking** designed for GCP Cloud Run
- **Production-ready patterns** that scale
- **Extensibility** for adding features
- **Testability** across all layers
- **Observability** with structured logging

The system is ready to be a foundational service in Akaion's LifeOS platform.
