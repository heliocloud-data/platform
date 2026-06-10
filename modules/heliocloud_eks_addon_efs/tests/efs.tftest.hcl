# HelioCloud EKS EFS CSI Driver Module Tests

variables {
  cluster_name               = "tofu-cluster"
  kubernetes_version         = "1.29"
  kubernetes_namespace       = "kube-system"
  kubernetes_service_account = "efs-csi-controller-sa"
  worker_node_role_name      = "tofu-node-role"
  qualifier                  = ""
}

run "plan_efs_addon" {
  command = plan

  plan_options {
    refresh = false
  }

  assert {
    condition     = aws_eks_addon.efs.addon_name == "aws-efs-csi-driver"
    error_message = "Addon name should be aws-efs-csi-driver."
  }

  assert {
    condition     = aws_eks_addon.efs.cluster_name == "tofu-cluster"
    error_message = "Addon should be attached to the correct cluster."
  }

  assert {
    condition     = aws_eks_addon.efs.resolve_conflicts_on_update == "OVERWRITE"
    error_message = "Addon should overwrite conflicts on update."
  }

  assert {
    condition     = aws_iam_policy.HelioCloud_EfsMountManagedPolicy.name == "HelioCloud_tofu-cluster_EfsMountManagedPolicy"
    error_message = "Custom EFS policy name should include cluster name."
  }

  assert {
    condition = contains(
      data.aws_iam_policy_document.pod_assume_role.statement[0].actions,
      "sts:AssumeRole"
    )
    error_message = "Assume role policy must allow sts:AssumeRole."
  }

  assert {
    condition     = aws_iam_role_policy_attachment.HelioCloud_WorkerNodeRole_AmazonEFSCSIDriverPolicy_PolicyAttachment.policy_arn == "arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy"
    error_message = "Worker node role must attach AmazonEFSCSIDriverPolicy."
  }

  assert {
    condition     = aws_iam_role_policy_attachment.HelioCloud_WorkerNodeRole_EfsMountManagedPolicy_PolicyAttachment.role == "tofu-node-role"
    error_message = "Custom EFS policy must attach to worker node role."
  }

  assert {
    condition     = aws_iam_role.HelioCloud_EFSCSIDriver_ServiceAccount.name != ""
    error_message = "Service account IAM role should be created."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_EFSCSIDriver_PodIdentityAssociation.cluster_name == "tofu-cluster"
    error_message = "Pod identity association must reference correct cluster."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_EFSCSIDriver_PodIdentityAssociation.namespace == "kube-system"
    error_message = "Namespace should match input."
  }

  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_EFSCSIDriver_PodIdentityAssociation.service_account == "efs-csi-controller-sa"
    error_message = "Service account should match input."
  }
}
