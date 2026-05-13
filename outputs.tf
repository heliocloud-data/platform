output "root_domain" {
  value = var.root_domain
}

output "daskhub_fqdn" {
  value = aws_route53_record.HelioCloud_Daskhub_Record.name
}

output "auth_fqdn" {
  value = aws_route53_record.HelioCloud_Auth_Record.name
}

output "cognito_fqdn" {
  value = "${var.cognito_subdomain}.auth.${var.aws_region}.amazoncognito.com"
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.heliocloud_auth.user_pool_id
}

output "cognito_user_pool_domain" {
  description = "Cognito User Pool Domain"
  value       = module.heliocloud_auth.user_pool_domain
}

output "cognito_client_id" {
  description = "Cognito User Pool Client ID"
  value       = module.heliocloud_auth.user_pool_client_id
}

output "cognito_client_secret" {
  description = "Cognito User Pool Client Secret"
  value       = module.heliocloud_auth.user_pool_client_secret
  sensitive   = true
}

output "aws_region" {
  value = var.aws_region
}

output "eks_cluster_name" {
  value = var.cluster_name
}

output "efs_file_system_id" {
  value = module.efs.id
}
