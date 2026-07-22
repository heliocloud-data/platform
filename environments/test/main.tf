module "aws_cognito" {
  source = "../../modules/aws_cognito"

  user_pool_name        = "${var.project}-${var.environment}-user-pool"
  user_pool_client_name = "${var.project}-${var.environment}-user-pool-client"
  create_ses_identity   = true
  domain_name           = "${var.domain}.com"
  deletion_protection   = false
  callback_urls         = ["https://${var.domain}.com/callback"]
  logout_urls           = ["https://${var.domain}.com/logout"]

  tags = {
    Environment = "test"
  }

}
