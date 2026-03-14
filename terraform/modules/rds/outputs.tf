output "db_endpoint" {
  description = "RDS host:port endpoint."
  value       = aws_db_instance.this.endpoint
}

output "db_host" {
  description = "RDS hostname only (without port)."
  value       = aws_db_instance.this.address
}

output "db_port" {
  description = "RDS port."
  value       = aws_db_instance.this.port
}

output "db_instance_id" {
  description = "RDS instance identifier."
  value       = aws_db_instance.this.identifier
}

output "db_arn" {
  description = "RDS instance ARN."
  value       = aws_db_instance.this.arn
}
