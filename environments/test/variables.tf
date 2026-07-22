variable "aws_region" {
  type        = string
  description = "The AWS region"
  default     = "us-east-1"
  sensitive   = false
  validation {
    condition     = length(var.aws_region) > 0
    error_message = "Value must not be empty."
  }
}

variable "domain" {
  type        = string
  description = "The domain name for SES identity"
  default     = "example.com"
  sensitive   = false
  validation {
    condition     = length(var.domain) > 0
    error_message = "Value must not be empty."
  }
}

variable "project" {
  type        = string
  description = "The project name"
  default     = "heliocloud"
  sensitive   = false
  validation {
    condition     = length(var.project) > 0
    error_message = "Value must not be empty."
  }
}

variable "environment" {
  type        = string
  description = "The environment name"
  default     = "dev"
  sensitive   = false
  validation {
    condition     = length(var.environment) > 0
    error_message = "Value must not be empty."
  }
}
