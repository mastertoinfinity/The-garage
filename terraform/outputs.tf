output "server_public_ip" {
  description = "Public Elastic IP address of The Garage web application server"
  value       = aws_eip.app_eip.public_ip
}

output "server_public_dns" {
  description = "Public DNS hostname of the server"
  value       = aws_eip.app_eip.public_dns
}

output "ssh_command" {
  description = "Direct SSH command to connect to the deployed instance"
  value       = "ssh -i ${var.ssh_public_key_path} ubuntu@${aws_eip.app_eip.public_ip}"
}

output "application_url" {
  description = "Live HTTP URL for the automotive web application"
  value       = "http://${aws_eip.app_eip.public_ip}"
}
