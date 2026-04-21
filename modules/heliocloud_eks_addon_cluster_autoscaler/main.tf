data "aws_iam_policy_document" "cluster-autoscaler_policy_document" {
  statement {
    actions = [
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:DescribeAutoScalingInstances",
      "autoscaling:DescribeLaunchConfigurations",
      "autoscaling:DescribeScalingActivities",
      "autoscaling:DescribeTags",
      "ec2:DescribeInstanceTypes",
      "ec2:DescribeLaunchTemplateVersions",
      "autoscaling:SetDesiredCapacity",
      "autoscaling:TerminateInstanceInAutoScalingGroup",
      "ec2:DescribeImages",
      "ec2:GetInstanceTypesFromInstanceRequirements",
      "eks:DescribeNodegroup"
    ]
    resources = ["*"]
    effect    = "Allow"
  }
}

resource "aws_iam_policy" "cluster-autoscaler_policy" {
  name   = "HelioCloud_${var.cluster_name}_PolicyAutoScaling"
  policy = data.aws_iam_policy_document.cluster-autoscaler_policy_document.json
}

resource "aws_iam_role_policy_attachment" "cluster-autoscaler_policy_attachment" {
  policy_arn = aws_iam_policy.cluster-autoscaler_policy.arn
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

resource "aws_iam_role" "HelioCloud_cluster-autoscaler_ServiceAccount" {
  name               = "HelioCloud_${var.cluster_name}_cluster-autoscaler_ServiceAccount"
  assume_role_policy = data.aws_iam_policy_document.pod_assume_role.json
}

resource "aws_iam_role_policy_attachment" "HelioCloud_cluster-autoscaler_ServiceAccount" {
  policy_arn = aws_iam_policy.cluster-autoscaler_policy.arn
  role       = aws_iam_role.HelioCloud_cluster-autoscaler_ServiceAccount.name
}

resource "aws_eks_pod_identity_association" "HelioCloud_cluster_autoscaler_PodIdentityAssociation" {
  cluster_name    = var.cluster_name
  namespace       = var.kubernetes_namespace
  service_account = var.kubernetes_service_account
  role_arn        = aws_iam_role.HelioCloud_cluster-autoscaler_ServiceAccount.arn
}
