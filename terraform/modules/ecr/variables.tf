variable "project_name" { type = string }
variable "environment" { type = string }
variable "image_tag_mutability" { type = string }
variable "max_image_count" { type = number }

variable "force_delete" {
  description = "Force delete the ECR repository even if it contains images"
  type        = bool
  default     = false
}