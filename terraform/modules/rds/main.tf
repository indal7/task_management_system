# ==============================================================================
# RDS – PostgreSQL 14 in private subnet
# ==============================================================================

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = var.db_password_secret_arn
}

locals {
  db_password = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"]
}

# ── Subnet Group ──────────────────────────────────────────────────────────────
resource "aws_db_subnet_group" "this" {
  name        = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids  = var.private_subnet_ids
  description = "Subnet group for ${var.project_name} ${var.environment} RDS"

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

# ── Parameter Group ────────────────────────────────────────────────────────────
resource "aws_db_parameter_group" "this" {
  name        = "${var.project_name}-${var.environment}-pg14"
  family      = "postgres14"
  description = "Custom parameter group for ${var.project_name} ${var.environment}"

  # Log slow queries (threshold: 1 second)
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  # Enable pg_stat_statements for query analysis
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-pg14"
  }
}

# ── RDS Instance ───────────────────────────────────────────────────────────────
resource "aws_db_instance" "this" {
  identifier = "${var.project_name}-${var.environment}-postgres"

  # Engine
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  # Storage
  allocated_storage     = var.allocated_storage_gb
  max_allocated_storage = var.max_allocated_storage_gb
  storage_type          = "gp3"
  storage_encrypted     = true

  # Database
  db_name  = var.db_name
  username = var.username
  password = local.db_password

  # Network
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [var.rds_security_group_id]
  publicly_accessible    = false

  # Configuration
  parameter_group_name = aws_db_parameter_group.this.name
  multi_az             = var.multi_az

  # Backup
  backup_retention_period = var.backup_retention_days
  backup_window           = "02:00-03:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Lifecycle
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project_name}-${var.environment}-final-snapshot"

  # Performance Insights (disabled on db.t3.micro to avoid extra cost)
  performance_insights_enabled = var.instance_class != "db.t3.micro"

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres"
  }
}
