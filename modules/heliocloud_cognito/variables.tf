variable "create_ses_identity" {
  description = "Whether to create SES domain identity"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for SES identity"
  type        = string
  default     = ""
}

variable "user_pool_name" {
  description = "Name of the Cognito User Pool"
  type        = string
}

variable "domain_prefix" {
  description = "Domain prefix for the Cognito User Pool domain"
  type        = string
}

variable "certificate_arn" {
  description = "ARN of the certificate for the custom domain (optional)"
  type        = string
  default     = null
}

variable "user_pool_client_name" {
  description = "Name of the Cognito User Pool Client"
  type        = string
}

variable "deletion_protection" {
  description = "Whether to enable deletion protection for the User Pool"
  type        = bool
  default     = true
}

variable "access_token_validity_hours" {
  description = "Validity period for access tokens in hours"
  type        = number
  default     = 1
}

variable "id_token_validity_hours" {
  description = "Validity period for ID tokens in hours"
  type        = number
  default     = 1
}

variable "refresh_token_validity_days" {
  description = "Validity period for refresh tokens in days"
  type        = number
  default     = 30
}

variable "logout_urls" {
  description = "List of logout URLs for the client"
  type        = list(string)
  default     = []
}

variable "callback_urls" {
  description = "List of callback URLs for the client"
  type        = list(string)
  default     = []
}

variable "email_configuration" {
  description = "Email configuration for the User Pool"
  type = object({
    from_email = string
    source_arn = string
  })
  default = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
