# The Pod Identity Agent must be installed on each node

# It handles credential injection for pods
data "aws_eks_addon_version" "pod_identity" {
  addon_name         = "eks-pod-identity-agent"
  kubernetes_version = var.kubernetes_version
  most_recent        = true
}

resource "aws_eks_addon" "pod_identity" {
  cluster_name                = var.cluster_name
  addon_name                  = "eks-pod-identity-agent"
  addon_version               = data.aws_eks_addon_version.pod_identity.version
  resolve_conflicts_on_update = "OVERWRITE"

  tags = { Name = "pod-identity-agent" }
}
