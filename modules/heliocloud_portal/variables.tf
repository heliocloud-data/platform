

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
