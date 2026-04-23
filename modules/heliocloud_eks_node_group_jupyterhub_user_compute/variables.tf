variable "subnet_ids" {
  type        = list(string)
  description = "The subnets"
  default     = []
  sensitive   = false
}

variable "node_role_arn" {
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
