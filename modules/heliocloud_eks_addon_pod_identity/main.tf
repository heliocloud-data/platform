# The Pod Identity Agent must be installed on each node

# It handles credential injection for pods
data "aws_eks_addon_version" "pod_identity" {
  count              = var.enable_addon_version_lookup ? 1 : 0
  addon_name         = "eks-pod-identity-agent"
  kubernetes_version = var.kubernetes_version
  most_recent        = true
}

resource "aws_eks_addon" "pod_identity" {
  cluster_name                = var.cluster_name
  addon_name                  = "eks-pod-identity-agent"
  addon_version               = var.enable_addon_version_lookup ? data.aws_eks_addon_version.pod_identity[0].version : null
  resolve_conflicts_on_update = "OVERWRITE"

  tags = { Name = "pod-identity-agent" }
}
