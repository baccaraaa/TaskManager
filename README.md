# FastAPI Task Management System

A comprehensive task management API built with FastAPI, showcasing enterprise-level features and best practices for senior Python developer positions.

## 🚀 Features

### Core Functionality
- **User Authentication & Authorization** (JWT tokens, role-based access)
- **Task Management** (CRUD operations with advanced filtering)
- **Project Organization** (Group tasks into projects)
- **Real-time Updates** (WebSocket notifications)
- **File Uploads** (Task attachments with cloud storage)
- **Email Notifications** (Async email sending)

### Technical Excellence
- **Database Integration** (PostgreSQL with SQLAlchemy ORM)
- **Async/Await** (Fully asynchronous architecture)
- **Caching** (Redis for performance optimization)
- **Background Tasks** (Celery for heavy operations)
- **API Documentation** (Auto-generated OpenAPI/Swagger)
- **Testing** (Comprehensive test suite with pytest)
- **Monitoring** (Logging, metrics, health checks)
- **Security** (Rate limiting, input validation, CORS)

### DevOps & Production Ready
- **Docker** (Multi-stage builds, docker-compose)
- **CI/CD** (GitHub Actions workflow)
- **Environment Configuration** (Pydantic settings)
- **Database Migrations** (Alembic)
- **Error Handling** (Structured exception handling)
- **Code Quality** (Black, isort, flake8, mypy)

## 🛠 Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Message Queue**: Celery with Redis broker
- **Authentication**: JWT with passlib
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic v2
- **Testing**: pytest, httpx
- **Documentation**: Auto-generated OpenAPI

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (or use Docker)
- Redis (or use Docker)

## 🚀 Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd fastapi-task-management
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker (Recommended)**
   ```bash
   docker-compose up -d
   ```

4. **Or Run Locally**
   ```bash
   # Start database and redis
   docker-compose up -d postgres redis
   
   # Run migrations
   alembic upgrade head
   
   # Start the application
   uvicorn app.main:app --reload
   ```

5. **Access the Application**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user

### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `GET /users/{user_id}` - Get user by ID (admin only)

### Projects
- `GET /projects/` - List user projects
- `POST /projects/` - Create new project
- `GET /projects/{project_id}` - Get project details
- `PUT /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Delete project

### Tasks
- `GET /tasks/` - List tasks with filtering/pagination
- `POST /tasks/` - Create new task
- `GET /tasks/{task_id}` - Get task details
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Delete task
- `POST /tasks/{task_id}/attachments` - Upload task attachment

### WebSocket
- `WS /ws/{user_id}` - Real-time notifications

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_tasks.py

# Run tests in parallel
pytest -n auto
```

## 🏗 Architecture

```
app/
├── api/                 # API routes
├── core/               # Core functionality (auth, config, security)
├── crud/               # Database operations
├── db/                 # Database models and connection
├── schemas/            # Pydantic models
├── services/           # Business logic
├── utils/              # Utility functions
├── workers/            # Background tasks
└── main.py            # Application entry point
```

## 🔒 Security Features

- JWT token authentication
- Password hashing with bcrypt
- Rate limiting
- CORS configuration
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## 📈 Performance Optimizations

- Database query optimization
- Redis caching
- Async database operations
- Connection pooling
- Background task processing
- Response compression

## 🚀 Deployment

The application is production-ready with:
- Docker multi-stage builds
- Health check endpoints
- Graceful shutdown handling
- Environment-based configuration
- Logging and monitoring
- Database migration management

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

---

This project demonstrates advanced FastAPI development skills suitable for senior Python developer positions, including modern async patterns, comprehensive testing, security best practices, and production deployment considerations.
