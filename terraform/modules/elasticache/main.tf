# ==============================================================================
# ElastiCache – Redis 7 cluster in private subnet
# ==============================================================================

resource "aws_elasticache_subnet_group" "this" {
  name        = "${var.project_name}-${var.environment}-redis-subnet-group"
  subnet_ids  = var.private_subnet_ids
  description = "Subnet group for ${var.project_name} ${var.environment} Redis"

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-subnet-group"
  }
}

resource "aws_elasticache_parameter_group" "this" {
  name        = "${var.project_name}-${var.environment}-redis7"
  family      = "redis7"
  description = "Custom parameter group for ${var.project_name} ${var.environment} Redis"

  # Enable keyspace notifications for cache eviction events (used by Flask-Caching)
  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }
}

resource "aws_elasticache_cluster" "this" {
  cluster_id           = "${var.project_name}-${var.environment}-redis"
  engine               = "redis"
  engine_version       = var.engine_version
  node_type            = var.node_type
  num_cache_nodes      = var.num_cache_nodes
  parameter_group_name = aws_elasticache_parameter_group.this.name
  port                 = var.port
  subnet_group_name    = aws_elasticache_subnet_group.this.name
  security_group_ids   = [var.redis_security_group_id]

  # Enable automatic minor version upgrades
  auto_minor_version_upgrade = true

  # Maintenance window (UTC)
  maintenance_window = "sun:05:00-sun:06:00"

  # Snapshot retention (0 = disabled)
  snapshot_retention_limit = 1
  snapshot_window          = "03:00-04:00"

  tags = {
    Name = "${var.project_name}-${var.environment}-redis"
  }
}
