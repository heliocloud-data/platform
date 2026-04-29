# Covers: root-stack integration wiring with a minimal realistic variable set.
# Mode: plan only with refresh disabled.
# Real AWS resources: no creates, but provider/data-source access may still be required.
# Intended use: regular CI after smoke tests or pre-merge verification.

variables {
  aws_region            = "us-east-1"
  aws_eks_az1           = "us-east-1a"
  aws_eks_az2           = "us-east-1b"
  cluster_name          = "tofu-int-root"
  kubernetes_version    = "1.33"
  cognito_callback_urls = ["https://example.test/oauth/callback"]
  cognito_logout_urls   = ["https://example.test/logout"]
  tags = {
    managed-by = "tofu-test"
    test-tier  = "integration"
  }
}

run "plan_root_module_minimal_stack" {
  command = plan

  plan_options {
    refresh = false
  }

  assert {
    condition     = aws_iam_role.cluster.name == "tofu-int-root-cluster-role"
    error_message = "Expected the root cluster IAM role name to be derived from the cluster name."
  }

  assert {
    condition     = module.cognito.user_pool_domain == "tofu-int-root"
    error_message = "Expected the Cognito hosted UI domain output to match the sanitized cluster name."
  }

  assert {
    condition     = output.cognito_user_pool_domain == "tofu-int-root"
    error_message = "Expected the root output to expose the Cognito user pool domain."
  }

  assert {
    condition     = aws_eks_cluster.private.version == "1.33"
    error_message = "Expected the configured Kubernetes version to be passed into the EKS cluster."
  }

  assert {
    condition     = output.cognito_client_id == module.cognito.user_pool_client_id
    error_message = "Expected the root output to forward the Cognito client ID."
  }

  assert {
    condition     = output.eks_cluster_name == "tofu-int-root"
    error_message = "Expected the root output to expose the configured EKS cluster name."
  }
}
