variable "worker_node_role_name" {
  type = any
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

variable "kubernetes_service_account" {
  type        = string
  description = "The namespace of the service account"
  default     = "ebs-csi-controller-sa"
  sensitive   = false
  validation {
    condition     = length(var.kubernetes_service_account) > 0
    error_message = "Value must not be empty."
  }
}
