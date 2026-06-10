data "aws_region" "current" {}

locals {
  name                     = "aws-efs-csi-driver"
  iam_policy_document_json = file("${path.module}/iam_policy_document.json")

  qualifier = var.qualifier != "" ? var.qualifier : "${var.cluster_name}"
}

data "aws_eks_addon_version" "aws-efs-csi-driver" {
  count              = var.enable_addon_version_lookup ? 1 : 0
  addon_name         = local.name
  kubernetes_version = var.kubernetes_version
  most_recent        = true
}
resource "aws_eks_addon" "efs" {
  cluster_name                = var.cluster_name
  addon_name                  = local.name
  addon_version               = var.enable_addon_version_lookup ? data.aws_eks_addon_version.aws-efs-csi-driver[0].version : null
  resolve_conflicts_on_update = "OVERWRITE"

  tags = { Name = local.name }
}

# pod_identity_association {
#   role_arn        = aws_iam_role.HelioCloud_efs-csi-driver_ServiceAccount.arn
#   service_account = var.kubernetes_service_account
# }

# tags = { Name = "eks-efs-csi-driver" }
# }

resource "aws_iam_policy" "HelioCloud_EfsMountManagedPolicy" {
  name   = "HelioCloud_${local.qualifier}_EfsMountManagedPolicy"
  policy = local.iam_policy_document_json
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

# TODO SECURITY GROUP for worker nodes to EFS target...
resource "aws_iam_role_policy_attachment" "HelioCloud_WorkerNodeRole_AmazonEFSCSIDriverPolicy_PolicyAttachment" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy"
  role       = var.worker_node_role_name
}

resource "aws_iam_role_policy_attachment" "HelioCloud_WorkerNodeRole_EfsMountManagedPolicy_PolicyAttachment" {
  policy_arn = aws_iam_policy.HelioCloud_EfsMountManagedPolicy.arn
  role       = var.worker_node_role_name
}

resource "aws_iam_role" "HelioCloud_EFSCSIDriver_ServiceAccount" {
  name               = substr("HelioCloud_${local.qualifier}_EFSCSIDriver_ServiceAccount", 0, 64)
  assume_role_policy = data.aws_iam_policy_document.pod_assume_role.json
}

resource "aws_iam_role_policy_attachment" "HelioCloud_EFSCSIDriver_AmazonEFSCSIDriverPolicy_PolicyAttachment" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy"
  role       = aws_iam_role.HelioCloud_EFSCSIDriver_ServiceAccount.name
}

resource "aws_iam_role_policy_attachment" "HelioCloud_EFSCSIDriver_EfsMountManagedPolicy_PolicyAttachment" {
  policy_arn = aws_iam_policy.HelioCloud_EfsMountManagedPolicy.arn
  role       = aws_iam_role.HelioCloud_EFSCSIDriver_ServiceAccount.name
}

resource "aws_eks_pod_identity_association" "HelioCloud_EFSCSIDriver_PodIdentityAssociation" {
  cluster_name    = var.cluster_name
  namespace       = var.kubernetes_namespace
  service_account = var.kubernetes_service_account
  role_arn        = aws_iam_role.HelioCloud_EFSCSIDriver_ServiceAccount.arn
}
