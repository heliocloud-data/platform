variable "aws_region" {
  description = "The AWS region hosting the EKS cluster and Cognito resources."
  type        = string
}

variable "oauth2_proxy_host" {
  description = "Public hostname for the oauth2-proxy ingress."
  type        = string
}

variable "root_domain" {
  description = "The root domain used for public ingress endpoints."
  type        = string
}

variable "cognito_user_pool_id" {
  description = "The Cognito user pool ID used by oauth2-proxy."
  type        = string
}

variable "cognito_user_pool_domain" {
  description = "The Cognito hosted UI domain prefix or custom domain."
  type        = string
}

variable "cognito_client_id" {
  description = "The Cognito user pool client ID used by oauth2-proxy."
  type        = string
}

variable "cognito_client_secret" {
  description = "The Cognito user pool client secret used by oauth2-proxy."
  type        = string
  sensitive   = true
}

variable "oauth2_proxy_cookie_secret" {
  description = "Cookie secret for oauth2-proxy."
  type        = string
  sensitive   = true
}

variable "namespace" {
  description = "Namespace to install ingress into."
  type        = string
  default     = "ingress-nginx"
}

variable "release_name" {
  description = "Helm release name for ingress."
  type        = string
  default     = "ingress"
}

variable "chart_version" {
  description = "Version for the local ingress chart."
  type        = string
  default     = "0.1.0"
}

variable "load_balancer_ssl_certificate_arn" {
  description = "Optional ACM certificate ARN for TLS termination on the ingress load balancer."
  type        = string
  default     = null
}
