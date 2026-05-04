locals {
  name = "aws-ebs-csi-driver"
}

data "aws_eks_addon_version" "eks-ebs-csi-driver" {
  addon_name         = local.name
  kubernetes_version = var.kubernetes_version
  most_recent        = true

  depends_on = [
    aws_iam_role_policy_attachment.nodegroup_AmazonEBSCSIDriverPolicy_ServiceAccount,
    aws_iam_role_policy_attachment.nodegroup_AmazonEBSCSIDriverPolicyV2_ServiceAccount
  ]
}

resource "aws_eks_addon" "ebs" {
  cluster_name                = var.cluster_name
  addon_name                  = local.name
  addon_version               = data.aws_eks_addon_version.eks-ebs-csi-driver.version
  resolve_conflicts_on_update = "OVERWRITE"

  tags = { Name = local.name }
}

data "aws_iam_policy_document" "pod_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole",
      "sts:TagSession"
    ]
  }
}

resource "aws_iam_role" "HelioCloud_EBSCSIDriver_ServiceAccount" {
  name               = "HelioCloud_${var.cluster_name}_EBSCSIDriver_ServiceAccount"
  assume_role_policy = data.aws_iam_policy_document.pod_assume_role.json
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEBSCSIDriverPolicy_ServiceAccount" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
  role       = aws_iam_role.HelioCloud_EBSCSIDriver_ServiceAccount.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEBSCSIDriverPolicyV2_ServiceAccount" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEBSCSIDriverPolicyV2"
  role       = aws_iam_role.HelioCloud_EBSCSIDriver_ServiceAccount.name
}

resource "aws_eks_pod_identity_association" "HelioCloud_EBSCSIDriver_PodIdentityAssociation" {
  cluster_name    = var.cluster_name
  namespace       = var.kubernetes_namespace
  service_account = var.kubernetes_service_account
  role_arn        = aws_iam_role.HelioCloud_EBSCSIDriver_ServiceAccount.arn
}
