# HelioCloud EKS Ingress Module Tests

variables {
  release_name                      = "ingress"
  namespace                         = "ingress-nginx"
  chart_version                     = "0.1.0"
  cognito_client_id                 = "test-client-id"
  cognito_client_secret             = "test-client-secret"
  cognito_user_pool_id              = "us-east-1_123456"
  cognito_user_pool_domain          = "test-domain"
  aws_region                        = "us-east-1"
  oauth2_proxy_host                 = "auth.example.com"
  root_domain                       = "example.com"
  oauth2_proxy_cookie_secret        = "super-secret"
  load_balancer_ssl_certificate_arn = null
}

run "plan_ingress" {
  command = plan

  plan_options {
    refresh = false
  }

  assert {
    condition     = helm_release.ingress.name == "ingress"
    error_message = "Helm release name should match input."
  }

  assert {
    condition     = helm_release.ingress.namespace == "ingress-nginx"
    error_message = "Namespace should match input."
  }

  assert {
    condition     = helm_release.ingress.create_namespace
    error_message = "Namespace creation should be enabled."
  }

  assert {
    condition     = helm_release.ingress.wait
    error_message = "Helm release should wait for resources."
  }

  assert {
    condition     = helm_release.ingress.timeout == 600
    error_message = "Timeout should be set to 600 seconds."
  }

}
