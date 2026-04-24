output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.arn
}

output "user_pool_domain" {
  description = "Domain of the Cognito User Pool"
  value       = aws_cognito_user_pool_domain.domain.domain
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
