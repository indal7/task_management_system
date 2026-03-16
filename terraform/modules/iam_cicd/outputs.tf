output "cicd_user_arn" {
  description = "ARN of the GitHub Actions IAM user."
  value       = aws_iam_user.cicd.arn
}

output "cicd_user_name" {
  description = "Name of the GitHub Actions IAM user."
  value       = aws_iam_user.cicd.name
}

output "cicd_access_key_id" {
  description = "AWS Access Key ID for the GitHub Actions IAM user. Set as AWS_ACCESS_KEY_ID GitHub Secret."
  value       = aws_iam_access_key.cicd.id
  sensitive   = true
}

output "cicd_secret_access_key" {
  description = "AWS Secret Access Key for the GitHub Actions IAM user. Set as AWS_SECRET_ACCESS_KEY GitHub Secret."
  value       = aws_iam_access_key.cicd.secret
  sensitive   = true
}

output "cicd_credentials_secret_arn" {
  description = "ARN of the Secrets Manager secret storing the CI/CD access key."
  value       = aws_secretsmanager_secret.cicd_credentials.arn
}
