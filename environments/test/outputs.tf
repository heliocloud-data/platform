output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = module.aws_cognito.user_pool_id
}

output "user_pool_name" {
  description = "Name of the Cognito User Pool"
  value       = module.aws_cognito.user_pool_name
}

output "user_pool_domain_prefix" {
  description = "Domain prefix of the Cognito User Pool"
  value       = module.aws_cognito.user_pool_domain_prefix
}

# output "user_pool_domain_name" {
#   description = "Domain name of the Cognito User Pool"
#   value       = module.aws_cognito.domain_name
# }