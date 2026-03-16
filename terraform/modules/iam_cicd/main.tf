# ==============================================================================
# IAM – Dedicated GitHub Actions CI/CD user
#
# Provides a least-privilege IAM user for the GitHub Actions pipelines to:
#   • Authenticate with Amazon ECR (GetAuthorizationToken)
#   • Push Docker images to the project ECR repository
#   • Verify its own identity (sts:GetCallerIdentity — used by aws-actions)
#
# The generated access key is stored in Secrets Manager so it can be retrieved
# and rotated without touching Terraform state. The key ID and secret are also
# available as Terraform outputs for initial population of GitHub Secrets.
# ==============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ── IAM User ───────────────────────────────────────────────────────────────────
resource "aws_iam_user" "cicd" {
  name = "${var.project_name}-${var.environment}-cicd"
  path = "/cicd/"

  tags = {
    Name    = "${var.project_name}-${var.environment}-cicd"
    Purpose = "GitHub Actions CI/CD pipeline"
  }
}

# ── Least-privilege policy ─────────────────────────────────────────────────────
data "aws_iam_policy_document" "cicd" {
  # Allow ECR authentication (account-level, no resource restriction possible)
  statement {
    sid    = "ECRAuth"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
    ]
    resources = ["*"]
  }

  # Allow pushing images to only THIS project's ECR repository
  statement {
    sid    = "ECRPush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
      "ecr:BatchGetImage",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
    ]
    resources = [var.ecr_repository_arn]
  }

  # Allow the pipeline to verify its own identity (used by aws-actions/configure-aws-credentials)
  statement {
    sid    = "STSIdentity"
    effect = "Allow"
    actions = [
      "sts:GetCallerIdentity",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "cicd" {
  name        = "${var.project_name}-${var.environment}-cicd-policy"
  description = "Least-privilege policy for GitHub Actions CI/CD pipeline (${var.environment})"
  policy      = data.aws_iam_policy_document.cicd.json

  tags = {
    Name = "${var.project_name}-${var.environment}-cicd-policy"
  }
}

resource "aws_iam_user_policy_attachment" "cicd" {
  user       = aws_iam_user.cicd.name
  policy_arn = aws_iam_policy.cicd.arn
}

# ── Access Key ─────────────────────────────────────────────────────────────────
resource "aws_iam_access_key" "cicd" {
  user = aws_iam_user.cicd.name
}

# ── Store credentials in Secrets Manager ──────────────────────────────────────
# Allows the key to be retrieved securely and rotated independently of Terraform.
resource "aws_secretsmanager_secret" "cicd_credentials" {
  name                    = "${var.project_name}/${var.environment}/cicd-credentials"
  description             = "GitHub Actions IAM access key for ${var.project_name} ${var.environment} CI/CD"
  recovery_window_in_days = 0

  tags = {
    Name = "${var.project_name}-${var.environment}-cicd-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "cicd_credentials" {
  secret_id = aws_secretsmanager_secret.cicd_credentials.id
  secret_string = jsonencode({
    aws_access_key_id     = aws_iam_access_key.cicd.id
    aws_secret_access_key = aws_iam_access_key.cicd.secret
  })
}
