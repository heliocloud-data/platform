# HelioCloud EKS Pod Identity Agent Module Tests

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
  cluster_name                = "tofu-cluster"
  kubernetes_version          = "1.29"
  enable_addon_version_lookup = false
}

run "plan_pod_identity_addon" {
  command = plan

  plan_options {
    refresh = false
  }

  assert {
    condition     = aws_eks_addon.pod_identity.addon_name == "eks-pod-identity-agent"
    error_message = "Addon name should be eks-pod-identity-agent."
  }

  assert {
    condition     = aws_eks_addon.pod_identity.cluster_name == "tofu-cluster"
    error_message = "Addon should be attached to the correct cluster."
  }

  assert {
    condition     = aws_eks_addon.pod_identity.resolve_conflicts_on_update == "OVERWRITE"
    error_message = "Addon should overwrite conflicts on update."
  }

  assert {
    condition     = aws_eks_addon.pod_identity.tags["Name"] == "pod-identity-agent"
    error_message = "Tag Name should be set correctly."
  }
}
