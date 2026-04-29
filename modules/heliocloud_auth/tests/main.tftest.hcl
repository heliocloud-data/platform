variables {
  user_pool_name        = "tofu-test-helio-user-pool"
  domain_prefix         = "tofu-test-helio"
  user_pool_client_name = "tofu-test-helio-client"
  deletion_protection   = false
  callback_urls         = ["http://localhost:8000/oauth_callback"]
  logout_urls           = ["http://localhost:8000"]
  tags = {
    environment = "test"
  }
}

run "plan_auth_module" {
  command = plan

  assert {
    condition     = aws_cognito_user_pool.user_pool.name == "tofu-test-helio-user-pool"
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
    condition     = aws_cognito_user_pool.user_pool.auto_verified_attributes[0] == "email"
    error_message = "Expected email to remain the auto-verified attribute."
  }

  assert {
    condition     = aws_cognito_user_pool_domain.domain.domain == "tofu-test-helio"
    error_message = "Expected the Cognito hosted UI domain to match the configured domain prefix."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.name == "tofu-test-helio-client"
    error_message = "Expected the user pool client name to match the configured module input."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.generate_secret
    error_message = "Expected the user pool client to generate a secret."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.callback_urls[0] == "http://localhost:8000/oauth_callback"
    error_message = "Expected the callback URL list to be passed to the user pool client."
  }

  assert {
    condition     = aws_cognito_user_pool_client.client.logout_urls[0] == "http://localhost:8000"
    error_message = "Expected the logout URL list to be passed to the user pool client."
  }

  assert {
    condition     = output.user_pool_domain == "tofu-test-helio"
    error_message = "Expected the module output to expose the configured Cognito domain."
  }
}
