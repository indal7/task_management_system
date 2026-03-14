# Task Management System – Terraform Infrastructure

This directory contains all Terraform code needed to provision the AWS infrastructure
for the **Task Management System** Flask application.

## Architecture

```
                  ┌──────────────────────────────┐
                  │          ap-south-1            │
                  │                                │
                  │  ┌─── VPC (10.0.0.0/16) ────┐ │
                  │  │                            │ │
Internet ──[IGW]──┼──┤  Public Subnets            │ │
                  │  │  ┌────────────────────┐   │ │
                  │  │  │  EC2 (app server)  │   │ │
                  │  │  │  + Elastic IP      │   │ │
                  │  │  └────────────────────┘   │ │
                  │  │           │ │              │ │
                  │  │      [NAT GW]              │ │
                  │  │           │                │ │
                  │  │  Private Subnets           │ │
                  │  │  ┌──────────┐ ┌─────────┐ │ │
                  │  │  │   RDS    │ │  Redis  │ │ │
                  │  │  │ Postgres │ │ (Cache) │ │ │
                  │  │  └──────────┘ └─────────┘ │ │
                  │  └────────────────────────────┘ │
                  │                                  │
                  │  ECR  ·  Secrets Manager  ·  IAM │
                  └──────────────────────────────────┘
```

## Resources Created

| Module | Resources |
|--------|-----------|
| `networking` | VPC, 2 public subnets, 2 private subnets, IGW, NAT GW, Elastic IP (NAT), route tables |
| `security_groups` | EC2 SG (22, 80, 443, 5000), RDS SG (5432 from EC2), Redis SG (6379 from EC2) |
| `iam` | EC2 IAM role + instance profile (SSM, Secrets Manager, ECR, CloudWatch) |
| `ecr` | ECR repository + lifecycle policy (keep last N images) |
| `secrets` | Secrets Manager entries: DB password, Flask SECRET_KEY, JWT_SECRET_KEY |
| `rds` | RDS PostgreSQL 14, subnet group, parameter group (slow query logging) |
| `elasticache` | ElastiCache Redis 7, subnet group, parameter group |
| `ec2` | EC2 Ubuntu 22.04, key pair, Elastic IP, user-data bootstrap script |

## Prerequisites

1. [Terraform ≥ 1.6](https://developer.hashicorp.com/terraform/install)
2. [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with credentials
3. An SSH key pair (for EC2 access): `ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa`
4. Docker installed locally (for building and pushing images to ECR)

## Quick Start

### 1. Clone and configure

```bash
cd terraform/

# Copy the example var file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars – at minimum set:
#   app_secret_key, app_jwt_secret_key, admin_cidr
```

Or use environment variables for secrets (recommended):

```bash
export TF_VAR_app_secret_key=$(python -c "import secrets; print(secrets.token_hex(32))")
export TF_VAR_app_jwt_secret_key=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### 2. Initialise Terraform

```bash
terraform init
```

### 3. Plan changes

```bash
# Dev environment
terraform plan -var-file=environments/dev/terraform.tfvars

# Production environment
terraform plan -var-file=environments/prod/terraform.tfvars
```

### 4. Apply

```bash
terraform apply -var-file=environments/dev/terraform.tfvars
```

### 5. Build and push the Docker image

After `apply` completes, the outputs include the ECR push commands:

```bash
terraform output ecr_push_commands
```

Run those commands to push your first image:

```bash
# From the repository root
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <ecr_repo_url>

docker build -f docker/Dockerfile -t <ecr_repo_url>:latest .
docker push <ecr_repo_url>:latest
```

### 6. Run database migrations

SSH into the EC2 instance and run migrations:

```bash
ssh -i ~/.ssh/id_rsa ubuntu@$(terraform output -raw ec2_public_ip)

# Inside the instance
cd /home/ubuntu/taskmanager
docker exec taskmanager_app flask db upgrade
```

### 7. Verify

```bash
curl $(terraform output -raw health_url)
# → {"status": "healthy", "service": "task-management-api"}
```

## Using Remote State (recommended for teams)

1. Create an S3 bucket and DynamoDB table for state locking.
2. Uncomment the `backend "s3"` block in `versions.tf` and fill in the bucket name.
3. Re-run `terraform init` to migrate local state to S3.

## Destroying Resources

```bash
terraform destroy -var-file=environments/dev/terraform.tfvars
```

> ⚠️ In production set `rds_deletion_protection = true` and
> `rds_skip_final_snapshot = false` to protect data.

## Module Reference

### `modules/networking`

| Variable | Default | Description |
|----------|---------|-------------|
| `vpc_cidr` | `10.0.0.0/16` | VPC CIDR |
| `public_subnet_cidrs` | `["10.0.1.0/24","10.0.2.0/24"]` | Two public subnets |
| `private_subnet_cidrs` | `["10.0.11.0/24","10.0.12.0/24"]` | Two private subnets |
| `availability_zones` | `["ap-south-1a","ap-south-1b"]` | AZs |
| `enable_nat_gateway` | `true` | Create NAT GW for private subnet egress |

### `modules/security_groups`

Manages three security groups: `ec2`, `rds`, `redis`.
RDS and Redis SGs only allow inbound from the EC2 SG.

### `modules/rds`

| Variable | Default | Description |
|----------|---------|-------------|
| `engine_version` | `14.17` | PostgreSQL version |
| `instance_class` | `db.t3.micro` | RDS instance size |
| `multi_az` | `false` | Enable Multi-AZ standby |
| `deletion_protection` | `false` | Protect from accidental deletion |

### `modules/elasticache`

| Variable | Default | Description |
|----------|---------|-------------|
| `engine_version` | `7.1` | Redis version |
| `node_type` | `cache.t3.micro` | Cache node size |

### `modules/ec2`

The EC2 user-data script (`userdata.sh.tpl`) automatically:
1. Installs Docker and Docker Compose
2. Fetches secrets from AWS Secrets Manager
3. Writes `/home/ubuntu/taskmanager/env/.env.prod`
4. Pulls the latest image from ECR
5. Starts the application with `docker compose`
6. Installs a `systemd` service for auto-restart on reboot

## Environment Variables Injected by Terraform

The following environment variables are written to `.env.prod` by the user-data script
and consumed by the Flask application (`config/production.py`):

| Variable | Source |
|----------|--------|
| `DATABASE_URL` | Built from RDS endpoint + Secrets Manager password |
| `REDIS_URL` | ElastiCache endpoint |
| `CACHE_REDIS_URL` | ElastiCache endpoint (DB 1) |
| `SECRET_KEY` | Secrets Manager |
| `JWT_SECRET_KEY` | Secrets Manager |
| `FLASK_ENV` | `production` |
| `LOG_LEVEL` | `INFO` |
| `RATELIMIT_ENABLED` | `true` |
