output "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state. Use in the backend 's3' block."
  value       = aws_s3_bucket.state.bucket
}

output "state_bucket_arn" {
  description = "ARN of the S3 state bucket."
  value       = aws_s3_bucket.state.arn
}

output "lock_table_name" {
  description = "Name of the DynamoDB lock table. Use as 'dynamodb_table' in the backend block."
  value       = aws_dynamodb_table.state_lock.name
}

output "backend_config" {
  description = "Copy-paste backend block for versions.tf (replace <bucket> with state_bucket_name output)."
  value       = <<-EOT
    backend "s3" {
      bucket         = "${aws_s3_bucket.state.bucket}"
      key            = "taskmanager/terraform.tfstate"
      region         = "${var.aws_region}"
      dynamodb_table = "${aws_dynamodb_table.state_lock.name}"
      encrypt        = true
    }
  EOT
}
