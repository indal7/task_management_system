# ==============================================================================
# Global
# ==============================================================================
variable "project_name" {
  description = "Short name used as a prefix for all AWS resources."
  type        = string
  default     = "taskmanager"
}

variable "environment" {
  description = "Deployment environment (dev | staging | prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be 'dev', 'staging', or 'prod'."
  }
}

variable "aws_region" {
  description = "AWS region to deploy resources in."
  type        = string
  default     = "ap-south-1"
}

# ==============================================================================
# Networking
# ==============================================================================
variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the two public subnets (EC2 / ALB)."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the two private subnets (RDS / ElastiCache)."
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "availability_zones" {
  description = "Availability zones to use for subnets (must match region)."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "enable_nat_gateway" {
  description = "Create a NAT Gateway so private subnet resources can reach the internet."
  type        = bool
  default     = true
}

# ==============================================================================
# EC2
# ==============================================================================
variable "ec2_instance_type" {
  description = "EC2 instance type for the application server."
  type        = string
  default     = "t3.small"
}

variable "ec2_ami_id" {
  description = "AMI ID for the EC2 instance (Ubuntu 22.04 LTS in ap-south-1)."
  type        = string
  # Latest Ubuntu 22.04 LTS HVM in ap-south-1 (update when needed)
  default = "ami-0f58b397bc5c1f2e8"
}

variable "ssh_public_key_path" {
  description = "Path to the SSH *public* key to install on the EC2 instance."
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "admin_cidr" {
  description = "CIDR allowed for SSH access to the EC2 instance. Restrict in production."
  type        = string
  default     = "0.0.0.0/0"
}

variable "flask_port" {
  description = "Port the Flask / Gunicorn application listens on inside the container."
  type        = number
  default     = 5000
}

variable "ec2_root_volume_size_gb" {
  description = "Root EBS volume size in GB."
  type        = number
  default     = 20
}

# ==============================================================================
# RDS – PostgreSQL
# ==============================================================================
variable "rds_engine_version" {
  description = "PostgreSQL major.minor version."
  type        = string
  default     = "14.17"
}

variable "rds_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage_gb" {
  description = "Initial storage in GB for the RDS instance."
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage_gb" {
  description = "Maximum storage in GB for autoscaling (0 = disabled)."
  type        = number
  default     = 100
}

variable "rds_db_name" {
  description = "Name of the PostgreSQL database to create."
  type        = string
  default     = "taskmanager"
}

variable "rds_username" {
  description = "Master username for the RDS instance."
  type        = string
  default     = "taskmanager_user"
}

variable "rds_backup_retention_days" {
  description = "Number of days to retain automated backups (0 = disabled)."
  type        = number
  default     = 7
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ standby for high availability."
  type        = bool
  default     = false
}

variable "rds_deletion_protection" {
  description = "Protect the RDS instance from accidental deletion."
  type        = bool
  default     = false
}

variable "rds_skip_final_snapshot" {
  description = "Skip final DB snapshot on destroy (set false for production)."
  type        = bool
  default     = true
}

# ==============================================================================
# ElastiCache – Redis
# ==============================================================================
variable "redis_node_type" {
  description = "ElastiCache node type."
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_engine_version" {
  description = "Redis engine version."
  type        = string
  default     = "7.1"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes (1 = no replication)."
  type        = number
  default     = 1
}

variable "redis_port" {
  description = "Redis port."
  type        = number
  default     = 6379
}

# ==============================================================================
# ECR
# ==============================================================================
variable "ecr_image_tag_mutability" {
  description = "Tag mutability for the ECR repository (MUTABLE | IMMUTABLE)."
  type        = string
  default     = "MUTABLE"
}

variable "ecr_max_image_count" {
  description = "Maximum number of images to retain in ECR (lifecycle policy)."
  type        = number
  default     = 10
}

# ==============================================================================
# Secrets Manager
# ==============================================================================
variable "app_secret_key" {
  description = "Flask SECRET_KEY – store in a tfvars file that is NOT committed."
  type        = string
  sensitive   = true
  default     = ""
}

variable "app_jwt_secret_key" {
  description = "Flask JWT_SECRET_KEY – store in a tfvars file that is NOT committed."
  type        = string
  sensitive   = true
  default     = ""
}
