output "ec2_sg_id" {
  description = "Security group ID for the EC2 instance."
  value       = aws_security_group.ec2.id
}

output "rds_sg_id" {
  description = "Security group ID for RDS."
  value       = aws_security_group.rds.id
}

output "redis_sg_id" {
  description = "Security group ID for ElastiCache Redis."
  value       = aws_security_group.redis.id
}
