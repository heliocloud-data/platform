# HelioCloud EKS External DNS Module Tests

variables {
  cluster_name               = "tofu-cluster"
  kubernetes_namespace       = "kube-system"
  kubernetes_service_account = "external-dns"
  worker_node_role_name      = "tofu-node-role"
}

run "plan_external_dns_addon" {
  command = plan

  plan_options {
    refresh = false
  }

  assert {
    condition     = aws_iam_policy.external_dns_policy.name == "HelioCloud_tofu-cluster_PolicyExternalDnsUpdates"
    error_message = "IAM policy name should include cluster name."
  }

  assert {
    condition     = aws_iam_role_policy_attachment.external_dns_policy_attachment.role == "tofu-node-role"
    error_message = "Policy should attach to worker node role."
  }

  assert {
    condition     = aws_iam_role.HelioCloud_external_dns_ServiceAccount.name == "HelioCloud_tofu-cluster_external_dns_ServiceAccount"
    error_message = "Service account IAM role name should match expected format."
  }

  assert {
    condition = contains(
      data.aws_iam_policy_document.pod_assume_role.statement[0].actions,
      "sts:AssumeRole"
    )
    error_message = "Assume role policy must allow sts:AssumeRole."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_external_dns_PodIdentityAssociation.cluster_name == "tofu-cluster"
    error_message = "Pod identity association must reference correct cluster."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_external_dns_PodIdentityAssociation.namespace == "kube-system"
    error_message = "Namespace should match input."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_external_dns_PodIdentityAssociation.service_account == "external-dns"
    error_message = "Service account should match input."
  }
}
