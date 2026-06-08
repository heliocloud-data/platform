

variable "aws_az1" {
  description = ""
  type        = string
}

variable "aws_az2" {
  description = ""
  type        = string
}

variable "identity_provider_client_id" {
  description = ""
  type        = string
}


variable "identity_provider_name" {
  description = ""
  type        = string
}

variable "identity_provider_server_side_token_check" {
  description = ""
  type        = bool
  default     = false
}

variable "cluster_name" {
  type        = string
  description = "The name of the cluster"
  sensitive   = false
  validation {
    condition     = length(var.cluster_name) > 0
    error_message = "Value must not be empty."
  }
}

variable "kubernetes_namespace" {
  type        = string
  description = "The namespace of the service account"
  default     = "portal"
  sensitive   = false
  validation {
    condition     = length(var.kubernetes_namespace) > 0
    error_message = "Value must not be empty."
  }
}

variable "kubernetes_service_account" {
  type        = string
  description = "The namespace of the service account"
  default     = "portal-sa"
  sensitive   = false
  validation {
    condition     = length(var.kubernetes_service_account) > 0
    error_message = "Value must not be empty."
  }
}
