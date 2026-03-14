# ==============================================================================
# Root outputs – reference these after `terraform apply`
# ==============================================================================

# ── Networking ─────────────────────────────────────────────────────────────────
output "vpc_id" {
  description = "VPC ID."
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the two public subnets."
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the two private subnets."
  value       = module.networking.private_subnet_ids
}

# ── EC2 ────────────────────────────────────────────────────────────────────────
output "ec2_public_ip" {
  description = "Elastic IP attached to the application EC2 instance."
  value       = module.ec2.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID."
  value       = module.ec2.instance_id
}

output "app_url" {
  description = "Base URL of the running Flask application."
  value       = "http://${module.ec2.public_ip}:${var.flask_port}"
}

output "health_url" {
  description = "Health-check endpoint."
  value       = "http://${module.ec2.public_ip}:${var.flask_port}/health"
}

output "ssh_command" {
  description = "SSH command to connect to the EC2 instance."
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${module.ec2.public_ip}"
}

# ── RDS ────────────────────────────────────────────────────────────────────────
output "rds_endpoint" {
  description = "RDS PostgreSQL host:port endpoint (without credentials)."
  value       = module.rds.db_endpoint
}

output "rds_db_name" {
  description = "Name of the PostgreSQL database."
  value       = var.rds_db_name
}

output "rds_username" {
  description = "Master username for the RDS instance."
  value       = var.rds_username
}

# ── ElastiCache ────────────────────────────────────────────────────────────────
output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint."
  value       = module.elasticache.redis_endpoint
}

output "redis_port" {
  description = "Redis port."
  value       = var.redis_port
}

# ── ECR ────────────────────────────────────────────────────────────────────────
output "ecr_repository_url" {
  description = "ECR repository URL (use as the base for docker push)."
  value       = module.ecr.repository_url
}

output "ecr_push_commands" {
  description = "Commands to authenticate and push a Docker image to ECR."
  value       = <<-EOT
    # Authenticate Docker with ECR:
    aws ecr get-login-password --region ${var.aws_region} | \
      docker login --username AWS --password-stdin ${module.ecr.repository_url}

    # Build and push:
    docker build -f docker/Dockerfile -t ${module.ecr.repository_url}:latest .
    docker push ${module.ecr.repository_url}:latest
  EOT
}

# ── Secrets Manager ────────────────────────────────────────────────────────────
output "db_password_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the RDS password."
  value       = module.secrets.db_password_secret_arn
}

output "app_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the Flask SECRET_KEY."
  value       = module.secrets.app_secret_arn
  sensitive   = true
}

output "jwt_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the JWT_SECRET_KEY."
  value       = module.secrets.jwt_secret_arn
  sensitive   = true
}

# ── DATABASE_URL ───────────────────────────────────────────────────────────────
output "database_url_template" {
  description = "DATABASE_URL template (replace <password> with the value from Secrets Manager)."
  value       = "postgresql://${var.rds_username}:<password>@${module.rds.db_endpoint}/${var.rds_db_name}?sslmode=require"
}
