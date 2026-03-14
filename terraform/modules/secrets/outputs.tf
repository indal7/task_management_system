output "db_password_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the RDS password."
  value       = aws_secretsmanager_secret.db_password.arn
}

output "db_password_secret_name" {
  description = "Name of the Secrets Manager secret containing the RDS password."
  value       = aws_secretsmanager_secret.db_password.name
}

output "app_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the Flask SECRET_KEY."
  value       = aws_secretsmanager_secret.app_secret.arn
  sensitive   = true
}

output "jwt_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the JWT_SECRET_KEY."
  value       = aws_secretsmanager_secret.jwt_secret.arn
  sensitive   = true
}
