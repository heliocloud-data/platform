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

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "root_domain" {
  description = "The root domain this heliocloud is being served from.  Is used for constructing URLs to the various services of the HelioCloud Platform.  For example 'heliocloud.org'"
  type        = string
  validation {
    condition     = length(var.root_domain) > 0
    error_message = "Value must not be empty."
  }
}

variable "cognito_callback_urls" {
  description = "Allowed callback URLs for the Cognito user pool client"
  type        = list(string)
  default     = ["http://localhost:8000/oauth2/callback"] # These need to be updated with actual urls when they are available.
}

variable "cognito_logout_urls" {
  description = "Allowed logout URLs for the Cognito user pool client"
  type        = list(string)
  default     = ["http://localhost:8000"] # These need to be updated with actual urls when they are available.
}
