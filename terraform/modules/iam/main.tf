# ==============================================================================
# IAM – EC2 instance role and instance profile
# ==============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name               = "${var.project_name}-${var.environment}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-role"
  }
}

# ── Managed Policy Attachments ─────────────────────────────────────────────────

# SSM Session Manager – allows SSH-free shell access via AWS Console / CLI
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# ECR – pull Docker images (read-only; push is handled by CI/CD IAM user)
resource "aws_iam_role_policy_attachment" "ecr" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# CloudWatch – ship logs and metrics
resource "aws_iam_role_policy_attachment" "cloudwatch" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# ── Least-privilege Secrets Manager inline policy ──────────────────────────────
# Replaces the overly-broad SecretsManagerReadWrite managed policy.
# Allows the EC2 instance to read only secrets owned by this project/environment.
data "aws_iam_policy_document" "secrets_read" {
  statement {
    sid    = "GetProjectSecrets"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/${var.environment}/*",
    ]
  }
}

resource "aws_iam_role_policy" "secrets_read" {
  name   = "${var.project_name}-${var.environment}-secrets-read"
  role   = aws_iam_role.ec2.name
  policy = data.aws_iam_policy_document.secrets_read.json
}

# ── Instance Profile ───────────────────────────────────────────────────────────
resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2.name
}
