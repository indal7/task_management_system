variable "project_name" { type = string }
variable "environment" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "redis_security_group_id" { type = string }
variable "node_type" { type = string }
variable "engine_version" { type = string }
variable "num_cache_nodes" { type = number }
variable "port" { type = number }
