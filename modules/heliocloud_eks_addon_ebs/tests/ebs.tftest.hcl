# HelioCloud EKS EBS CSI Driver Module Tests

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
  cluster_name               = "tofu-cluster"
  kubernetes_version         = "1.29"
  kubernetes_namespace       = "kube-system"
  kubernetes_service_account = "ebs-csi-controller-sa"
  worker_node_role_name      = "tofu-node-role"
}

run "plan_ebs_addon" {
  command = plan

  plan_options {
    refresh = false
  }

  assert {
    condition     = aws_eks_addon.ebs.addon_name == "aws-ebs-csi-driver"
    error_message = "Addon name should be aws-ebs-csi-driver."
  }

  assert {
    condition     = aws_eks_addon.ebs.cluster_name == "tofu-cluster"
    error_message = "Addon should be attached to the correct cluster."
  }

  assert {
    condition     = aws_eks_addon.ebs.resolve_conflicts_on_update == "OVERWRITE"
    error_message = "Addon should overwrite conflicts on update."
  }

  assert {
    condition     = aws_iam_role.HelioCloud_EBSCSIDriver_ServiceAccount.name == "HelioCloud_tofu-cluster_EBSCSIDriver_ServiceAccount"
    error_message = "IAM role name should match expected format."
  }

  assert {
    condition = contains(
      data.aws_iam_policy_document.pod_assume_role.statement[0].actions,
      "sts:AssumeRole"
    )
    error_message = "Assume role policy must allow sts:AssumeRole."
  }

  assert {
    condition     = aws_iam_role_policy_attachment.nodegroup_AmazonEBSCSIDriverPolicy_ServiceAccount.policy_arn == "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
    error_message = "EBS CSI policy attachment should use correct AWS managed policy."
  }

  assert {
    condition     = aws_iam_role_policy_attachment.nodegroup_AmazonEBSCSIDriverPolicyV2_ServiceAccount.policy_arn == "arn:aws:iam::aws:policy/AmazonEBSCSIDriverPolicyV2"
    error_message = "EBS CSI V2 policy attachment should use correct AWS managed policy."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_EBSCSIDriver_PodIdentityAssociation.cluster_name == "tofu-cluster"
    error_message = "Pod identity association must reference correct cluster."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_EBSCSIDriver_PodIdentityAssociation.namespace == "kube-system"
    error_message = "Namespace should match input."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_EBSCSIDriver_PodIdentityAssociation.service_account == "ebs-csi-controller-sa"
    error_message = "Service account should match input."
  }
}
