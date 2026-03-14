# 🚀 Enterprise Task Management System

A comprehensive Flask-based REST API for managing tasks, projects, and sprints designed for software development teams. Built with enterprise-grade features including agile project management, time tracking, team collaboration, and advanced analytics.

---

## 📋 Table of Contents

1. [Key Features](#-key-features)
2. [Technology Stack](#-technology-stack)
3. [Local Setup Guide](#-local-setup-guide)
4. [AWS Prerequisites](#-aws-prerequisites)
5. [GitHub Secrets Setup](#-github-secrets-setup)
6. [Terraform Deployment](#-terraform-deployment)
7. [Docker & ECR Setup](#-docker--ecr-setup)
8. [GitHub Actions Deployment](#-github-actions-deployment)
9. [Accessing the Application](#-accessing-the-application)
10. [API Overview](#-api-overview)
11. [Database Schema](#-database-schema)
12. [Testing](#-testing)
13. [Troubleshooting](#-troubleshooting)
14. [Contributing](#-contributing)

---

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

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|------------|
| **Web Framework** | Flask 3.1.1 with modular blueprint architecture |
| **Database ORM** | SQLAlchemy + Flask-Migrate (Alembic) |
| **Database** | PostgreSQL 14 (AWS RDS in production) |
| **Authentication** | Flask-JWT-Extended |
| **Caching** | Redis 7 (AWS ElastiCache in production) |
| **Real-time** | Flask-SocketIO |
| **Task Queue** | Celery + Redis |
| **WSGI Server** | Gunicorn with Gevent workers |
| **Containerization** | Docker + Docker Compose |
| **Infrastructure** | Terraform (AWS) |
| **CI/CD** | GitHub Actions |
| **Image Registry** | AWS ECR |
| **Secrets** | AWS Secrets Manager |

---

## 💻 Local Setup Guide

Follow these steps to run the application on your local machine.

### Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.11+** — [Download here](https://www.python.org/downloads/)
- **PostgreSQL 12+** — [Download here](https://www.postgresql.org/download/)
- **Redis 7** (optional, for caching/real-time features) — [Download here](https://redis.io/download/)
- **Git** — [Download here](https://git-scm.com/)
- **Docker & Docker Compose** (optional, for containerized local dev) — [Download here](https://docs.docker.com/get-docker/)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/indal7/task_management_system.git
cd task_management_system
```

### Step 2 — Create a Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3 — Install Dependencies

```bash
# Install all development dependencies (includes Flask, pytest, flake8, etc.)
pip install -r requirements/dev.txt
```

> **Note:** `dev.txt` already includes everything from `base.txt`. For production, use `requirements/base.txt` and `requirements/production.txt`.

### Step 4 — Set Up a Local PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database and user
CREATE DATABASE taskmanager;
CREATE USER taskmanager_user WITH PASSWORD 'your_local_password';
GRANT ALL PRIVILEGES ON DATABASE taskmanager TO taskmanager_user;
\q
```

### Step 5 — Create the Environment File

```bash
# Create the env directory and a local .env file
mkdir -p env
```

Create a file `env/.env.dev` with the following content:

```bash
# Flask
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true

# Database (local PostgreSQL)
DATABASE_URL=postgresql://taskmanager_user:your_local_password@localhost:5432/taskmanager

# Security — change these to any random strings locally
SECRET_KEY=local-dev-secret-key-change-me
JWT_SECRET_KEY=local-jwt-secret-key-change-me
JWT_ACCESS_TOKEN_EXPIRES=3600

# Redis (optional — remove if not installed)
REDIS_URL=redis://localhost:6379/0
CACHE_REDIS_URL=redis://localhost:6379/1
CACHE_TYPE=RedisCache
CACHE_DEFAULT_TIMEOUT=300

# Logging
LOG_LEVEL=DEBUG
LOG_TO_STDOUT=true
```

> **Tip:** Generate strong secret keys with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### Step 6 — Initialize the Database

```bash
# Apply database migrations
flask db upgrade

# Seed the database with sample data (users, projects, tasks, etc.)
python -m scripts.init_db
```

### Step 7 — Start the Application

```bash
python app.py
```

The app will be available at **http://localhost:5000**

### Step 8 — Verify It's Working

```bash
# Check health
curl http://localhost:5000/health

# Check DB connectivity
curl http://localhost:5000/health/db
```

### Sample Login Credentials

Once you've seeded the database, you can log in with:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@example.com` | `admin123` |
| Project Manager | `manager@example.com` | `manager123` |
| Developer | `indalsaroj404@gmail.com` | `123456789` |

### Option B — Run with Docker Compose (Easiest)

If you have Docker installed, this is the simplest way to run everything locally (app + Redis in one command):

```bash
# Start app + Redis
cd docker
docker compose up --build

# App will be available at http://localhost:5000
```

---

## ☁️ AWS Prerequisites

Before deploying to AWS, you need the following resources and permissions. This project's Terraform code provisions all of them automatically — but you must have an AWS account ready.

### Required AWS Account Setup

1. **Create an AWS Account** at [https://aws.amazon.com](https://aws.amazon.com) if you don't have one.

2. **Create an IAM User for Terraform/CI** with programmatic access:
   - Go to **AWS Console → IAM → Users → Create User**
   - User name: e.g., `taskmanager-deployer`
   - Select **Attach policies directly**
   - Attach these managed policies (or use a custom policy):
     - `AmazonEC2FullAccess`
     - `AmazonRDSFullAccess`
     - `AmazonElastiCacheFullAccess`
     - `AmazonECRFullAccess`
     - `SecretsManagerReadWrite`
     - `IAMFullAccess`
     - `AmazonVPCFullAccess`
   - Click **Create User**, then go to **Security credentials → Create access key**
   - Choose **Application running outside AWS**
   - **Save the Access Key ID and Secret Access Key** — you will need them for GitHub Secrets

3. **Install and Configure AWS CLI** on your local machine:
   ```bash
   # Install AWS CLI
   # macOS:
   brew install awscli

   # Linux:
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip && sudo ./aws/install

   # Configure it
   aws configure
   # Enter: AWS Access Key ID, Secret Access Key, Region (ap-south-1), Output (json)
   ```

4. **Create an SSH Key Pair** for EC2 access:
   ```bash
   # Generate an SSH key pair (if you don't already have one)
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

   # The public key (~/.ssh/id_rsa.pub) will be uploaded to EC2 by Terraform
   # The private key (~/.ssh/id_rsa) is what you use to SSH into EC2
   ```

### AWS Resources Provisioned by Terraform

Terraform will automatically create all of the following:

| Resource | Type | Purpose |
|----------|------|---------|
| **VPC** | Networking | Isolated network (10.0.0.0/16) |
| **Subnets** | Networking | 2 public + 2 private subnets |
| **Internet Gateway + NAT** | Networking | Internet access |
| **Security Groups** | Security | Firewall rules for EC2, RDS, Redis |
| **EC2 Instance** | Compute | t3.small Ubuntu 22.04 — runs the app |
| **Elastic IP** | Compute | Static public IP for EC2 |
| **RDS PostgreSQL** | Database | db.t3.micro, PostgreSQL 14 |
| **ElastiCache Redis** | Cache | cache.t3.micro, Redis 7 |
| **ECR Repository** | Container Registry | Stores Docker images |
| **Secrets Manager** | Secrets | DB password, SECRET_KEY, JWT_SECRET_KEY |
| **IAM Role** | Security | EC2 permissions to access ECR, Secrets, SSM |

### Estimated AWS Costs (ap-south-1)

> ⚠️ These resources are **not free tier eligible** and will incur costs.

| Resource | Estimated Monthly Cost |
|----------|----------------------|
| EC2 t3.small | ~$15–20 |
| RDS db.t3.micro | ~$15–20 |
| ElastiCache cache.t3.micro | ~$12–15 |
| NAT Gateway | ~$35–45 |
| ECR (storage + transfer) | ~$1–5 |
| **Total (approx.)** | **~$78–105/month** |

> 💡 **Tip:** To reduce costs in dev, you can set `enable_nat_gateway = false` and place EC2 in a public subnet (already the default in `terraform.tfvars.example`).

---

## 🔑 GitHub Secrets Setup

GitHub Actions needs credentials to build Docker images, push to ECR, and deploy to EC2. All secrets are stored in **GitHub Secrets** — never committed to code.

### Step-by-Step: Add Secrets to GitHub

1. **Go to your repository** on GitHub: `https://github.com/indal7/task_management_system`

2. Click **Settings** (top menu of the repo)

3. In the left sidebar, click **Secrets and variables → Actions**

4. Click **New repository secret** for each secret below

---

### Required Secrets

#### 🔐 Secret 1: `AWS_ACCESS_KEY_ID`

**What it is:** The Access Key ID of the IAM user you created.

**How to get it:**
```
AWS Console → IAM → Users → taskmanager-deployer → Security credentials → Access keys
```

**Example value:** `AKIAIOSFODNN7EXAMPLE`

---

#### 🔐 Secret 2: `AWS_SECRET_ACCESS_KEY`

**What it is:** The Secret Access Key paired with `AWS_ACCESS_KEY_ID`.

**How to get it:** This was shown once when you created the access key. If lost, create a new access key.

**Example value:** `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

---

#### 🔐 Secret 3: `AWS_REGION`

**What it is:** The AWS region where your infrastructure is deployed.

**Value:** `ap-south-1` (Mumbai — or whichever region you used in Terraform)

---

#### 🔐 Secret 4: `ECR_REPOSITORY`

**What it is:** The name of your ECR repository (not the full URL, just the name).

**How to get it:** After running `terraform apply`, run:
```bash
cd terraform
terraform output ecr_repository_url
# Output: 492661377251.dkr.ecr.ap-south-1.amazonaws.com/taskmanager-dev
# The repository name is: taskmanager-dev
```

**Value:** `taskmanager-dev` (or your project name + environment)

---

#### 🔐 Secret 5: `EC2_HOST`

**What it is:** The public IP address of your EC2 instance.

**How to get it:** After running `terraform apply`, run:
```bash
cd terraform
terraform output ec2_public_ip
# Example output: 52.66.118.215
```

> ⚠️ **Important:** Every time you destroy and re-create the EC2 instance, it gets a new IP. You must update this secret with the new IP.

**Value:** `52.66.118.215` (replace with your actual IP)

---

#### 🔐 Secret 6: `EC2_KEY`

**What it is:** The **private** SSH key used to connect to EC2 (the contents of `~/.ssh/id_rsa`).

**How to get it:**
```bash
# Print your private key (copy the entire output including BEGIN/END lines)
cat ~/.ssh/id_rsa
```

**Value:** The full contents of your private key file, like:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAA...
...your key contents...
-----END OPENSSH PRIVATE KEY-----
```

> ⚠️ **Security:** Never share this key publicly. It gives full SSH access to your server.

---

### Summary Table

| Secret Name | Description | Where to Find |
|-------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key ID | AWS Console → IAM → Access Keys |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | Created with access key (save it!) |
| `AWS_REGION` | AWS region | e.g., `ap-south-1` |
| `ECR_REPOSITORY` | ECR repo name | `terraform output ecr_repository_url` |
| `EC2_HOST` | EC2 public IP address | `terraform output ec2_public_ip` |
| `EC2_KEY` | SSH private key contents | `cat ~/.ssh/id_rsa` |

### Verify Secrets Are Set

After adding all secrets, go to:
**Settings → Secrets and variables → Actions**

You should see all 6 secrets listed. ✅

---

## 🏗️ Terraform Deployment

Terraform provisions all AWS infrastructure automatically. Follow these steps to set it up.

### Prerequisites

1. **Install Terraform** (version ≥ 1.6.0):
   ```bash
   # macOS
   brew install terraform

   # Linux (manual)
   wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
   unzip terraform_1.7.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/

   # Verify
   terraform --version
   ```

2. **Configure AWS CLI** (if not done already):
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, Region, and output format
   ```

### Step 1 — Navigate to Terraform Directory

```bash
cd terraform
```

### Step 2 — Create Your Variables File

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_name = "taskmanager"
environment  = "dev"
aws_region   = "ap-south-1"

# Networking
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
availability_zones   = ["ap-south-1a", "ap-south-1b"]
enable_nat_gateway   = true

# EC2
ec2_ami_id          = "ami-0f58b397bc5c1f2e8"   # Ubuntu 22.04 LTS in ap-south-1
ec2_instance_type   = "t3.small"
ssh_public_key_path = "~/.ssh/id_rsa.pub"        # Your SSH public key
admin_cidr          = "0.0.0.0/0"               # Restrict to your IP in production!

flask_port              = 5000
ec2_root_volume_size_gb = 20

# RDS PostgreSQL
rds_engine_version           = "14.17"
rds_instance_class           = "db.t3.micro"
rds_allocated_storage_gb     = 20
rds_max_allocated_storage_gb = 100
rds_db_name                  = "taskmanager"
rds_username                 = "taskmanager_user"
rds_backup_retention_days    = 7
rds_multi_az                 = false
rds_deletion_protection      = false
rds_skip_final_snapshot      = true

# ElastiCache Redis
redis_node_type       = "cache.t3.micro"
redis_engine_version  = "7.1"
redis_num_cache_nodes = 1
redis_port            = 6379

# ECR
ecr_image_tag_mutability = "MUTABLE"
ecr_max_image_count      = 10

# IMPORTANT: Replace with strong random values!
app_secret_key     = "replace-with-a-strong-random-secret-min-32-chars"
app_jwt_secret_key = "replace-with-a-different-strong-secret-min-32-chars"
```

> **Generate strong secrets:**
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

> ⚠️ **Never commit `terraform.tfvars` to git** — it contains sensitive values. It is already in `.gitignore`.

### Step 3 — Initialize Terraform

```bash
terraform init
```

This downloads the AWS provider and module dependencies.

### Step 4 — Preview Changes

```bash
terraform plan
```

Review what Terraform will create. You should see ~30–40 resources being created.

### Step 5 — Apply (Create Infrastructure)

```bash
terraform apply
```

Type `yes` when prompted. This takes **5–10 minutes** to complete.

### Step 6 — Save the Outputs

After `terraform apply` completes, note the outputs:

```bash
terraform output
```

You'll see something like:

```
app_url                 = "http://52.66.118.215:5000"
ec2_public_ip           = "52.66.118.215"
ecr_repository_url      = "492661377251.dkr.ecr.ap-south-1.amazonaws.com/taskmanager-dev"
health_url              = "http://52.66.118.215:5000/health"
rds_endpoint            = "taskmanager-dev-db.xxxx.ap-south-1.rds.amazonaws.com:5432"
redis_endpoint          = "taskmanager-dev-redis.xxxx.cache.amazonaws.com"
ssh_command             = "ssh -i ~/.ssh/id_rsa ubuntu@52.66.118.215"
```

**Use these values to update your GitHub Secrets** (`EC2_HOST`, `ECR_REPOSITORY`).

### Step 7 — Get Specific Outputs

```bash
# Get EC2 IP (for EC2_HOST secret)
terraform output -raw ec2_public_ip

# Get ECR repository name (for ECR_REPOSITORY secret)
terraform output -raw ecr_repository_url | cut -d'/' -f2
```

### Destroy Infrastructure (When Done)

```bash
# Destroy all resources (stops billing)
terraform destroy

# Or destroy only EC2 (to recreate with updated user-data)
terraform destroy -target 'module.ec2.aws_instance.this'
terraform apply -target 'module.ec2'
```

> ⚠️ **Warning:** `terraform destroy` permanently deletes all data including the RDS database. Make sure you have backups first.

---

## 🐳 Docker & ECR Setup

### Build Docker Image Locally

```bash
# From the root of the repository
docker build -f docker/Dockerfile -t taskmanager:latest .
```

### Run Locally with Docker

```bash
docker run -d \
  --name taskmanager_app \
  -p 5000:5000 \
  --env-file env/.env.dev \
  taskmanager:latest
```

### Push to AWS ECR Manually

Use this if you want to push an image manually (GitHub Actions does this automatically).

#### Step 1 — Authenticate Docker with ECR

```bash
# Get your ECR registry URL
ECR_REGISTRY=$(aws ecr describe-repositories \
  --repository-names taskmanager-dev \
  --region ap-south-1 \
  --query 'repositories[0].repositoryUri' \
  --output text | cut -d'/' -f1)

# Login to ECR
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY
```

#### Step 2 — Build and Tag the Image

```bash
# Get the full ECR repository URL
ECR_REPO_URL=$(aws ecr describe-repositories \
  --repository-names taskmanager-dev \
  --region ap-south-1 \
  --query 'repositories[0].repositoryUri' \
  --output text)

# Build and tag
docker build -f docker/Dockerfile \
  -t $ECR_REPO_URL:latest \
  -t $ECR_REPO_URL:$(git rev-parse --short HEAD) \
  .
```

#### Step 3 — Push the Image

```bash
docker push $ECR_REPO_URL:latest
docker push $ECR_REPO_URL:$(git rev-parse --short HEAD)
```

#### Or use Terraform's built-in push commands

```bash
cd terraform
terraform output -raw ecr_push_commands
# This prints the exact commands to run for your environment
```

---

## 🤖 GitHub Actions Deployment

The repository includes two GitHub Actions workflows:

### CI Workflow (`.github/workflows/ci.yml`)

**Triggers:** Every push and pull request to any branch.

**What it does:**
1. Installs Python 3.11 and dev dependencies
2. Runs `flake8` linter on `app/` and `config/`
3. Runs `pytest` tests with coverage report

You don't need to configure anything — this works automatically.

### Deploy Workflow (`.github/workflows/deploy.yml`)

**Triggers:** Every push to the `master` branch.

**What it does:**

```
Push to master
    │
    ├─► Job 1: build-and-push
    │     ├── Checkout code
    │     ├── Configure AWS credentials (from secrets)
    │     ├── Login to ECR
    │     ├── Build Docker image (docker/Dockerfile)
    │     ├── Tag with git SHA + "latest"
    │     └── Push to ECR
    │
    └─► Job 2: deploy (runs after Job 1)
          ├── SSH into EC2 using EC2_KEY + EC2_HOST
          ├── Authenticate EC2 with ECR
          ├── Pull the new Docker image
          ├── Restart the app (docker compose or docker run)
          ├── Wait 10 seconds for startup
          └── Verify /health endpoint responds
```

### Trigger a Deployment

```bash
# Simply push to master
git add .
git commit -m "your commit message"
git push origin master
```

### Monitor the Deployment

1. Go to your repo on GitHub
2. Click **Actions** tab
3. Click the latest **"Deploy Flask to EC2"** workflow run
4. Watch the steps in real time

### Deployment Success Output

When deployment succeeds, you'll see:
```
🚀 Deployment successful!
App: http://<EC2_HOST>:5000
Health: http://<EC2_HOST>:5000/health
Image tag: 1d6dba2
```

### Re-run a Failed Deployment

If deployment fails, fix the issue and push again, or:
1. Go to **Actions → Deploy Flask to EC2 → Re-run all jobs**

---

## 🌐 Accessing the Application

### Get Your Application URL

```bash
cd terraform
terraform output app_url
# Output: http://52.66.118.215:5000
```

### Test the Endpoints

```bash
# Basic health check
curl http://<EC2_HOST>:5000/health

# Database connectivity check
curl http://<EC2_HOST>:5000/health/db

# Kubernetes readiness probe
curl http://<EC2_HOST>:5000/health/ready

# API login
curl -X POST http://<EC2_HOST>:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

### Open in Browser

```
http://<EC2_HOST>:5000          # App root
http://<EC2_HOST>:5000/health   # Health check
```

### SSH into the EC2 Instance

```bash
# Get the SSH command from Terraform
cd terraform
terraform output -raw ssh_command

# Then run it:
ssh -i ~/.ssh/id_rsa ubuntu@<EC2_HOST>
```

### Check Application Status on EC2

Once SSH'd in:

```bash
# See running containers
docker ps

# View app logs (live)
docker logs taskmanager_app -f

# View last 50 lines of logs
docker logs taskmanager_app --tail=50

# Check docker-compose services
docker compose -f /home/ubuntu/taskmanager/docker-compose.prod.yml ps

# Restart the app
docker compose -f /home/ubuntu/taskmanager/docker-compose.prod.yml restart
```

### Make an Authenticated API Request

```bash
# Step 1: Login and get the token
TOKEN=$(curl -s -X POST http://<EC2_HOST>:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])")

# Step 2: Use the token
curl http://<EC2_HOST>:5000/api/tasks \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 API Overview

### Authentication
```http
POST /api/auth/register     - Register a new user
POST /api/auth/login        - Log in and receive JWT tokens
POST /api/auth/refresh      - Refresh access token
GET  /api/auth/me           - Get current user profile
PUT  /api/auth/profile      - Update profile
```

### Task Management
```http
GET    /api/tasks                   - List tasks (supports filters)
POST   /api/tasks                   - Create a new task
GET    /api/tasks/{id}              - Get task details
PUT    /api/tasks/{id}              - Update task
DELETE /api/tasks/{id}              - Delete task
POST   /api/tasks/{id}/assign       - Assign task to a user
POST   /api/tasks/{id}/comments     - Add a comment
POST   /api/tasks/{id}/time         - Log time on a task
```

### Project & Sprint Management
```http
GET  /api/projects              - List projects
POST /api/projects              - Create a project
GET  /api/sprints               - List sprints
POST /api/sprints               - Create a sprint
POST /api/sprints/{id}/start    - Start a sprint
```

### Analytics & Notifications
```http
GET /api/analytics/task-completion  - Task completion analytics
GET /api/notifications              - Get user notifications
GET /api/enums                      - Get all system enums (roles, statuses, etc.)
```

### Health Checks
```http
GET /health       - Overall application health
GET /health/db    - Database connectivity
GET /health/ready - Readiness probe (for Kubernetes/load balancers)
```

### Request/Response Format

All API responses follow this standardized format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { },
  "timestamp": "2024-01-17T10:30:00.123456"
}
```

**Authentication:** Include `Authorization: Bearer <jwt-token>` in headers for all protected endpoints.

---

## 🗃️ Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts with roles and profiles |
| `projects` | Project containers with team management |
| `tasks` | Work items with rich metadata |
| `sprints` | Time-boxed iterations for agile development |
| `project_members` | User-project associations with permissions |
| `time_logs` | Time tracking entries per task |
| `notifications` | System-generated notifications |
| `task_comments` | Task discussion threads |
| `task_attachments` | File uploads linked to tasks |

### Key Relationships
```
User (1) ←→ (Many) Tasks [assigned/created]
Project (1) ←→ (Many) Tasks, Sprints, Members
Task (1) ←→ (Many) Comments, Attachments, TimeLogs
Sprint (1) ←→ (Many) Tasks
```

---

## 🧪 Testing

### Run All Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Run Specific Tests

```bash
# Authentication tests
pytest tests/test_auth.py -v

# Health check tests
pytest tests/test_health.py -v
```

### Sample Data

Seed realistic sample data for development and testing:

```bash
python -m scripts.init_db
```

This creates:
- **9 Users** across different roles with realistic profiles
- **6 Projects** in various states
- **4 Active Sprints** with velocity tracking
- **10+ Tasks** with different types, priorities, and statuses
- Time logs, comments, and notifications

---

## 🔧 Troubleshooting

### ❌ SSH Connection Timeout

**Error:**
```
ssh: connect to host <EC2_HOST> port 22: Connection timed out
```

**Causes & Fixes:**

1. **EC2 IP changed** — Every time you recreate EC2, the IP changes. Update `EC2_HOST` in GitHub Secrets:
   ```bash
   cd terraform
   terraform output -raw ec2_public_ip
   # Update EC2_HOST in GitHub Settings → Secrets and variables → Actions
   ```

2. **EC2 is still booting** — Wait 2–3 minutes after first creation, then re-run the workflow.

3. **Security Group blocking SSH** — Check that port 22 is open:
   ```
   AWS Console → EC2 → Security Groups → taskmanager-ec2-sg → Inbound rules
   # Port 22 should be open (to your IP or 0.0.0.0/0 for dev)
   ```

---

### ❌ Host Key Verification Failed

**Error:**
```
Host key for <IP> has changed and you have requested strict checking.
```

**Fix:** The EC2 instance was recreated. Remove the old SSH key from your known hosts:

```bash
ssh-keygen -R <EC2_IP>
# Then try connecting again:
ssh -i ~/.ssh/id_rsa ubuntu@<EC2_IP>
```

---

### ❌ Permission Denied on `.env.prod`

**Error:**
```
open /home/ubuntu/taskmanager/env/.env.prod: permission denied
```

**Fix:** SSH into EC2 and fix the file permissions:

```bash
ssh -i ~/.ssh/id_rsa ubuntu@<EC2_IP>

sudo chown ubuntu:ubuntu /home/ubuntu/taskmanager/env/.env.prod
sudo chmod 644 /home/ubuntu/taskmanager/env/.env.prod

# Verify
ls -la /home/ubuntu/taskmanager/env/
```

---

### ❌ Docker Image Pull Failed (ECR Auth Error)

**Error:**
```
no basic auth credentials
```

**Fix:** The EC2 instance lost ECR authentication. SSH in and re-authenticate:

```bash
ssh -i ~/.ssh/id_rsa ubuntu@<EC2_IP>

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin \
  $(aws ecr describe-repositories \
    --repository-names taskmanager-dev \
    --region ap-south-1 \
    --query 'repositories[0].repositoryUri' \
    --output text | cut -d'/' -f1)
```

---

### ❌ App Not Responding After Deployment

**Error:**
```
⚠️ App may not be responding yet – check logs above
```

**Fix:** Check logs on EC2:

```bash
ssh -i ~/.ssh/id_rsa ubuntu@<EC2_IP>

# View app logs
docker logs taskmanager_app --tail=100

# Check if container is running
docker ps -a

# Check if port 5000 is listening
ss -tlnp | grep 5000
```

Common causes:
- Database connection failed — check `DATABASE_URL` in `.env.prod`
- App crashed on startup — check logs for Python errors
- Port 5000 blocked by security group — verify AWS Security Group allows port 5000

---

### ❌ Terraform Apply Fails

**Common errors and fixes:**

```bash
# "Error: InvalidClientTokenId" — wrong AWS credentials
aws sts get-caller-identity   # Verify credentials work

# "Error: AMI not found" — AMI ID is region-specific
# For ap-south-1, use: ami-0f58b397bc5c1f2e8
# Find AMI IDs for your region: https://cloud-images.ubuntu.com/locator/ec2/

# "Error: S3 bucket does not exist" — if you enabled S3 backend
# Create the S3 bucket first or comment out the backend block in versions.tf
```

---

### ❌ GitHub Actions: Missing Secrets

**Error:**
```
Error: Input required and not supplied: aws-access-key-id
```

**Fix:** Add all required secrets to GitHub:
```
Settings → Secrets and variables → Actions
```
Required: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECR_REPOSITORY`, `EC2_HOST`, `EC2_KEY`

---

### 🔍 Useful Debugging Commands

```bash
# On EC2 — Check user-data script ran successfully
sudo cat /var/log/cloud-init-output.log

# Check systemd service status
sudo systemctl status taskmanager

# See all Docker containers (including stopped)
docker ps -a

# Follow live logs
docker logs taskmanager_app -f

# Check app environment variables (inside container)
docker exec taskmanager_app env | grep -v PASSWORD

# Test database connection from EC2
docker exec taskmanager_app python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.engine.connect()
    print('DB connected!')
"
```

---

## 🔒 Security Features

- **JWT Token Authentication** with configurable expiration
- **Role-based Access Control** with project-specific permissions
- **Input Validation** and SQL injection prevention (SQLAlchemy ORM)
- **Rate Limiting** with Flask-Limiter
- **CORS Configuration** for API access control
- **Secure Password Hashing** with bcrypt
- **Secrets Management** via AWS Secrets Manager (never in code)
- **Private Subnets** for RDS and Redis (not publicly accessible)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and run tests: `pytest tests/ -v`
4. Lint your code: `flake8 app config`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🆘 Support

- **Bugs & Features**: [Open a GitHub Issue](https://github.com/indal7/task_management_system/issues)
- **Health Check**: `GET /health` when the app is running
- **Logs**: `docker logs taskmanager_app`
- **Infrastructure**: Check Terraform outputs with `terraform output`

**Development**: `http://localhost:5000`  
**Production**: `http://<EC2_HOST>:5000`

*Built with ❤️ for enterprise software development teams*