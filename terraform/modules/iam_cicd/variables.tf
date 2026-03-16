variable "project_name" { type = string }
variable "environment" { type = string }

variable "ecr_repository_arn" {
  description = "ARN of the ECR repository this CI/CD user is allowed to push to."
  type        = string
}
