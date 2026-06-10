# HelioCloud EKS Cluster Autoscaler Module Tests

variables {
  cluster_name               = "tofu-cluster"
  worker_node_role_name      = "tofu-node-role"
  kubernetes_namespace       = "kube-system"
  kubernetes_service_account = "cluster-autoscaler"
}

run "plan_cluster_autoscaler" {
  command = plan

  plan_options {
    refresh = false
  }

  assert {
    condition     = aws_iam_policy.cluster-autoscaler_policy.name == "HelioCloud_tofu-cluster_PolicyAutoScaling"
    error_message = "IAM policy name should include cluster name."
  }

  assert {
    condition     = aws_iam_role_policy_attachment.cluster-autoscaler_policy_attachment.role == "tofu-node-role"
    error_message = "Policy should attach to provided worker node role."
  }

  assert {
    condition     = aws_iam_role.HelioCloud_cluster-autoscaler_ServiceAccount.name == "HelioCloud_tofu-cluster_cluster-autoscaler_ServiceAccount"
    error_message = "Service account IAM role name should match expected format."
  }

  assert {
    condition = contains(
      data.aws_iam_policy_document.cluster-autoscaler_policy_document.statement[0].actions,
      "autoscaling:SetDesiredCapacity"
    )
    error_message = "Policy must include autoscaling permissions."
  }

  assert {
    condition = contains(
      data.aws_iam_policy_document.pod_assume_role.statement[0].actions,
      "sts:AssumeRole"
    )
    error_message = "Assume role policy must allow sts:AssumeRole."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_cluster_autoscaler_PodIdentityAssociation.cluster_name == "tofu-cluster"
    error_message = "Pod identity association must reference correct cluster."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_cluster_autoscaler_PodIdentityAssociation.namespace == "kube-system"
    error_message = "Namespace should match input."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_cluster_autoscaler_PodIdentityAssociation.service_account == "cluster-autoscaler"
    error_message = "Service account should match input."
  }
}
