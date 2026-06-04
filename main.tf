provider "aws" {
  region = var.aws_region
}

locals {
  oauth2_proxy_host         = "${var.auth_subdomain}.${var.root_domain}"
  oauth2_proxy_callback_url = "https://${local.oauth2_proxy_host}/oauth2/callback"
}

resource "random_password" "oauth2_proxy_cookie_secret" {
  length  = 32
  special = false
}

resource "aws_acm_certificate" "HelioCloud_Certificate_Wildcard" {
  domain_name       = "*.${var.root_domain}"
  validation_method = "DNS"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_route53_zone" "HelioCloud_PrimaryZone" {
  name = var.root_domain

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_route53_record" "HelioCloud_Daskhub_Record" {
  zone_id = aws_route53_zone.HelioCloud_PrimaryZone.zone_id
  name    = "${var.daskhub_subdomain}.${var.root_domain}"
  type    = "CNAME"
  ttl     = 300

  # External DNS Kubernetes application will update this record with the LoadBalancer
  # created during the Kubernetes deployment.
  records = ["0.0.0.0"]

  lifecycle {
    ignore_changes = [
      records,
    ]
  }
}

resource "aws_route53_record" "HelioCloud_Portal_Record" {
  zone_id = aws_route53_zone.HelioCloud_PrimaryZone.zone_id
  name    = "${var.portal_subdomain}.${var.root_domain}"
  type    = "CNAME"
  ttl     = 300

  # External DNS Kubernetes application will update this record with the LoadBalancer
  # created during the Kubernetes deployment.
  records = ["0.0.0.0"]

  lifecycle {
    ignore_changes = [
      records,
    ]
  }
}

resource "aws_route53_record" "HelioCloud_Auth_Record" {
  zone_id = aws_route53_zone.HelioCloud_PrimaryZone.zone_id
  name    = "${var.auth_subdomain}.${var.root_domain}"
  type    = "CNAME"
  ttl     = 300

  # External DNS Kubernetes application will update this record with the LoadBalancer
  # created during the Kubernetes deployment.
  records = ["0.0.0.0"]

  lifecycle {
    ignore_changes = [
      records,
    ]
  }
}

resource "aws_vpc" "myvpc" {
  cidr_block = "192.168.0.0/16"
  tags = {
    Name = "${var.cluster_name}/VPC"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.myvpc.id
  tags = {
    Name = "${var.cluster_name}/InternetGateway"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.myvpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  route {
    cidr_block = aws_vpc.myvpc.cidr_block
    gateway_id = "local"
  }

  tags = {
    Name = "${var.cluster_name}/RouteTablePublic"
  }
}

resource "aws_subnet" "subnet_public_01" {
  vpc_id                  = aws_vpc.myvpc.id
  cidr_block              = "192.168.64.0/19"
  availability_zone       = var.aws_eks_az1
  map_public_ip_on_launch = true
  tags = {
    Name = "${var.cluster_name}/SubnetPublic-${var.aws_eks_az1}"
  }
}

resource "aws_subnet" "subnet_public_02" {
  vpc_id                  = aws_vpc.myvpc.id
  cidr_block              = "192.168.96.0/19"
  availability_zone       = var.aws_eks_az2
  map_public_ip_on_launch = true
  tags = {
    Name = "${var.cluster_name}/SubnetPublic-${var.aws_eks_az2}"
  }
}

resource "aws_route_table_association" "route_table_association_subnet_public_01" {
  subnet_id      = aws_subnet.subnet_public_01.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "route_table_association_subnet_public_02" {
  subnet_id      = aws_subnet.subnet_public_02.id
  route_table_id = aws_route_table.public.id
}

resource "aws_iam_role" "HelioCloud_EKS_ClusterRole" {
  name = "HelioCloud_${var.cluster_name}_ClusterRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = ["sts:AssumeRole"]
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.HelioCloud_EKS_ClusterRole.name
}

resource "aws_iam_role" "HelioCloud_EKS_NodeGroupRole" {
  name = "HelioCloud_${var.cluster_name}_NodeGroupRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = ["sts:AssumeRole"]
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEC2RoleforSSM" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM"
  role       = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonRoute53AutoNamingRegistrantAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonRoute53AutoNamingRegistrantAccess"
  role       = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_CloudWatchAgentServerPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}



resource "aws_eks_cluster" "private" {
  name     = var.cluster_name
  role_arn = aws_iam_role.HelioCloud_EKS_ClusterRole.arn
  version  = var.kubernetes_version

  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = true
  }

  vpc_config {
    subnet_ids = [
      aws_subnet.subnet_public_01.id,
      aws_subnet.subnet_public_02.id
    ]

    # Disable public endpoint - API only accessible within VPC
    endpoint_public_access  = true
    endpoint_private_access = false
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator"]

  tags = {
    Name    = var.cluster_name
    Private = "true"
  }
}

resource "aws_eks_node_group" "mng_daskhub_service" {
  cluster_name    = aws_eks_cluster.private.name
  node_group_name = "mng_daskhub_service"
  node_role_arn   = aws_iam_role.HelioCloud_EKS_NodeGroupRole.arn

  # heliocould had a constraint for using a single AZ, so I'll keep that configuration
  # here.
  subnet_ids = [aws_subnet.subnet_public_01.id]

  instance_types = ["t3a.medium"]

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 2
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    lifecycle                      = "OnDemand"
    "hub.jupyter.org/node-purpose" = "core"
  }

  tags = {
    "k8s.io/cluster-autoscaler/node-template/label/lifecycle"                    = "OnDemand"
    "k8s.io/cluster-autoscaler/node-template/label/hub.jupyter.org/node-purpose" = "core"
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_internet_gateway.gw,
    aws_iam_role.HelioCloud_EKS_NodeGroupRole,
    aws_iam_role_policy_attachment.nodegroup_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.nodegroup_AmazonEC2RoleforSSM,
    aws_iam_role_policy_attachment.nodegroup_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.nodegroup_AmazonEC2ContainerRegistryReadOnly,
    aws_iam_role_policy_attachment.nodegroup_AmazonRoute53AutoNamingRegistrantAccess,
    aws_iam_role_policy_attachment.nodegroup_CloudWatchAgentServerPolicy
  ]
}

module "heliocloud_eks_node_group_jupyterhub_user_compute" {
  source = "./modules/heliocloud_eks_node_group_jupyterhub_user_compute"

  cluster_name  = aws_eks_cluster.private.name
  node_role_arn = aws_iam_role.HelioCloud_EKS_NodeGroupRole.arn

  # heliocould had a constraint for using a single AZ, so I'll keep that configuration
  # here.
  subnet_ids = [aws_subnet.subnet_public_01.id]

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_internet_gateway.gw,
    aws_iam_role.HelioCloud_EKS_NodeGroupRole,
    aws_iam_role_policy_attachment.nodegroup_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.nodegroup_AmazonEC2RoleforSSM,
    aws_iam_role_policy_attachment.nodegroup_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.nodegroup_AmazonEC2ContainerRegistryReadOnly,
    aws_iam_role_policy_attachment.nodegroup_AmazonRoute53AutoNamingRegistrantAccess,
    aws_iam_role_policy_attachment.nodegroup_CloudWatchAgentServerPolicy
  ]
}

module "heliocloud_eks_addon_pod_identity" {
  source = "./modules/heliocloud_eks_addon_pod_identity"

  cluster_name       = aws_eks_cluster.private.name
  kubernetes_version = var.kubernetes_version
}

module "heliocloud_eks_addon_cluster_autoscaler" {
  source = "./modules/heliocloud_eks_addon_cluster_autoscaler"

  cluster_name          = aws_eks_cluster.private.name
  worker_node_role_name = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}

module "heliocloud_eks_addon_external_dns" {
  source = "./modules/heliocloud_eks_addon_external_dns"

  cluster_name          = aws_eks_cluster.private.name
  worker_node_role_name = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}

module "heliocloud_eks_addon_ebs" {
  source = "./modules/heliocloud_eks_addon_ebs"

  cluster_name          = aws_eks_cluster.private.name
  kubernetes_version    = var.kubernetes_version
  worker_node_role_name = aws_iam_role.HelioCloud_EKS_NodeGroupRole.name
}

module "heliocloud_auth" {
  source = "./modules/heliocloud_auth"

  user_pool_name        = "${replace(var.cluster_name, "_", "-")}-user-pool"
  domain_prefix         = replace(var.cognito_subdomain, "_", "-")
  user_pool_client_name = "${replace(var.cluster_name, "_", "-")}-client"

  deletion_protection = false
  callback_urls       = distinct(concat(var.cognito_callback_urls, [local.oauth2_proxy_callback_url]))
  logout_urls         = var.cognito_logout_urls
  tags                = var.tags
}

module "heliocloud_eks_ingress" {
  source = "./modules/heliocloud_eks_ingress"

  aws_region                        = var.aws_region
  oauth2_proxy_host                 = local.oauth2_proxy_host
  root_domain                       = var.root_domain
  cognito_user_pool_id              = module.heliocloud_auth.user_pool_id
  cognito_user_pool_domain          = module.heliocloud_auth.user_pool_domain
  cognito_client_id                 = module.heliocloud_auth.user_pool_client_id
  cognito_client_secret             = module.heliocloud_auth.user_pool_client_secret
  oauth2_proxy_cookie_secret        = coalesce(var.oauth2_proxy_cookie_secret, random_password.oauth2_proxy_cookie_secret.result)
  load_balancer_ssl_certificate_arn = aws_acm_certificate.HelioCloud_Certificate_Wildcard.arn

  depends_on = [
    aws_eks_cluster.private,
    aws_eks_node_group.mng_daskhub_service,
    module.heliocloud_eks_node_group_jupyterhub_user_compute,
    module.heliocloud_auth
  ]
}

module "efs" {
  source               = "terraform-aws-modules/efs/aws"
  version              = "~> 2.0"
  name                 = "heliocloud-efs-user-share"
  creation_token       = "heliocloud-efs-user-share-token"
  encrypted            = true
  performance_mode     = "generalPurpose"
  enable_backup_policy = true

  mount_targets = {
    "${var.aws_eks_az1}" = { subnet_id = aws_subnet.subnet_public_01.id }
    "${var.aws_eks_az2}" = { subnet_id = aws_subnet.subnet_public_02.id }
  }
  security_group_vpc_id = aws_vpc.myvpc.id
  tags                  = var.tags
}

module "heliocloud_portal" {
  source = "./modules/heliocloud_portal"

  cluster_name = var.cluster_name

  aws_az1                     = var.aws_eks_az1
  aws_az2                     = var.aws_eks_az2
  identity_provider_client_id = module.heliocloud_auth.user_pool_client_id
  identity_provider_name      = "cognito-idp.${var.aws_region}.amazonaws.com/${module.heliocloud_auth.user_pool_id}"

}
