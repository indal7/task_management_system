# ==============================================================================
# Secrets Manager – application secrets
# ==============================================================================

resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Separate random passwords for Flask secrets – never reuse the DB password.
resource "random_password" "app_secret" {
  length  = 64
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

# ── RDS master password ────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.project_name}/${var.environment}/db-password"
  description             = "RDS master password for the Task Management System"
  recovery_window_in_days = 0 # allow immediate deletion (set 7+ in production)

  tags = {
    Name = "${var.project_name}-${var.environment}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    password = random_password.db_password.result
  })
}

# ── Flask SECRET_KEY ───────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "app_secret" {
  name                    = "${var.project_name}/${var.environment}/secret-key"
  description             = "Flask SECRET_KEY for the Task Management System"
  recovery_window_in_days = 0

  tags = {
    Name = "${var.project_name}-${var.environment}-secret-key"
  }
}

resource "aws_secretsmanager_secret_version" "app_secret" {
  secret_id = aws_secretsmanager_secret.app_secret.id
  # Use the caller-supplied key when provided; otherwise fall back to a
  # separately-generated random value (never the DB password).
  secret_string = var.app_secret_key != "" ? var.app_secret_key : random_password.app_secret.result
}

# ── JWT SECRET_KEY ─────────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.project_name}/${var.environment}/jwt-secret-key"
  description             = "Flask JWT_SECRET_KEY for the Task Management System"
  recovery_window_in_days = 0

  tags = {
    Name = "${var.project_name}-${var.environment}-jwt-secret-key"
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id = aws_secretsmanager_secret.jwt_secret.id
  # Use the caller-supplied key when provided; otherwise fall back to a
  # separately-generated random value (never the DB password).
  secret_string = var.app_jwt_secret_key != "" ? var.app_jwt_secret_key : random_password.jwt_secret.result
}

