# This module sets up a Cognito User Pool with an optional SES domain identity for email verification. It also creates a user pool client with specified callback and logout URLs.

# SES Identity (for email verification)
resource "aws_ses_domain_identity" "domain_identity" {
  count  = var.create_ses_identity ? 1 : 0
  domain = var.domain_name
}

resource "aws_ses_domain_identity_verification" "domain_verification" {
  count      = var.create_ses_identity ? 1 : 0
  domain     = aws_ses_domain_identity.domain_identity[0].domain
  depends_on = [aws_ses_domain_identity.domain_identity]
}

# Cognito User Pool Config
resource "aws_cognito_user_pool" "user_pool" {
  name = var.user_pool_name

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Sign in options
  username_configuration {
    case_sensitive = false
  }

  # Deletion protection
  deletion_protection = var.deletion_protection ? "ACTIVE" : "INACTIVE"

  # Standard attributes
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }

  # Custom attributes
  schema {
    name                = "affiliation"
    attribute_data_type = "String"
    string_attribute_constraints {
      max_length = "50"
    }
    mutable = true
  }

  schema {
    name                = "access_code"
    attribute_data_type = "String"
    string_attribute_constraints {
      max_length = "50"
    }
    mutable = false
  }

  # Auto verify email
  auto_verified_attributes = ["email"]

  # Self sign up disabled
  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  # Email configuration (if SES identity is provided)
  dynamic "email_configuration" {
    for_each = var.email_configuration != null ? [1] : []
    content {
      email_sending_account = "DEVELOPER"
      from_email_address    = var.email_configuration.from_email
      source_arn            = var.create_ses_identity ? aws_ses_domain_identity.domain_identity[0].arn : var.email_configuration.source_arn
    }
  }

  # Removal policy
  lifecycle {
    ignore_changes = []
  }

  tags = var.tags
}

# Cognito User Pool Domain Config
resource "aws_cognito_user_pool_domain" "domain" {
  domain          = var.domain_prefix
  user_pool_id    = aws_cognito_user_pool.user_pool.id
  certificate_arn = var.certificate_arn
}

# Cognito User Pool Client Config
# Only one client is needed for the cluster, multiple callback/logout URLs are configured on the client itself - these are set in the main variables.
resource "aws_cognito_user_pool_client" "client" {
  name         = var.user_pool_client_name
  user_pool_id = aws_cognito_user_pool.user_pool.id

  # Generate client secret
  generate_secret = true

  # OAuth settings
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  # Token validity
  access_token_validity  = var.access_token_validity_hours
  id_token_validity      = var.id_token_validity_hours
  refresh_token_validity = var.refresh_token_validity_days

  # Logout URLs
  logout_urls = var.logout_urls

  # Callback URLs
  callback_urls = var.callback_urls

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # Token revocation
  enable_token_revocation = true

  # Read/write attributes
  read_attributes = [
    "email",
    "email_verified",
    "custom:affiliation",
    "custom:access_code"
  ]

  write_attributes = [
    "email",
    "custom:affiliation"
  ]
}

# The UI Customization is a bit buggy at the moment, so I'm leaving it out for now. It can be added back in later as needed.

# UI Customization
# resource "aws_cognito_user_pool_ui_customization" "customization" {
#   user_pool_id = aws_cognito_user_pool.user_pool.id
#   client_id    = aws_cognito_user_pool_client.client.id

#   css = file("${path.module}/static/style.css")

#   # Note: Image upload would require additional handling
#   # For now, using CSS only as in the CDK version
# }
