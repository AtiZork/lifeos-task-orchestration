"""Tests for task endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    """Test task creation."""
    task_data = {
        "title": "Clean up inbox",
        "description": "Archive emails older than 30 days",
        "priority": "high",
    }
    
    response = await client.post("/api/v1/tasks", json=task_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["priority"] == task_data["priority"]
    assert data["status"] == "classified"
    assert "task_id" in data
    assert "classification" in data
    assert data["classification"]["category"] == "email_automation"


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient):
    """Test task retrieval."""
    # First create a task
    task_data = {
        "title": "Test task",
        "description": "Test description",
        "priority": "medium",
    }
    
    create_response = await client.post("/api/v1/tasks", json=task_data)
    task_id = create_response.json()["task_id"]
    
    # Then retrieve it
    response = await client.get(f"/api/v1/tasks/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["task_id"] == task_id
    assert data["title"] == task_data["title"]


@pytest.mark.asyncio
async def test_get_nonexistent_task(client: AsyncClient):
    """Test retrieving a nonexistent task."""
    response = await client.get("/api/v1/tasks/nonexistent_task")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient):
    """Test listing tasks."""
    # Create a few tasks
    for i in range(3):
        task_data = {
            "title": f"Task {i}",
            "description": f"Description {i}",
            "priority": "medium",
        }
        await client.post("/api/v1/tasks", json=task_data)
    
    # List tasks
    response = await client.get("/api/v1/tasks")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "tasks" in data
    assert len(data["tasks"]) >= 3
    assert data["total"] >= 3
