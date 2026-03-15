# ==============================================================================
# Dev environment – Terraform variable overrides
# Apply with: terraform apply -var-file=environments/dev/terraform.tfvars
# ==============================================================================

project_name = "taskmanager"
environment  = "dev"
aws_region   = "ap-south-1"

# ── Networking ─────────────────────────────────────────────────────────────────
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
availability_zones   = ["ap-south-1a", "ap-south-1b"]
enable_nat_gateway   = true

# ── EC2 ────────────────────────────────────────────────────────────────────────
ec2_ami_id          = "ami-0f58b397bc5c1f2e8"   # Ubuntu 22.04 LTS (ap-south-1)
ec2_instance_type   = "t3.small"
ssh_public_key_path = "~/.ssh/id_rsa.pub"
admin_cidr          = "0.0.0.0/0"               # Open for dev convenience
flask_port              = 5000
ec2_root_volume_size_gb = 20

# ── RDS – PostgreSQL ───────────────────────────────────────────────────────────
rds_engine_version           = "14.17"
rds_instance_class           = "db.t3.micro"     # Minimal, cost-optimised
rds_allocated_storage_gb     = 20
rds_max_allocated_storage_gb = 100
rds_db_name                  = "taskmanager"
rds_username                 = "taskmanager_user"
rds_backup_retention_days    = 7
rds_multi_az                 = false             # Single-AZ is fine for dev
rds_deletion_protection      = false             # Allow easy teardown
rds_skip_final_snapshot      = true              # No need to preserve dev data

# ── ElastiCache – Redis ────────────────────────────────────────────────────────
redis_node_type       = "cache.t3.micro"
redis_engine_version  = "7.1"
redis_num_cache_nodes = 1
redis_port            = 6379

# ── ECR ────────────────────────────────────────────────────────────────────────
ecr_image_tag_mutability = "MUTABLE"
ecr_max_image_count      = 10

# ── Secrets (SENSITIVE – never commit real values) ─────────────────────────────
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
app_secret_key     = "REPLACE_WITH_A_STRONG_RANDOM_SECRET"
app_jwt_secret_key = "REPLACE_WITH_A_DIFFERENT_STRONG_SECRET"
