locals {
  iam_policy_document_json = file("${path.module}/iam_policy_document.json")
}

resource "aws_iam_policy" "external_dns_policy" {
  name   = "HelioCloud_${var.cluster_name}_PolicyExternalDnsUpdates"
  policy = local.iam_policy_document_json
}

resource "aws_iam_role_policy_attachment" "external_dns_policy_attachment" {
  policy_arn = aws_iam_policy.external_dns_policy.arn
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

resource "aws_iam_role" "HelioCloud_external_dns_ServiceAccount" {
  name               = "HelioCloud_${var.cluster_name}_external_dns_ServiceAccount"
  assume_role_policy = data.aws_iam_policy_document.pod_assume_role.json
}

resource "aws_iam_role_policy_attachment" "HelioCloud_external_dns_ServiceAccount" {
  policy_arn = aws_iam_policy.external_dns_policy.arn
  role       = aws_iam_role.HelioCloud_external_dns_ServiceAccount.name
}

resource "aws_eks_pod_identity_association" "HelioCloud_external_dns_PodIdentityAssociation" {
  cluster_name    = var.cluster_name
  namespace       = var.kubernetes_namespace
  service_account = var.kubernetes_service_account
  role_arn        = aws_iam_role.HelioCloud_external_dns_ServiceAccount.arn
}
