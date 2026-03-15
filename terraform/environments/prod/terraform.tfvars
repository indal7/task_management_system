# ==============================================================================
# Prod environment – Terraform variable overrides
# Apply with: terraform apply -var-file=environments/prod/terraform.tfvars
# ==============================================================================

project_name = "taskmanager"
environment  = "prod"
aws_region   = "ap-south-1"

# ── Networking ─────────────────────────────────────────────────────────────────
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
availability_zones   = ["ap-south-1a", "ap-south-1b"]
enable_nat_gateway   = true

# ── EC2 ────────────────────────────────────────────────────────────────────────
ec2_ami_id          = "ami-0f58b397bc5c1f2e8"   # Ubuntu 22.04 LTS (ap-south-1)
ec2_instance_type   = "t3.medium"               # More headroom for production traffic
ssh_public_key_path = "~/.ssh/id_rsa.pub"
admin_cidr          = "203.0.113.0/24"          # Restrict SSH to your office/VPN CIDR
flask_port              = 5000
ec2_root_volume_size_gb = 20

# ── RDS – PostgreSQL ───────────────────────────────────────────────────────────
rds_engine_version           = "14.17"
rds_instance_class           = "db.t3.small"    # Production-grade instance
rds_allocated_storage_gb     = 20
rds_max_allocated_storage_gb = 100
rds_db_name                  = "taskmanager"
rds_username                 = "taskmanager_user"
rds_backup_retention_days    = 30               # Long retention for compliance
rds_multi_az                 = true             # High availability standby
rds_deletion_protection      = true             # Prevent accidental deletion
rds_skip_final_snapshot      = false            # Always preserve a final snapshot

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
