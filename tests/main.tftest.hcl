# HelioCloud Platform Root Module Tests

variables {
  aws_region            = "us-east-1"
  cluster_name          = "test-cluster"
  kubernetes_version    = "1.29"
  aws_eks_az1           = "us-east-1a"
  aws_eks_az2           = "us-east-1b"
  cognito_callback_urls = ["https://example.com/callback"]
  cognito_logout_urls   = ["https://example.com/logout"]
  root_domain           = "example.com"
  oauth2_proxy_host     = "auth.example.com"

  tags = {
    Environment = "test"
  }
}

# NOTE:
# Root module includes Helm provider wiring that cannot be evaluated at plan time
# due to unknown Kubernetes connection values.
#
# OpenTofu tests cannot exclude these resources or catch provider init failures,
# so we intentionally do not define a run block here.
#
# Root module validation is covered indirectly via module-level tests.
