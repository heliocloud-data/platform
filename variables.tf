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

variable "aws_eks_az1" {
  type        = string
  description = "The availability (1) used by the EKS cluster"
  default     = "us-east-1a"
  sensitive   = false
  validation {
    condition     = length(var.aws_eks_az1) > 0
    error_message = "Value must not be empty and must not be equal to 'var.aws_eks_az2'."
  }
}

variable "aws_eks_az2" {
  type        = string
  description = "The availability (1) used by the EKS cluster"
  default     = "us-east-1a"
  sensitive   = false
  validation {
    condition = (
      length(var.aws_eks_az2) > 0 &&
      var.aws_eks_az2 != var.aws_eks_az1
    )

    error_message = "Value must not be empty and must not be equal to 'var.aws_eks_az1'."
  }
}

variable "cluster_name" {
  type        = string
  description = "The name of the cluster"
  default     = "eks-default-helio"
  sensitive   = false
  validation {
    condition     = length(var.cluster_name) > 0
    error_message = "Value must not be empty."
  }
}

variable "kubernetes_version" {
  type        = string
  description = "The kubernetes version"
  default     = "1.21"
  sensitive   = false
  validation {
    condition     = length(var.kubernetes_version) > 0
    error_message = "Value must not be empty."
  }
}
