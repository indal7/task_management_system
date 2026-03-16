# ==============================================================================
# EC2 – Ubuntu 22.04 application server
# ==============================================================================

# ── Key Pair ───────────────────────────────────────────────────────────────────
resource "aws_key_pair" "this" {
  key_name   = "${var.project_name}-${var.environment}-keypair"
  public_key = file(var.ssh_public_key_path)

  tags = {
    Name = "${var.project_name}-${var.environment}-keypair"
  }
}

# ── User Data – bootstraps Docker, Docker Compose, and the Flask app ────────────
locals {
  user_data = templatefile("${path.module}/userdata.sh.tpl", {
    aws_region             = var.aws_region
    project_name           = var.project_name
    environment            = var.environment
    flask_port             = var.flask_port
    ecr_repo_url           = var.ecr_repo_url
    db_host                = var.db_host
    db_name                = var.db_name
    db_username            = var.db_username
    db_password_secret_arn = var.db_password_secret_arn
    redis_host             = var.redis_host
    redis_port             = var.redis_port
    app_secret_arn         = var.app_secret_arn
    jwt_secret_arn         = var.jwt_secret_arn
  })
}

# ── EC2 Instance ───────────────────────────────────────────────────────────────
resource "aws_instance" "this" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_id
  vpc_security_group_ids = [var.ec2_security_group_id]
  iam_instance_profile   = var.iam_instance_profile
  key_name               = aws_key_pair.this.key_name
  user_data              = local.user_data

  # Enable detailed monitoring
  monitoring = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gb
    delete_on_termination = true
    encrypted             = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-app-server"
    Role = "application"
  }

  lifecycle {
    # Prevent accidental recreation when AMI is updated; replace manually
    ignore_changes = [ami, user_data]
  }
}

# ── Elastic IP ─────────────────────────────────────────────────────────────────
resource "aws_eip" "this" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-app-eip"
  }
}

resource "aws_eip_association" "this" {
  instance_id   = aws_instance.this.id
  allocation_id = aws_eip.this.id
}


