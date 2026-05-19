output "oauth2_proxy_host" {
  description = "Public hostname for the oauth2-proxy ingress."
  value       = var.oauth2_proxy_host
}

output "oauth2_proxy_callback_url" {
  description = "OAuth2 callback URL for Cognito app client configuration."
  value       = "https://${var.oauth2_proxy_host}/oauth2/callback"
}
