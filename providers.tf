data "aws_eks_cluster" "private" {
  name = aws_eks_cluster.private.name
}

data "aws_eks_cluster_auth" "private" {
  name = aws_eks_cluster.private.name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.private.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.private.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.private.token
}
