# ==============================================================================
# Task Management System – Root Terraform Module
#
# Resources provisioned (ap-south-1 by default):
#   Networking  : VPC · 2 public subnets · 2 private subnets · IGW · NAT GW
#   Compute     : EC2 (Ubuntu 22.04, Docker + Docker Compose via user-data)
#   Database    : RDS PostgreSQL 14 (private subnet)
#   Cache       : ElastiCache Redis 7 (private subnet)
#   Registry    : ECR repository for Docker images
#   Secrets     : Secrets Manager entries for DB password + app secrets
#   IAM         : EC2 instance profile (SSM, Secrets Manager, ECR)
# ==============================================================================

# ── Networking ─────────────────────────────────────────────────────────────────
module "networking" {
  source = "./modules/networking"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  enable_nat_gateway   = var.enable_nat_gateway
}

# ── Security Groups ─────────────────────────────────────────────────────────────
module "security_groups" {
  source = "./modules/security_groups"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.networking.vpc_id
  admin_cidr   = var.admin_cidr
  flask_port   = var.flask_port
  redis_port   = var.redis_port
}

# ── IAM ────────────────────────────────────────────────────────────────────────
module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
  environment  = var.environment
}

# ── ECR ────────────────────────────────────────────────────────────────────────
module "ecr" {
  source = "./modules/ecr"

  project_name         = var.project_name
  environment          = var.environment
  image_tag_mutability = var.ecr_image_tag_mutability
  max_image_count      = var.ecr_max_image_count
}

# ── Secrets Manager ────────────────────────────────────────────────────────────
module "secrets" {
  source = "./modules/secrets"

  project_name       = var.project_name
  environment        = var.environment
  app_secret_key     = var.app_secret_key
  app_jwt_secret_key = var.app_jwt_secret_key
}

# ── RDS – PostgreSQL ───────────────────────────────────────────────────────────
module "rds" {
  source = "./modules/rds"

  project_name             = var.project_name
  environment              = var.environment
  private_subnet_ids       = module.networking.private_subnet_ids
  rds_security_group_id    = module.security_groups.rds_sg_id
  engine_version           = var.rds_engine_version
  instance_class           = var.rds_instance_class
  allocated_storage_gb     = var.rds_allocated_storage_gb
  max_allocated_storage_gb = var.rds_max_allocated_storage_gb
  db_name                  = var.rds_db_name
  username                 = var.rds_username
  backup_retention_days    = var.rds_backup_retention_days
  multi_az                 = var.rds_multi_az
  deletion_protection      = var.rds_deletion_protection
  skip_final_snapshot      = var.rds_skip_final_snapshot
  db_password_secret_arn   = module.secrets.db_password_secret_arn

  depends_on = [module.secrets]
}

# ── ElastiCache – Redis ────────────────────────────────────────────────────────
module "elasticache" {
  source = "./modules/elasticache"

  project_name            = var.project_name
  environment             = var.environment
  private_subnet_ids      = module.networking.private_subnet_ids
  redis_security_group_id = module.security_groups.redis_sg_id
  node_type               = var.redis_node_type
  engine_version          = var.redis_engine_version
  num_cache_nodes         = var.redis_num_cache_nodes
  port                    = var.redis_port
}

# ── EC2 Application Server ─────────────────────────────────────────────────────
module "ec2" {
  source = "./modules/ec2"

  project_name          = var.project_name
  environment           = var.environment
  ami_id                = var.ec2_ami_id
  instance_type         = var.ec2_instance_type
  public_subnet_id      = module.networking.public_subnet_ids[0]
  ec2_security_group_id = module.security_groups.ec2_sg_id
  iam_instance_profile  = module.iam.instance_profile_name
  ssh_public_key_path   = var.ssh_public_key_path
  root_volume_size_gb   = var.ec2_root_volume_size_gb
  flask_port            = var.flask_port
  aws_region            = var.aws_region

  # Inject runtime configuration via user-data
  db_host                = module.rds.db_endpoint
  db_name                = var.rds_db_name
  db_username            = var.rds_username
  db_password_secret_arn = module.secrets.db_password_secret_arn
  redis_host             = module.elasticache.redis_endpoint
  redis_port             = var.redis_port
  ecr_repo_url           = module.ecr.repository_url
  app_secret_arn         = module.secrets.app_secret_arn
  jwt_secret_arn         = module.secrets.jwt_secret_arn

  depends_on = [module.rds, module.elasticache, module.ecr]
}
