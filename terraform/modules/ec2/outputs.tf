output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.this.id
}

output "public_ip" {
  description = "Elastic IP address of the application server."
  value       = aws_eip.this.public_ip
}

output "private_ip" {
  description = "Private IP of the EC2 instance."
  value       = aws_instance.this.private_ip
}
