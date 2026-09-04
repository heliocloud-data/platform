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

variable "aws_eks_public_subnet_01_cidr_block" {
  type        = string
  description = "The cidr_block for public subnet 1 of the EKS cluster"
  default = "192.168.64.0/19"
  sensitive   = false
}

variable "aws_eks_public_subnet_02_cidr_block" {
  type        = string
  description = "The cidr_block for public subnet 2 of the EKS cluster"
  default = "192.168.96.0/19"
  sensitive   = false
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

variable "daskhub_subdomain" {
  description = "The subdomain of this heliocloud instance of daskhub is being served from.  It's prepended to the root domain specified by 'root_domain' to derive the output 'daskhub_fqdn'."
  type        = string
  default     = "daskhub"
  validation {
    condition     = length(var.daskhub_subdomain) > 0
    error_message = "Value must not be empty."
  }
}

variable "portal_subdomain" {
  description = "The subdomain of this heliocloud instance of portal is being served from.  It's prepended to the root domain specified by 'root_domain' to derive the output 'portal_fqdn'."
  type        = string
  default     = "portal"
  validation {
    condition     = length(var.portal_subdomain) > 0
    error_message = "Value must not be empty."
  }
}

variable "auth_subdomain" {
  description = "The subdomain of this heliocloud instance of auth is being served from.  It's prepended to the root domain specified by 'root_domain' to derive the output 'auth_fqdn'."
  type        = string
  default     = "auth"
  validation {
    condition     = length(var.auth_subdomain) > 0
    error_message = "Value must not be empty."
  }
}

variable "cognito_subdomain" {
  description = "The subdomain of this heliocloud's AWS cognito.  It's prepended to the auth.<var.aws_region>.amazoncognito.com domain to derive the output 'cognito_fqdn'."
  type        = string
  default     = "auth"
  validation {
    condition     = length(var.cognito_subdomain) > 0
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

variable "oauth2_proxy_cookie_secret" {
  description = "Cookie secret for oauth2-proxy."
  type        = string
  default     = null
  sensitive   = true
}

variable "aws_efs_name" {
  description = "The name of the HelioCloud EFS Shared File System"
  type        = string
  default     = "heliocloud-efs-user-share"
  sensitive   = false
}

variable "aws_efs_number_of_mount_targets" {
  description = "The name of the HelioCloud EFS Shared File System"
  type        = number
  default     = 1
  sensitive   = false
}

variable "aws_efs_creation_token" {
  description = "The creation token of the HelioCloud EFS Shared File System"
  type        = string
  default     = "heliocloud-efs-user-share-token"
  sensitive   = false
}

variable "aws_efs_kms_key_arn" {
  description = "The ARN of the KMS Key used for encryption of the HelioCloud EFS Shared File System"
  type        = string
  default     = null
  sensitive   = false
}

variable "aws_efs_security_group_name" {
  description = "The name of the security group included with the HelioCloud EFS Shared File System"
  type        = string
  default     = null
  sensitive   = false
}

variable "aws_efs_security_group_description" {
  description = "The description of the security group included with the HelioCloud EFS Shared File System"
  type        = string
  default     = null
  sensitive   = false
}
