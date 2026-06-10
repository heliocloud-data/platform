variable "worker_node_role_name" {
  type = any
}

variable "enable_addon_version_lookup" {
  type        = bool
  description = "Enable AWS lookup for addon version (disable for tests/CI)"
  default     = false
}

variable "qualifier" {
  type        = string
  description = "The instance qualifier included in all AWS derived resources, used to differentiate"
  default     = ""
  sensitive   = false
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

variable "kubernetes_version" {
  type        = string
  description = "The kubernetes version"
  sensitive   = false
  validation {
    condition     = length(var.kubernetes_version) > 0
    error_message = "Value must not be empty."
  }
}

variable "kubernetes_namespace" {
  type        = string
  description = "The namespace of the service account"
  default     = "kube-system"
  sensitive   = false
  validation {
    condition     = length(var.kubernetes_namespace) > 0
    error_message = "Value must not be empty."
  }
}

# variable "kubernetes_service_account_controller" {
#   type        = string
#   description = "The name of the service account for the csi-controller"
#   default     = "efs-csi-controller-sa"
#   sensitive   = false
#   validation {
#     condition     = length(var.kubernetes_service_account) > 0
#     error_message = "Value must not be empty."
#   }
# }

variable "kubernetes_service_account" {
  type        = string
  description = "The name of the service account for the csi-node"
  default     = "efs-csi-controller-sa"
  sensitive   = false
  validation {
    condition     = length(var.kubernetes_service_account) > 0
    error_message = "Value must not be empty."
  }
}
