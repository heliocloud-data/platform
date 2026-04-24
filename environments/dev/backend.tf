# This backend configuration file can only hardcoded values. Variables are not allowed in the backend configuration.
# Update this configuration file with the appropriate values for your S3 bucket, DynamoDB table, and AWS region before running tofu commands.

terraform {
  backend "s3" {
    bucket         = "heliocloud-tofu-state-bucket-hsdcloud"
    key            = "hsdcloud-dev/terraform.tfstate"
    region         = "us-east-2"
    encrypt        = true
    dynamodb_table = "heliocloud-tofu-state-lock-hsdcloud"

    # Not setup yet
    # For GitHub Actions
    # skip_credentials_validation = true
    # skip_metadata_api_check     = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}


provider "aws" {
  region = var.aws_region
}
