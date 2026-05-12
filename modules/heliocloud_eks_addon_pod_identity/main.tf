# The Pod Identity Agent must be installed on each node

# It handles credential injection for pods
resource "aws_eks_addon" "pod_identity" {
  cluster_name                = var.cluster_name
  addon_name                  = "eks-pod-identity-agent"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = { Name = "pod-identity-agent" }
}
