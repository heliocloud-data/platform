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

variable "aws_region" {
  type        = string
  description = "The AWS region"
  sensitive   = false
  validation {
    condition     = length(var.aws_region) > 0
    error_message = "Value must not be empty."
  }
}

variable "mng_jupyterhub_burst_compute_instance_types" {
  type        = list(string)
  description = "The set if compatible instance types for the 'mng_jupyterhub_burst_compute' node group, subsequencely downselected by available instances by region"
  default = [
    "h1.8xlarge",
    "m5.8xlarge",
    "m5a.8xlarge",
    "m5ad.8xlarge",
    "m5d.8xlarge",
    "m5dn.8xlarge",
    "m5n.8xlarge",
    "m6a.8xlarge",
    "m6i.8xlarge",
    "m6id.8xlarge",
    "m6idn.8xlarge",
    "m6in.8xlarge",
    "m7a.8xlarge",
    "m7i-flex.8xlarge",
    "m7i.8xlarge",
    "m8a.8xlarge",
    "m8i-flex.8xlarge",
    "m8i.8xlarge"
  ]
  sensitive = false
  validation {
    condition     = length(var.mng_jupyterhub_burst_compute_instance_types) > 0
    error_message = "Value must not be empty."
  }
}

variable "mng_jupyterhub_burst_compute_gpu_xlarge_instance_types" {
  type        = list(string)
  description = "The set if compatible instance types for the 'mng_jupyterhub_burst_compute' node group, subsequencely downselected by available instances by region"
  default = [
    "g4dn.xlarge",
    "g5.xlarge",
    "g6.xlarge",
    "g6e.xlarge",
    "g6f.xlarge",
  ]
  sensitive = false
  validation {
    condition     = length(var.mng_jupyterhub_burst_compute_gpu_xlarge_instance_types) > 0
    error_message = "Value must not be empty."
  }
}
