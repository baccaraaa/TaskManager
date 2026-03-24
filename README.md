<p align="center">
  <h1 align="center">Task Manager API</h1>
</p>

<p align="center">
  Task management REST API built with <strong>FastAPI</strong>, featuring JWT authentication, real-time WebSocket notifications, background task processing, and a clean layered architecture.
</p>

<p align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/baccaraaa/taskmanager/ci.yml?branch=main)](https://github.com/baccaraaa/taskmanager/actions)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

</p>

## Features

- **JWT authentication** -- access/refresh tokens, role-based access control, password reset flow
- **Project & task management** -- full CRUD with ownership-based authorization
- **Advanced task filtering** -- by status, priority, assignee, project, due date, and full-text search
- **Real-time notifications** -- WebSocket with per-user connection tracking
- **Background tasks** -- Celery workers for email notifications and scheduled reminders
- **File attachments** -- upload and download files attached to tasks
- **Security middleware** -- rate limiting, security headers, request validation, audit logging
- **Async architecture** -- fully async with SQLAlchemy 2.0 and asyncpg
- **Comprehensive tests** -- 130+ tests with 80%+ coverage

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.104 |
| Database | PostgreSQL 15 + SQLAlchemy 2.0 (async) |
| Cache / Broker | Redis 7 |
| Background Tasks | Celery 5.3 |
| Authentication | JWT (python-jose) + bcrypt |
| Validation | Pydantic v2 |
| Migrations | Alembic |
| Testing | pytest + pytest-asyncio + httpx |
| Containerization | Docker (multi-stage) + docker-compose |
| CI/CD | GitHub Actions |

## Quick Start

Clone and configure:

```bash
git clone https://github.com/baccaraaa/taskmanager.git
cd taskmanager
cp .env.example .env
```

Run with Docker (recommended):

```bash
docker-compose up -d
```

Or run locally:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start the app
uvicorn app.main:app --reload
```

Open the API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Project Structure

```
app/
  api/
    api_v1/endpoints/   -- route handlers (auth, users, projects, tasks, websocket)
    deps.py             -- dependency injection (auth, DB sessions)
  core/                 -- config, security, middleware, exceptions
  crud/                 -- database operations (user, project, task)
  db/                   -- SQLAlchemy models and connection
  schemas/              -- Pydantic request/response models
  services/             -- business logic and authorization
  workers/              -- Celery tasks (email, reminders)
  utils/                -- email rendering
tests/                  -- 130+ async tests
```

## API Overview

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user", "password": "securepass123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "securepass123"}'
# Returns: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### Projects

```bash
# Create a project
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "description": "Project description"}'
```

### Tasks

```bash
# Create a task
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Fix login bug", "priority": "high", "project_id": 1}'

# Filter tasks
curl "http://localhost:8000/api/v1/tasks/?status=todo&priority=high&search=bug" \
  -H "Authorization: Bearer <token>"
```

### WebSocket

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/ws/1?token=<access_token>");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data); // { event: "task_status_changed", task_id: 1, ... }
};
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns JWT tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/password-reset` | Request password reset |
| POST | `/auth/password-reset/confirm` | Confirm password reset |
| GET | `/users/me` | Current user profile |
| PUT | `/users/me` | Update profile |
| GET | `/users/` | List users (admin) |
| GET | `/users/{id}` | Get user (admin) |
| GET | `/projects/` | List own projects |
| POST | `/projects/` | Create project |
| GET | `/projects/{id}` | Get project |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |
| GET | `/tasks/` | List tasks (with filters) |
| POST | `/tasks/` | Create task |
| GET | `/tasks/{id}` | Get task |
| PUT | `/tasks/{id}` | Update task |
| DELETE | `/tasks/{id}` | Delete task |
| POST | `/tasks/{id}/attachments` | Upload attachment |
| GET | `/tasks/{id}/attachments/{att_id}` | Download attachment |
| WS | `/ws/{user_id}` | Real-time notifications |

All endpoints prefixed with `/api/v1`.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific module
pytest tests/test_tasks.py -v
```

## License

[MIT](LICENSE)
