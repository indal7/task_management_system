# ==============================================================================
# Remote State Backend – S3 bucket + DynamoDB lock table
#
# This module is intentionally separate from the main infrastructure and should
# be applied ONCE before any other Terraform configuration.
#
# Usage:
#   cd terraform/
#   terraform init -backend=false
#   terraform apply -target=module.state_backend
#
# After applying, uncomment the `backend "s3"` block in versions.tf and run:
#   terraform init   (migrates local state to S3)
# ==============================================================================

data "aws_caller_identity" "current" {}

# ── S3 State Bucket ────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "state" {
  # Bucket name must be globally unique; include the account ID for uniqueness.
  bucket = "${var.project_name}-terraform-state-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name    = "${var.project_name}-terraform-state"
    Purpose = "Terraform remote state"
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── DynamoDB Lock Table ────────────────────────────────────────────────────────
resource "aws_dynamodb_table" "state_lock" {
  name         = "${var.project_name}-terraform-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name    = "${var.project_name}-terraform-lock"
    Purpose = "Terraform state locking"
  }
}
