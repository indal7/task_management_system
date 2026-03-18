#!/usr/bin/env bash
# ==============================================================================
# EC2 User Data – minimal one-time bootstrap
#
# Installs Docker + AWS CLI, writes .env.prod from Secrets Manager, and
# registers a systemd service so the container restarts on reboot.
#
# All deployment steps (image pull, migrations, container start) are handled
# by the CI/CD pipeline via SSH – not here.
# ==============================================================================
set -euo pipefail

LOG_FILE="/var/log/userdata.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date)] Starting EC2 bootstrap…"

# ── System packages + AWS CLI ──────────────────────────────────────────────────
apt-get update -y
apt-get install -y --no-install-recommends ca-certificates curl gnupg jq unzip

curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp && /tmp/aws/install

# ── Docker ─────────────────────────────────────────────────────────────────────
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
bash /tmp/get-docker.sh
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

# ── App directories ────────────────────────────────────────────────────────────
APP_DIR="/home/ubuntu/taskmanager"
mkdir -p "$APP_DIR/env"

# ── Fetch secrets and write .env.prod ─────────────────────────────────────────
# Uses the EC2 IAM instance role – no long-lived credentials needed.
echo "[$(date)] Fetching secrets from Secrets Manager…"

DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id "${db_password_secret_arn}" --region "${aws_region}" \
  --query SecretString --output text | jq -r .password)

SECRET_KEY=$(aws secretsmanager get-secret-value \
  --secret-id "${app_secret_arn}" --region "${aws_region}" \
  --query SecretString --output text)

JWT_SECRET_KEY=$(aws secretsmanager get-secret-value \
  --secret-id "${jwt_secret_arn}" --region "${aws_region}" \
  --query SecretString --output text)

cat > "$APP_DIR/env/.env.prod" <<ENVEOF
FLASK_ENV=production
FLASK_HOST=0.0.0.0
FLASK_PORT=${flask_port}
FLASK_DEBUG=false

DATABASE_URL=postgresql://${db_username}:$${DB_PASSWORD}@${db_host}/${db_name}?sslmode=require
REDIS_URL=redis://${redis_host}:${redis_port}/0
CACHE_REDIS_URL=redis://${redis_host}:${redis_port}/1
CACHE_TYPE=RedisCache
CACHE_DEFAULT_TIMEOUT=300

SECRET_KEY=$${SECRET_KEY}
JWT_SECRET_KEY=$${JWT_SECRET_KEY}
JWT_ACCESS_TOKEN_EXPIRES=3600

LOG_LEVEL=INFO
LOG_TO_STDOUT=true
RATELIMIT_ENABLED=true
ENVEOF

chmod 600 "$APP_DIR/env/.env.prod"
chown -R ubuntu:ubuntu "$APP_DIR"

# ── systemd service (auto-restart on reboot) ───────────────────────────────────
# The compose file is placed at this path by the CI/CD pipeline on first deploy.
COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"

cat > /etc/systemd/system/taskmanager.service <<SERVICEEOF
[Unit]
Description=Task Management System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose -f $COMPOSE_FILE up -d --remove-orphans
ExecStop=/usr/bin/docker compose -f $COMPOSE_FILE down
User=ubuntu

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable taskmanager.service

echo "[$(date)] Bootstrap complete – EC2 ready for pipeline deployment."
