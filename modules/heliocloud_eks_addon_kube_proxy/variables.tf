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
