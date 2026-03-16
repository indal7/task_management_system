# Task Management System – Terraform Infrastructure

This directory contains all Terraform code to provision the AWS infrastructure
for the **Task Management System** Flask application.

## Architecture

```
                  ┌──────────────────────────────────────────┐
                  │               ap-south-1                  │
                  │                                           │
                  │  ┌─── VPC (10.0.0.0/16) ──────────────┐  │
                  │  │                                      │  │
Internet ──[IGW]──┼──┤  Public Subnets                     │  │
                  │  │  ┌────────────────────────────────┐  │  │
                  │  │  │  EC2 (app server) + Elastic IP │  │  │
                  │  │  └────────────────────────────────┘  │  │
                  │  │                                      │  │
                  │  │  Private Subnets (no internet egress)│  │
                  │  │  ┌──────────────┐ ┌──────────────┐  │  │
                  │  │  │  RDS Postgres│ │ Redis Cache  │  │  │
                  │  │  └──────────────┘ └──────────────┘  │  │
                  │  └──────────────────────────────────────┘  │
                  │                                            │
                  │  ECR · Secrets Manager · IAM · S3/DynamoDB│
                  └────────────────────────────────────────────┘
```

## Resources Created

| Module | Resources |
|--------|-----------|
| `networking` | VPC, 2 public subnets, 2 private subnets, IGW, (optional NAT GW), route tables |
| `security_groups` | EC2 SG (22, 80, 443, 5000), RDS SG (5432 from EC2 only), Redis SG (6379 from EC2 only) |
| `iam` | EC2 IAM role + instance profile (SSM, scoped Secrets Manager read, ECR read, CloudWatch) |
| `iam_cicd` | GitHub Actions IAM user + least-privilege ECR push policy + access key in Secrets Manager |
| `ecr` | ECR repository + lifecycle policy (expire untagged after 1 day, keep last N tagged) |
| `secrets` | Secrets Manager entries: DB password, Flask SECRET_KEY, JWT_SECRET_KEY |
| `rds` | RDS PostgreSQL 14, subnet group, parameter group (slow query logging) |
| `elasticache` | ElastiCache Redis 7, subnet group, parameter group |
| `ec2` | EC2 Ubuntu 22.04, key pair, Elastic IP, user-data bootstrap script |
| `state_backend` | S3 bucket (versioned + encrypted) + DynamoDB table for remote Terraform state |

## Prerequisites

1. [Terraform ≥ 1.6](https://developer.hashicorp.com/terraform/install)
2. [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with credentials
3. An SSH key pair for EC2 access: `ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa`

## Quick Start

### 1. Configure variables

```bash
cd terraform/

# Copy the example var file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars – set app_secret_key, app_jwt_secret_key, admin_cidr
```

Or use environment variables for secrets (recommended – avoids committing secrets):

```bash
export TF_VAR_app_secret_key=$(python -c "import secrets; print(secrets.token_hex(32))")
export TF_VAR_app_jwt_secret_key=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### 2. Bootstrap the remote state backend (once per AWS account)

```bash
terraform init -backend=false
terraform apply -target=module.state_backend
```

Copy the `state_bucket_name` output, uncomment the `backend "s3"` block in
`versions.tf`, then migrate state:

```bash
terraform init   # Terraform will prompt to migrate local state to S3
```

### 3. Plan and apply

```bash
# Dev environment
terraform plan  -var-file=environments/dev/terraform.tfvars
terraform apply -var-file=environments/dev/terraform.tfvars

# Production environment
terraform plan  -var-file=environments/prod/terraform.tfvars
terraform apply -var-file=environments/prod/terraform.tfvars
```

### 4. Configure GitHub Actions secrets

After `apply` the `github_secrets_setup` output lists all secrets to configure:

```bash
terraform output github_secrets_setup
```

Set the following in **Settings → Secrets and variables → Actions**:

| Secret | Source |
|--------|--------|
| `AWS_ACCESS_KEY_ID` | `terraform output -raw cicd_access_key_id` (dev apply) |
| `AWS_SECRET_ACCESS_KEY` | `terraform output -raw cicd_secret_access_key` (dev apply) |
| `AWS_REGION` | `ap-south-1` |
| `ECR_REPOSITORY_DEV` | `terraform output -raw ecr_repository_name` (dev apply) |
| `EC2_HOST_DEV` | `terraform output -raw ec2_public_ip` (dev apply) |
| `EC2_KEY_DEV` | Contents of your SSH private key |
| `AWS_ACCESS_KEY_ID_PROD` | `terraform output -raw cicd_access_key_id` (prod apply) |
| `AWS_SECRET_ACCESS_KEY_PROD` | `terraform output -raw cicd_secret_access_key` (prod apply) |
| `AWS_REGION_PROD` | `ap-south-1` |
| `ECR_REPOSITORY_PROD` | `terraform output -raw ecr_repository_name` (prod apply) |
| `EC2_HOST_PROD` | `terraform output -raw ec2_public_ip` (prod apply) |
| `EC2_KEY_PROD` | Contents of your SSH private key |

### 5. Push your first Docker image

```bash
terraform output ecr_push_commands
```

### 6. Verify

```bash
curl $(terraform output -raw health_url)
# → {"status": "healthy", "service": "task-management-api"}
```

## Environment Differences

| Setting | Dev | Prod |
|---------|-----|------|
| EC2 instance type | `t3.small` | `t3.medium` |
| RDS instance class | `db.t3.micro` | `db.t3.small` |
| NAT Gateway | ❌ disabled (saves ~$32/month) | ✅ enabled |
| RDS Multi-AZ | ❌ | ✅ |
| RDS deletion protection | ❌ | ✅ |
| RDS final snapshot | skipped | taken |
| RDS backup retention | 7 days | 30 days |
| SSH CIDR (`admin_cidr`) | `0.0.0.0/0` | restricted to office/VPN |

## Module Reference

### `modules/iam`

EC2 instance role. Uses a **least-privilege inline Secrets Manager policy** scoped
to `${project_name}/${environment}/*` instead of the broad `SecretsManagerReadWrite`
managed policy.

### `modules/iam_cicd`

Dedicated IAM user for GitHub Actions CI/CD. Permissions:
- `ecr:GetAuthorizationToken` (account-level – required by ECR)
- ECR push actions scoped to only the project's ECR repository
- `sts:GetCallerIdentity` (used by `aws-actions/configure-aws-credentials`)

The generated access key is stored in Secrets Manager for safe retrieval and rotation.

### `modules/ecr`

ECR repository with a two-rule lifecycle policy:
1. Expire **untagged** images after **1 day** (cleans up push intermediaries)
2. Keep the **N most recent tagged** images (configurable via `ecr_max_image_count`)

### `modules/state_backend`

S3 bucket (versioned + AES-256 encrypted, public access blocked) and DynamoDB
table for Terraform state locking. Apply this module **before** enabling the S3
backend in `versions.tf`.

## Destroying Resources

```bash
terraform destroy -var-file=environments/dev/terraform.tfvars
```

> ⚠️ In production set `rds_deletion_protection = true` and
> `rds_skip_final_snapshot = false` to protect data before destroying.
