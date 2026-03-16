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
  # Remote State – S3 backend (recommended for teams and CI/CD pipelines).
  #
  # Step 1: Bootstrap the backend resources first (only once):
  #   terraform init -backend=false
  #   terraform apply -target=module.state_backend
  #
  # Step 2: Uncomment the block below; fill in the bucket name from the output:
  #   terraform output state_bucket_name
  #
  # Step 3: Migrate local state to S3:
  #   terraform init   (Terraform will ask to migrate existing state)
  # ---------------------------------------------------------------------------
  # backend "s3" {
  #   bucket         = "taskmanager-terraform-state-<account-id>"
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
