# HelioCloud Auth Module Test - Basic Plan Validation
# Covers: Basic plan validation with a realistic variable set, including all required variables and some optional

# Fake AWS provider to allow plan without real credentials
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "mock"
  secret_key                  = "mock"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

variables {
  user_pool_name              = "tofu-auth-user-pool"
  domain_prefix               = "tofu-auth"
  user_pool_client_name       = "tofu-auth-client"
  deletion_protection         = false
  access_token_validity_hours = 2
  id_token_validity_hours     = 2
  refresh_token_validity_days = 7
  callback_urls               = ["https://example.test/oauth/callback"]
  logout_urls                 = ["https://example.test/logout"]
  tags = {
    managed-by = "tofu-test"
    test-tier  = "module"
  }
}

run "plan_heliocloud_auth_module" {
  command = plan

  plan_options {
    refresh = false
  }

  assert {
    condition     = aws_cognito_user_pool.user_pool.name == "tofu-auth-user-pool"
    error_message = "Expected the user pool name to match the configured module input."
  }

  assert {
    condition     = aws_cognito_user_pool.user_pool.deletion_protection == "INACTIVE"
    error_message = "Expected deletion protection to be disabled when the module input is false."
  }

  assert {
    condition     = aws_cognito_user_pool.user_pool.admin_create_user_config[0].allow_admin_create_user_only
    error_message = "Expected self-service sign-up to remain disabled."
  }

  assert {
    condition = contains(
      aws_cognito_user_pool.user_pool.auto_verified_attributes,
      "email"
    )
    error_message = "Expected email to remain the auto-verified attribute."
  }

  assert {
    condition     = aws_cognito_user_pool_domain.domain.domain == "tofu-auth"
    error_message = "Expected the Cognito hosted UI domain to match the configured domain prefix."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.name == "tofu-auth-client"
    error_message = "Expected the user pool client name to match the configured module input."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.generate_secret
    error_message = "Expected the user pool client to generate a secret."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.access_token_validity == 2
    error_message = "Expected the access token validity to honor the module input."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.id_token_validity == 2
    error_message = "Expected the ID token validity to honor the module input."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.refresh_token_validity == 7
    error_message = "Expected the refresh token validity to honor the module input."
  }

  assert {
    condition     = contains(aws_cognito_user_pool_client.client.callback_urls, "https://example.test/oauth/callback")
    error_message = "Expected the callback URL list to be passed to the user pool client."
  }

  assert {
    condition     = contains(aws_cognito_user_pool_client.client.logout_urls, "https://example.test/logout")
    error_message = "Expected the logout URL list to be passed to the user pool client."
  }

  assert {
    condition     = output.user_pool_domain == "tofu-auth"
    error_message = "Expected the module output to expose the configured Cognito domain."
  }

  assert {
    condition     = output.user_pool_id != ""
    error_message = "Expected the module to output a non-empty user pool ID."
  }

  assert {
    condition     = output.user_pool_client_id != ""
    error_message = "Expected the module to output a non-empty user pool client ID."
  }

  assert {
    condition     = aws_cognito_user_pool.user_pool.tags["managed-by"] == "tofu-test"
    error_message = "Expected tags to propagate to the Cognito user pool."
  }

  assert {
    condition     = aws_cognito_user_pool.user_pool.tags["test-tier"] == "module"
    error_message = "Expected all provided tags to propagate correctly."
  }

  # NOTE: Cannot assert relationships using IDs at plan time because they are unknown.
  # These would require apply-time validation or different test strategy.
}

# Validation failure tests for all variables with validation blocks, covering empty strings etc.



run "reject_empty_user_pool_name" {
  command = plan

  variables {
    user_pool_name        = ""
    domain_prefix         = "tofu-invalid-auth"
    user_pool_client_name = "tofu-invalid-auth-client"
  }

  expect_failures = [var.user_pool_name]
}

run "reject_missing_domain_name_when_ses_identity_enabled" {
  command = plan

  variables {
    create_ses_identity   = true
    domain_name           = ""
    user_pool_name        = "tofu-invalid-auth-user-pool"
    domain_prefix         = "tofu-invalid-auth"
    user_pool_client_name = "tofu-invalid-auth-client"
  }

  expect_failures = [var.domain_name]
}

run "reject_empty_domain_prefix" {
  command = plan

  variables {
    user_pool_name        = "tofu-invalid-auth-user-pool"
    domain_prefix         = ""
    user_pool_client_name = "tofu-invalid-auth-client"
  }

  expect_failures = [var.domain_prefix]
}

run "reject_empty_user_pool_client_name" {
  command = plan

  variables {
    user_pool_name        = "tofu-invalid-auth-user-pool"
    domain_prefix         = "tofu-invalid-auth"
    user_pool_client_name = ""
  }

  expect_failures = [var.user_pool_client_name]
}

run "reject_empty_certificate_arn_when_provided" {
  command = plan

  variables {
    certificate_arn = ""
  }

  expect_failures = [var.certificate_arn]
}

run "reject_non_positive_access_token_validity" {
  command = plan

  variables {
    access_token_validity_hours = 0
  }

  expect_failures = [var.access_token_validity_hours]
}

run "reject_non_positive_id_token_validity" {
  command = plan

  variables {
    id_token_validity_hours = 0
  }

  expect_failures = [var.id_token_validity_hours]
}

run "reject_non_positive_refresh_token_validity" {
  command = plan

  variables {
    refresh_token_validity_days = 0
  }

  expect_failures = [var.refresh_token_validity_days]
}

run "reject_empty_callback_url_entry" {
  command = plan

  variables {
    callback_urls = [""]
  }

  expect_failures = [var.callback_urls]
}

run "reject_empty_logout_url_entry" {
  command = plan

  variables {
    logout_urls = [""]
  }

  expect_failures = [var.logout_urls]
}

run "reject_incomplete_email_configuration" {
  command = plan

  variables {
    email_configuration = {
      from_email = ""
      source_arn = ""
    }
  }

  expect_failures = [var.email_configuration]
}
