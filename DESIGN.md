# Task Management System – Design Document

## Table of Contents
1. [High-Level Design (HLD)](#high-level-design-hld)
2. [Low-Level Design (LLD)](#low-level-design-lld)

---

## High-Level Design (HLD)

### 1. Overview

The Task Management System is a RESTful API backend built with Flask and PostgreSQL.  
It provides a multi-role project and sprint management platform with real-time notifications,
Redis caching, JWT-based authentication, and analytics.

### 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Client Applications                           │
│         Angular SPA (localhost:4200)  │  CLI / Curl / Postman       │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼───────────────────────────────────────────┐
│                    Flask API Server (Gunicorn/Werkzeug)              │
│                                                                      │
│  ┌────────────┐  ┌───────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ Auth Layer │  │ Blueprints│  │ Services │  │ Socket.IO Layer │  │
│  │ (JWT)      │  │ (Routes)  │  │          │  │  (real-time)    │  │
│  └────────────┘  └───────────┘  └──────────┘  └─────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                     SQLAlchemy ORM                             │  │
│  └────────────────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────────────────┬─────────────────┘
             │                                      │
   ┌─────────▼──────────┐              ┌────────────▼────────────┐
   │  PostgreSQL (RDS)  │              │  Redis (cache + broker) │
   └────────────────────┘              └─────────────────────────┘
```

### 3. Key Components

| Component | Responsibility |
|-----------|---------------|
| **Routes (Blueprints)** | Parse HTTP requests, validate inputs, call services, return JSON responses |
| **Services** | Business logic, permission enforcement, orchestration |
| **Models (ORM)** | Database schema, relationships, model-level utilities |
| **Utils** | Cross-cutting concerns: logging, caching, JWT helpers, validators |
| **Config** | Environment-aware configuration (`BaseConfig` → `DevelopmentConfig`) |
| **Socket.IO** | Real-time notifications and project room broadcasts |

### 4. API Surface

| Prefix | Module | Description |
|--------|--------|-------------|
| `/api/auth` | `auth_routes` | Registration, login, profile, token refresh |
| `/api/tasks` | `task_routes` | Task CRUD, comments, time logging |
| `/api/projects` | `project_routes` | Project CRUD, team membership |
| `/api/sprints` | `sprint_routes` | Sprint lifecycle, burndown, task assignment |
| `/api/comments` | `comment_routes` | Standalone comment management |
| `/api/notifications` | `notification_routes` | Notification CRUD and read-marking |
| `/api/analytics` | `analytics_routes` | Dashboard, task, project, user metrics |
| `/api/enums` | `enum_routes` | Enum values + rich metadata for clients |
| `/api/cache` | `cache_routes` | Admin-only cache management |
| `/health` | inline | Liveness and DB readiness probes |

### 5. Request Lifecycle

```
HTTP Request
    │
    ▼
Flask Router (URL dispatch)
    │
    ▼
JWT Middleware (@jwt_required)
    │
    ▼
Route Handler (Blueprint)
  ├── Request parsing & basic validation
  ├── Log API request
  └── Delegate to Service
          │
          ▼
      Service Layer
        ├── Business rule validation
        ├── Permission checks
        ├── Cache check (Redis)
        └── ORM operations (SQLAlchemy)
                │
                ▼
           PostgreSQL
                │
          (result returned)
                │
    ┌───────────┘
    ▼
Standardised JSON Response
{ success, message, data, timestamp }
```

### 6. Security Model

- **Authentication**: JWT access tokens (configurable TTL) + refresh tokens
- **Authorisation**: Role-based (11 roles in `UserRole` enum) + project-level permission flags on `ProjectMember`
- **Passwords**: bcrypt hashing via Werkzeug
- **CORS**: Restricted to `http://localhost:4200` (configurable)
- **Admin endpoints**: `@admin_required` decorator gates cache management

### 7. Caching Strategy

- **Backend**: Redis (`flask-caching`)
- **Per-user keys**: `{prefix}:user_{id}` — isolated per authenticated user
- **TTLs**: 60 s (dev) / 300-600 s (prod)
- **Invalidation**: Explicit on writes (`invalidate_user_cache`, `invalidate_project_cache`)
- **Failure mode**: Cache misses fall through to the database gracefully

### 8. Real-Time Notifications

- **Transport**: Socket.IO over WebSocket/long-polling
- **Authentication**: JWT token passed in `connect` auth payload
- **Rooms**: `user_{id}` for personal notifications, `project_{id}` for project events
- **Broadcast helpers**: `broadcast_notification`, `broadcast_to_project`, `broadcast_task_update`

---

## Low-Level Design (LLD)

### 1. Module / Package Structure

```
task_management_system/
├── app/                        # Main application package
│   ├── __init__.py             # create_app() factory, extension init
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── enums.py            # Shared enumerations + rich metadata dicts
│   │   ├── user.py             # User model
│   │   ├── project.py          # Project model
│   │   ├── task.py             # Task model (supports subtasks, labels)
│   │   ├── sprint.py           # Sprint model with burndown helpers
│   │   ├── task_comment.py     # Comment model
│   │   ├── task_attachment.py  # Attachment model
│   │   ├── project_member.py   # Many-to-many User↔Project with permissions
│   │   ├── time_log.py         # Time tracking per task/user
│   │   └── notification.py     # System notification model
│   ├── routes/                 # Flask Blueprints (HTTP layer only)
│   │   ├── __init__.py         # register_blueprints() + health routes
│   │   ├── auth_routes.py
│   │   ├── task_routes.py
│   │   ├── project_routes.py
│   │   ├── sprint_routes.py
│   │   ├── comment_routes.py
│   │   ├── notification_routes.py
│   │   ├── analytics_routes.py
│   │   ├── enum_routes.py
│   │   └── cache_routes.py
│   ├── services/               # Business logic (no Flask request context assumed)
│   │   ├── auth_service.py
│   │   ├── task_service.py
│   │   ├── project_service.py
│   │   ├── sprint_service.py
│   │   ├── comment_service.py
│   │   ├── notification_service.py
│   │   └── analytics_service.py
│   └── utils/                  # Cross-cutting utilities
│       ├── response.py         # Standardised JSON response helpers
│       ├── logger.py           # Logging setup + structured log helpers
│       ├── cache_utils.py      # Redis cache init + decorators + invalidation
│       ├── jwt_utils.py        # JWT helper stubs
│       ├── decorators.py       # @admin_required, @log_request
│       ├── validators.py       # Email, password, task field validation
│       ├── database.py         # DB init + connection test
│       └── socket_utils.py     # Socket.IO init + event handlers + broadcast helpers
├── config/
│   ├── __init__.py             # get_config() factory + __all__
│   ├── base.py                 # BaseConfig (shared settings)
│   └── dev.py                  # DevelopmentConfig
├── migrations/                 # Alembic migration environment
├── scripts/
│   ├── init_db.py              # One-shot DB initialisation script
│   ├── setup_sample_data.py    # Sample data seeder
│   └── test_socket_client.py   # Manual Socket.IO test client
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements/
│   ├── base.txt                # Production dependencies
│   ├── dev.txt                 # Development / test dependencies
│   └── production.txt          # Production server (Gunicorn, Gevent)
├── app.py                      # Development entry point
├── wsgi.py                     # Production WSGI entry point
├── manage.py                   # Click CLI (create_db, drop_db, reset_db, show_tables)
└── DESIGN.md                   # This document
```

### 2. Data Model

#### Entity Relationship Summary

```
User ──< ProjectMember >── Project
 │                            │
 │                           ├──< Sprint
 ├── created Tasks            │
 └── assigned Tasks ──────< Task >──────< TaskComment
                               │              (User)
                               ├──< TimeLog (User)
                               ├──< TaskAttachment (User)
                               └──< Notification (User)
```

#### Key Model Details

**User**
```python
id, name, email, password_hash, role (UserRole)
avatar_url, bio, skills (JSON), github_username, linkedin_url, phone
timezone, daily_work_hours, hourly_rate
is_active, last_login, created_at, updated_at
```

**Project**
```python
id, name, description, status (ProjectStatus)
repository_url, documentation_url, technology_stack (JSON)
start_date, end_date, estimated_hours
owner_id → User, client_name, client_email
created_at, updated_at
```

**Task**
```python
id, title, description
status (TaskStatus), priority (TaskPriority), task_type (TaskType)
assigned_to_id → User, created_by_id → User
project_id → Project, sprint_id → Sprint (nullable)
parent_task_id → Task (nullable, for subtasks)
due_date, start_date, completion_date
estimated_hours, actual_hours, story_points, estimation_unit
labels (JSON), acceptance_criteria
created_at, updated_at
```

**Sprint**
```python
id, name, description, status (SprintStatus)
project_id → Project
start_date, end_date, goal
capacity_hours, velocity_points
created_at, updated_at
```

**ProjectMember** (User ↔ Project junction with permissions)
```python
id, project_id → Project, user_id → User, role
can_create_tasks, can_edit_tasks, can_delete_tasks
can_manage_sprints, can_manage_members
joined_at, updated_at
UNIQUE(project_id, user_id)
```

**TimeLog**
```python
id, task_id → Task, user_id → User
hours, description, work_date
logged_at, updated_at
```

**Notification**
```python
id, user_id → User, task_id → Task (nullable)
type (NotificationType), title, message
related_user_id → User (nullable)
project_id → Project (nullable), sprint_id → Sprint (nullable)
read (bool), read_at, created_at
```

### 3. Service Layer Contracts

All service methods return **plain dicts** (never Flask response tuples).  
Route handlers are responsible for mapping dict values to HTTP status codes.

```python
# Success:
{"key": value, ...}

# Error:
{"error": "Human-readable error message"}

# Auth/boolean result:
{"success": True/False, "error": "...", ...}
```

### 4. Response Schema

Every HTTP response from any endpoint uses the same envelope:

```json
{
  "success": true,
  "message": "Human-readable outcome",
  "data": { ... },
  "timestamp": "2024-01-17T10:30:00.123456"
}
```

HTTP status codes follow REST conventions:  
`200` OK · `201` Created · `400` Bad Request · `401` Unauthorized  
`403` Forbidden · `404` Not Found · `422` Validation Error · `500` Server Error

### 5. Logging Architecture

```
setup_logging(app)
    ├── Console handler  – colored, INFO level
    ├── app.log          – rotating 10 MB × 5, all levels
    └── errors.log       – rotating 10 MB × 5, ERROR+ only

Named loggers (get_logger(name)):
    app.auth    – auth/registration events
    app.tasks   – task operations
    app.projects – project operations
    app.cache   – cache hits/misses/invalidations
    app.socket  – Socket.IO events
    app.api     – incoming HTTP requests
    app.db      – database queries
```

### 6. Caching Keys Convention

```
{prefix}:user_{user_id}                 – user-scoped data
{prefix}:user_{user_id}:{params_hash}   – with query parameters
projects:all                            – global project list
projects:{project_id}                   – single project
login:{email}                           – login result (5 min)
```

### 7. Configuration Hierarchy

```
BaseConfig (config/base.py)
└── DevelopmentConfig (config/dev.py)
    - DEBUG, SQLALCHEMY_ECHO
    - SQLALCHEMY_DATABASE_URI (override via DATABASE_URL env var)
    - CACHE_REDIS_URL, CACHE_DEFAULT_TIMEOUT
    - LOG_TO_STDOUT
```

Sensitive values (secrets, connection strings) should always be provided via
environment variables rather than being hard-coded in config files.

### 8. Deployment Targets

| Mode | Command |
|------|---------|
| Development | `python app.py` |
| Production (sync) | `gunicorn -w 4 wsgi:app` |
| Production (async) | `gunicorn --worker-class gevent wsgi:app` |
| Docker | `docker-compose -f docker/docker-compose.yml up --build` |

### 9. Extension Checklist for Future Work

- [ ] Add `config/production.py` and `config/testing.py`
- [ ] Enable test suite: uncomment `pytest` in `requirements/dev.txt`, create `tests/` package
- [ ] Replace hard-coded DB URL in `config/dev.py` with `DATABASE_URL` env var
- [ ] Add `flask db migrate` automation to CI/CD pipeline
- [ ] Add rate limiting (`flask-limiter`) on auth endpoints
- [ ] Consider moving Celery task definitions to `app/tasks/` package
