output "root_domain" {
  value = var.root_domain
}

output "daskhub_fqdn" {
  value = aws_route53_record.HelioCloud_Daskhub_Record.name
}

output "portal_fqdn" {
  value = aws_route53_record.HelioCloud_Portal_Record.name
}

output "auth_fqdn" {
  value = aws_route53_record.HelioCloud_Auth_Record.name
}

output "cognito_fqdn" {
  value = "${var.cognito_subdomain}.auth.${var.aws_region}.amazoncognito.com"
}

output "root_domain_cert_arn" {
  value = aws_acm_certificate.HelioCloud_Certificate_Wildcard.arn
}

output "oauth2_proxy_callback_url" {
  description = "OAuth2 callback URL for the ingress oauth2-proxy."
  value       = module.heliocloud_eks_ingress.oauth2_proxy_callback_url
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

output "portal_subnet_id" {
  description = "ID of the subnet containing the ec2 instances spawned by the HelioCloud User Portal."
  value       = module.heliocloud_portal.portal_subnet_id
}

output "portal_identity_pool_id" {
  description = ""
  value       = module.heliocloud_portal.portal_identity_pool_id
}

output "portal_ec2_instance_profile_arn" {
  description = ""
  value       = module.heliocloud_portal.portal_ec2_instance_profile_arn
}

output "portal_security_group_id" {
  description = ""
  value       = module.heliocloud_portal.portal_security_group_id
}

output "portal_user_role_arn" {
  description = ""
  value       = module.heliocloud_portal.portal_user_role_arn
}
