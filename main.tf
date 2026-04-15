provider "aws" {
 region = var.aws_region
}

resource "aws_vpc" "myvpc" {
 cidr_block = "192.168.0.0/16"
 tags = {
   Name = "${var.cluster_name}/VPC"
 }
}

resource "aws_nat_gateway" "nat_gateway" {
  vpc_id            = aws_vpc.myvpc.id
  availability_mode = "regional"

  tags = {
   Name = "${var.cluster_name}/NATGateway"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.myvpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id  = aws_nat_gateway.nat_gateway.id
  }

  route {
    cidr_block = aws_vpc.myvpc.cidr_block
    gateway_id = "local"
  }

  tags = {
   Name = "${var.cluster_name}/RouteTablePrivate"
  }
}


resource "aws_subnet" "subnet_private_01" {
 vpc_id = aws_vpc.myvpc.id
 cidr_block = "192.168.0.0/19"
 availability_zone = var.aws_eks_az1
 tags = {
   Name = "${var.cluster_name}/SubnetPrivate-${var.aws_eks_az1}"
 }
}

resource "aws_subnet" "subnet_private_02" {
 vpc_id = aws_vpc.myvpc.id
 cidr_block = "192.168.32.0/19"
 availability_zone = var.aws_eks_az2
 tags = {
   Name = "${var.cluster_name}/SubnetPrivate-${var.aws_eks_az2}"
 }
}

resource "aws_route_table_association" "route_table_association_subnet_private_01" {
  subnet_id = aws_subnet.subnet_private_01.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "route_table_association_subnet_private_02" {
  subnet_id = aws_subnet.subnet_private_02.id
  route_table_id = aws_route_table.private.id
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
    gateway_id  = aws_internet_gateway.gw.id
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
 vpc_id = aws_vpc.myvpc.id
 cidr_block = "192.168.64.0/19"
 availability_zone = var.aws_eks_az1
 map_public_ip_on_launch = true
 tags = {
   Name = "${var.cluster_name}/SubnetPublic-${var.aws_eks_az1}"
 }
}

resource "aws_subnet" "subnet_public_02" {
 vpc_id = aws_vpc.myvpc.id
 cidr_block = "192.168.96.0/19"
 availability_zone = var.aws_eks_az2
 map_public_ip_on_launch = true
 tags = {
   Name = "${var.cluster_name}/SubnetPublic-${var.aws_eks_az2}"
 }
}

resource "aws_route_table_association" "route_table_association_subnet_public_01" {
  subnet_id = aws_subnet.subnet_public_01.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "route_table_association_subnet_public_02" {
  subnet_id = aws_subnet.subnet_public_02.id
  route_table_id = aws_route_table.public.id
}

resource "aws_iam_role" "cluster" {
  name = "eks-cluster-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = ["sts:AssumeRole"]
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role = aws_iam_role.cluster.name
}


resource "aws_iam_role" "nodegroup" {
  name = "${var.cluster_name}-nodegroup"
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
  role = aws_iam_role.nodegroup.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEC2RoleforSSM" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM"
  role = aws_iam_role.nodegroup.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role = aws_iam_role.nodegroup.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role = aws_iam_role.nodegroup.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_AmazonRoute53AutoNamingRegistrantAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonRoute53AutoNamingRegistrantAccess"
  role = aws_iam_role.nodegroup.name
}

resource "aws_iam_role_policy_attachment" "nodegroup_CloudWatchAgentServerPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role = aws_iam_role.nodegroup.name
}



resource "aws_eks_cluster" "private" {
  name     = var.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids = [
        aws_subnet.subnet_private_01.id,    
        aws_subnet.subnet_private_02.id,    
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
  node_role_arn   = aws_iam_role.nodegroup.arn

  # heliocould had a constraint for using a single AZ, so I'll keep that configuration
  # here.
  subnet_ids      = [aws_subnet.subnet_public_01.id]

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
    lifecycle = "OnDemand"
    "hub.jupyter.org/node-purpose" = "core"
  }

  tags = {
    "k8s.io/cluster-autoscaler/node-template/label/lifecycle" = "OnDemand"
    "k8s.io/cluster-autoscaler/node-template/label/hub.jupyter.org/node-purpose" = "core"
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_internet_gateway.gw,
    aws_iam_role.nodegroup,
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

  cluster_name    = aws_eks_cluster.private.name
  node_role_arn   = aws_iam_role.nodegroup.arn

  # heliocould had a constraint for using a single AZ, so I'll keep that configuration
  # here.
  subnet_ids = [aws_subnet.subnet_public_01.id]

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_internet_gateway.gw,
    aws_iam_role.nodegroup,
    aws_iam_role_policy_attachment.nodegroup_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.nodegroup_AmazonEC2RoleforSSM,
    aws_iam_role_policy_attachment.nodegroup_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.nodegroup_AmazonEC2ContainerRegistryReadOnly,
    aws_iam_role_policy_attachment.nodegroup_AmazonRoute53AutoNamingRegistrantAccess,
    aws_iam_role_policy_attachment.nodegroup_CloudWatchAgentServerPolicy
  ]
}
