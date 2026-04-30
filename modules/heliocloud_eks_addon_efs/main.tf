resource "aws_eks_addon" "efs" {
  cluster_name                = var.cluster_name
  addon_name                  = "eks-efs-csi-driver"
  addon_version               = "v3.0.1-eksbuild.1"
  resolve_conflicts_on_update = "OVERWRITE"

  pod_identity_association {
    role_arn        = aws_iam_role.HelioCloud_efs-csi-driver_ServiceAccount.arn
    service_account = var.kubernetes_service_account
  }

  tags = { Name = "eks-efs-csi-driver" }
}

locals {
  iam_policy_document_json = file("${path.module}/iam_policy_document.json")
}

resource "aws_iam_policy" "aws-efs-csi-driver_policy" {
  name   = "HelioCloud_${var.cluster_name}_EfsMountManagedPolicy"
  policy = local.iam_policy_document_json
}

resource "aws_iam_role_policy_attachment" "aws-efs-csi-driver_policy_attachment" {
  policy_arn = aws_iam_policy.aws-efs-csi-driver_policy.arn
  role       = var.worker_node_role_name
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

resource "aws_iam_role" "HelioCloud_efs-csi-driver_ServiceAccount" {
  name               = "HelioCloud_${var.cluster_name}_efs-csi-driver_ServiceAccount"
  assume_role_policy = data.aws_iam_policy_document.pod_assume_role.json
}

resource "aws_iam_role_policy_attachment" "HelioCloud_efs-csi-driver_ServiceAccount" {
  policy_arn = aws_iam_policy.aws-efs-csi-driver_policy.arn
  role       = aws_iam_role.HelioCloud_efs-csi-driver_ServiceAccount.name
}
