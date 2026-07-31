variable "create_ses_identity" {
  description = "Whether to create SES domain identity"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for SES identity"
  type        = string
  default     = ""
  validation {
    condition     = !var.create_ses_identity || length(var.domain_name) > 0
    error_message = "domain_name must not be empty when create_ses_identity is true."
  }
}

variable "user_pool_name" {
  description = "Name of the Cognito User Pool"
  type        = string
  validation {
    condition     = length(var.user_pool_name) > 0
    error_message = "user_pool_name must not be empty."
  }
}

variable "domain_prefix" {
  description = "Domain prefix for the Cognito User Pool domain"
  type        = string
  validation {
    condition     = length(var.domain_prefix) > 0
    error_message = "domain_prefix must not be empty."
  }
}

variable "certificate_arn" {
  description = "ARN of the certificate for the custom domain (optional)"
  type        = string
  default     = null
  validation {
    condition     = var.certificate_arn == null || length(var.certificate_arn) > 0
    error_message = "certificate_arn must not be an empty string when provided."
  }
}

variable "user_pool_client_name" {
  description = "Name of the Cognito User Pool Client"
  type        = string
  validation {
    condition     = length(var.user_pool_client_name) > 0
    error_message = "user_pool_client_name must not be empty."
  }
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
  validation {
    condition     = var.access_token_validity_hours > 0
    error_message = "access_token_validity_hours must be greater than 0."
  }
}

variable "id_token_validity_hours" {
  description = "Validity period for ID tokens in hours"
  type        = number
  default     = 1
  validation {
    condition     = var.id_token_validity_hours > 0
    error_message = "id_token_validity_hours must be greater than 0."
  }
}

variable "refresh_token_validity_days" {
  description = "Validity period for refresh tokens in days"
  type        = number
  default     = 30
  validation {
    condition     = var.refresh_token_validity_days > 0
    error_message = "refresh_token_validity_days must be greater than 0."
  }
}

variable "logout_urls" {
  description = "List of logout URLs for the client"
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for url in var.logout_urls : length(url) > 0])
    error_message = "logout_urls must not contain empty strings."
  }
}

variable "callback_urls" {
  description = "List of callback URLs for the client"
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for url in var.callback_urls : length(url) > 0])
    error_message = "callback_urls must not contain empty strings."
  }
}

variable "email_configuration" {
  description = "Email configuration for the User Pool"
  type = object({
    from_email = string
    source_arn = string
  })
  default = null
  validation {
    condition = (
      var.email_configuration == null ||
      (
        length(var.email_configuration.from_email) > 0 &&
        length(var.email_configuration.source_arn) > 0
      )
    )
    error_message = "email_configuration.from_email and email_configuration.source_arn must not be empty when email_configuration is provided."
  }
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
