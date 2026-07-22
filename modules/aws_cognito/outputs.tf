output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.id
}

output "user_pool_name" {
  description = "Name of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.name
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.arn
}

output "user_pool_domain" {
  description = "Domain of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.domain
}

output "user_pool_domain_prefix" {
  description = "Domain prefix of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.domain
}

output "user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.client.id
}

output "user_pool_client_secret" {
  description = "Secret of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.client.client_secret
  sensitive   = true
}

output "user_pool_client_name" {
  description = "Name of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.client.name
}

output "user_pool_client_callback_urls" {
  description = "Callback URLs of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.client.callback_urls
}

output "user_pool_client_logout_urls" {
  description = "Logout URLs of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.client.logout_urls
}
