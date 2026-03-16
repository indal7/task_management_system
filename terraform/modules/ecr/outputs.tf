output "repository_url" {
  description = "ECR repository URL."
  value       = aws_ecr_repository.app.repository_url
}

output "repository_name" {
  description = "ECR repository name (e.g. taskmanager-dev). Use as ECR_REPOSITORY_DEV/PROD GitHub Secret."
  value       = aws_ecr_repository.app.name
}

output "repository_arn" {
  description = "ECR repository ARN."
  value       = aws_ecr_repository.app.arn
}
