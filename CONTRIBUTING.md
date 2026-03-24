# Contributing to Task Manager

Thanks for your interest in contributing. This guide will get you up and running.

## Prerequisites

- Python 3.10+
- Docker (for PostgreSQL and Redis)

## Getting Started

```bash
git clone https://github.com/baccaraaa/taskmanager.git
cd taskmanager
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker-compose up -d postgres redis
alembic upgrade head
```

## Project Structure

```
app/
  api/api_v1/endpoints/  -- Route handlers
  core/                  -- Config, security, middleware
  crud/                  -- Database operations
  db/                    -- Models and connection
  schemas/               -- Pydantic models
  services/              -- Business logic
  workers/               -- Celery tasks
  utils/                 -- Utilities
```

## Development Workflow

1. Create a branch from `main`: `git checkout -b feat/my-feature`
2. Make your changes
3. Run tests: `pytest`
4. Run linters: `black . && isort . && flake8`
5. Submit a pull request

## Code Style

Black handles formatting (88 char line width). isort sorts imports with the black profile. Run both before submitting.

Do not add comments unless the logic is non-obvious. Let the code speak for itself.

## Testing

We use pytest with pytest-asyncio. Write tests for any new functionality.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_tasks.py -v
```

## Architecture Rules

- **Routes** call **services**, services call **CRUD** -- never skip layers
- All database operations go through `app/crud/`
- Authorization checks live in `app/services/`
- Keep routes thin -- just parse input, call service, return response
