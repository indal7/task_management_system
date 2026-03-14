terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # ---------------------------------------------------------------------------
  # Remote State – S3 backend.
  # Uncomment and fill in bucket / key when you have an S3 bucket for state.
  # ---------------------------------------------------------------------------
  # backend "s3" {
  #   bucket         = "taskmanager-terraform-state"
  #   key            = "taskmanager/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "taskmanager-terraform-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
