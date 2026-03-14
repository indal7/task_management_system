# 🚀 Enterprise Task Management System

A comprehensive Flask-based REST API for managing tasks, projects, and sprints designed for software development teams. Built with enterprise-grade features including agile project management, time tracking, team collaboration, and advanced analytics.

## ✨ Key Features

### 🔐 **User Management**
- **JWT Authentication** with access & refresh tokens
- **11 Specialized Roles**: Admin, Project Manager, Team Lead, Senior Developer, Developer, QA Engineer, DevOps Engineer, UI/UX Designer, Business Analyst, Product Owner, Scrum Master
- **User Profiles** with skills, GitHub/LinkedIn integration, timezone support
- **Role-based Permissions** with project-specific access control

### 📋 **Advanced Task Management**
- **9 Status Workflow**: Backlog → TODO → In Progress → In Review → Testing → Done → Deployed
- **4 Priority Levels**: Critical, High, Medium, Low with escalation timeframes
- **10 Task Types**: Feature, Bug, Enhancement, Refactor, Documentation, Testing, Deployment, Research, Maintenance, Security
- **Rich Metadata**: Story points, time estimates, acceptance criteria, labels, parent-child relationships
- **File Attachments** with support for code files, documents, images

### 🏗️ **Project & Sprint Management**
- **Complete Project Lifecycle**: Planning → Active → Completed with team management
- **Agile Sprint Support**: Sprint planning, burndown charts, velocity tracking
- **Technology Stack Tracking** and client information management
- **Team Permissions**: Project-specific roles and capabilities

### ⏱️ **Time Tracking & Analytics**
- **Detailed Time Logging** with work date tracking and validation
- **Productivity Analytics**: User performance, completion rates, workload analysis
- **Project Progress**: Real-time completion percentages and resource utilization
- **Sprint Analytics**: Velocity tracking and burndown reports

### 🔔 **Real-time Notifications**
- **8 Notification Types**: Task assignments, updates, completions, comments, mentions, project updates, sprint events
- **Smart Notification Management** with read/unread states and cleanup

## 🛠 Technology Stack

**Backend Framework**
- Flask 3.1.1 with modular blueprint architecture
- SQLAlchemy ORM with PostgreSQL database
- Flask-JWT-Extended for authentication
- Flask-Migrate for database migrations

**Production Features**
- Celery + Redis for background tasks
- Flask-SocketIO for real-time updates
- Gunicorn WSGI server support
- Docker containerization ready

**Additional Libraries**
- Pillow (image processing), bcrypt (security), python-dotenv (configuration)
- pytest (testing), Flask-CORS (API support), Flask-Limiter (rate limiting)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis (optional, for background tasks)

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd task_management_system
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with your database credentials

# Database initialization
# python scripts/init_db.py
python -m scripts.init_db


# Start the application
python app.py
```

**Access**: `http://localhost:5000`

### Sample Login Credentials
```
Admin: admin@example.com / admin123
Project Manager: manager@example.com / manager123
Developer (You): indalsaroj404@gmail.com / 123456789
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Flask
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true

# Optional Features
REDIS_URL=redis://localhost:6379/0
MAIL_SERVER=smtp.gmail.com
MAX_CONTENT_LENGTH=16777216
```

### Configuration Environments
- **Development** - Debug enabled, local database
- **Production** - Optimized performance, security enabled
- **Testing** - In-memory SQLite for tests
- **Docker** - Container-specific settings

## 📚 API Overview

### Authentication
```http
POST /api/auth/register - Register new user
POST /api/auth/login    - User login
GET  /api/auth/me       - Get current user
PUT  /api/auth/profile  - Update profile
```

### Task Management
```http
GET    /api/tasks              - Get tasks (with filters)
POST   /api/tasks              - Create task
GET    /api/tasks/{id}         - Get task details
PUT    /api/tasks/{id}         - Update task
DELETE /api/tasks/{id}         - Delete task
POST   /api/tasks/{id}/assign  - Assign task
POST   /api/tasks/{id}/comments - Add comment
POST   /api/tasks/{id}/time    - Log time
```

### Project & Sprint Management
```http
GET  /api/projects     - Get projects
POST /api/projects     - Create project
GET  /api/sprints      - Get sprints
POST /api/sprints      - Create sprint
POST /api/sprints/{id}/start - Start sprint
```

### Analytics & Notifications
```http
GET /api/analytics/task-completion - Task analytics
GET /api/notifications - Get notifications
GET /api/enums - Get all system enums
```

### Request/Response Format
All API responses use standardized format:
```json
{
  "success": true,
  "message": "Operation completed successfully", 
  "data": { /* actual response data */ },
  "timestamp": "2024-01-17T10:30:00.123456"
}
```

**Authentication**: Include `Authorization: Bearer <jwt-token>` in headers for protected endpoints.

## 🗃️ Database Schema

### Core Tables
- **users** - User accounts with roles and profiles
- **projects** - Project containers with team management  
- **tasks** - Work items with rich metadata
- **sprints** - Time-boxed iterations for agile development
- **project_members** - User-project associations with permissions
- **time_logs** - Time tracking entries
- **notifications** - System notifications
- **task_comments** - Task discussions
- **task_attachments** - File uploads

### Key Relationships
```
User (1) ←→ (Many) Tasks [assigned/created]
Project (1) ←→ (Many) Tasks, Sprints, Members
Task (1) ←→ (Many) Comments, Attachments, TimeLogs
Sprint (1) ←→ (Many) Tasks
```

## 🐳 Docker Deployment

### Development
```bash
# Build and run
docker build -t task-management .
docker run -p 5000:5000 task-management

# Or with Docker Compose
docker-compose up --build
```

### Production
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Or with Gunicorn
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_tasks.py -v
```

## 📊 Sample Data

The system includes comprehensive sample data:
- **9 Users** across different roles with realistic profiles
- **6 Projects** in various states with technology stacks
- **4 Active Sprints** with velocity tracking
- **10+ Tasks** with different types, priorities, and statuses
- **Time logs, comments, notifications** for realistic testing

Access sample data by running: `python scripts/init_db.py`

## 🔒 Security Features

- **JWT Token Authentication** with configurable expiration
- **Role-based Access Control** with project-specific permissions
- **Input Validation** and SQL injection prevention
- **Rate Limiting** and CORS configuration
- **Secure Password Hashing** with bcrypt
- **Environment-based Configuration** for secrets management

## 📈 Analytics & Monitoring

### Built-in Analytics
- Task completion rates and cycle times
- User productivity and workload distribution  
- Project progress and resource utilization
- Sprint velocity and burndown tracking

### Health Monitoring
```bash
GET /health     - General health check
GET /health/db  - Database connectivity
GET /health/ready - Kubernetes readiness probe
```

## 🚀 Production Deployment

### Requirements
- PostgreSQL database (AWS RDS recommended)
- Redis for caching (optional but recommended)
- SMTP server for email notifications
- SSL certificates for HTTPS

### Deployment Checklist
- [ ] Update environment variables
- [ ] Configure production database
- [ ] Set up reverse proxy (Nginx)
- [ ] Configure SSL certificates  
- [ ] Set up monitoring and logging
- [ ] Run database migrations
- [ ] Configure backup strategy

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

---

## 🆘 Support

- **Repository Issues**: Create GitHub issues for bugs/features
- **Documentation**: Check `/health` endpoint when running
- **API Testing**: Use provided Postman collection
- **Sample Data**: Run initialization script for development data

**Production API**: Available at configured endpoint
**Development**: `http://localhost:5000`

*Built with ❤️ for enterprise software development teams*