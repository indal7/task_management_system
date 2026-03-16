variable "project_name" {
  description = "Short project name used as a prefix for S3 bucket and DynamoDB table."
  type        = string
}

variable "aws_region" {
  description = "AWS region where the backend resources are created."
  type        = string
}
