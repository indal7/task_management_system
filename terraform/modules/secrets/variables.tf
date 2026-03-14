variable "project_name" { type = string }
variable "environment" { type = string }

variable "app_secret_key" {
  type      = string
  sensitive = true
}

variable "app_jwt_secret_key" {
  type      = string
  sensitive = true
}
