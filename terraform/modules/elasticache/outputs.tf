output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint (hostname only)."
  value       = aws_elasticache_cluster.this.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis port."
  value       = aws_elasticache_cluster.this.port
}

output "redis_url" {
  description = "Full Redis URL (redis://host:port/0)."
  value       = "redis://${aws_elasticache_cluster.this.cache_nodes[0].address}:${aws_elasticache_cluster.this.port}/0"
}
