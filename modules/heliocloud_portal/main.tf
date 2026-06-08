
resource "aws_vpc" "HelioCloud_Portal_VPC" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "HelioCloud/Portal/VPC"
  }
}

resource "aws_internet_gateway" "HelioCloud_Portal_InternetGateway" {
  vpc_id = aws_vpc.HelioCloud_Portal_VPC.id
  tags = {
    Name = "HelioCloud/Portal/InternetGateway"
  }
}

resource "aws_route_table" "HelioCloud_Portal_RouteTable" {
  vpc_id = aws_vpc.HelioCloud_Portal_VPC.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.HelioCloud_Portal_InternetGateway.id
  }

  route {
    cidr_block = aws_vpc.HelioCloud_Portal_VPC.cidr_block
    gateway_id = "local"
  }

  tags = {
    Name = "HelioCloud/Portal/RouteTablePublic"
  }
}

resource "aws_subnet" "HelioCloud_Portal_Subnet_Public_01" {
  vpc_id                  = aws_vpc.HelioCloud_Portal_VPC.id
  cidr_block              = "10.0.0.0/18"
  availability_zone       = var.aws_az1
  map_public_ip_on_launch = true
  tags = {
    Name = "HelioCloud/Portal/SubnetPublic-${var.aws_az1}"
  }
}

resource "aws_subnet" "HelioCloud_Portal_Subnet_Public_02" {
  vpc_id                  = aws_vpc.HelioCloud_Portal_VPC.id
  cidr_block              = "10.0.64.0/18"
  availability_zone       = var.aws_az2
  map_public_ip_on_launch = true
  tags = {
    Name = "HelioCloud/Portal/SubnetPublic-${var.aws_az2}"
  }
}

resource "aws_route_table_association" "HelioCloud_Portal_RouteTableAssociation_SubnetPublic_01" {
  subnet_id      = aws_subnet.HelioCloud_Portal_Subnet_Public_01.id
  route_table_id = aws_route_table.HelioCloud_Portal_RouteTable.id
}

resource "aws_route_table_association" "HelioCloud_Portal_RouteTableAssociation_SubnetPublic_02" {
  subnet_id      = aws_subnet.HelioCloud_Portal_Subnet_Public_02.id
  route_table_id = aws_route_table.HelioCloud_Portal_RouteTable.id
}

locals {
  iam_policy_document_json_UserS3Policy                       = file("${path.module}/iam_policy_document_UserS3Policy.json")
  iam_policy_document_json_IdentityPool_AuthenticatedPolicy   = file("${path.module}/iam_policy_document_IdentityPool_AuthenticatedPolicy.json")
  iam_policy_document_json_IdentityPool_UnauthenticatedPolicy = file("${path.module}/iam_policy_document_IdentityPool_UnauthenticatedPolicy.json")
}

resource "aws_iam_role" "HelioCloud_Portal_UserRole" {
  name        = "PortalEc2Role"
  description = "Default Portal EC2 Role with S3 access"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = ["sts:AssumeRole"]
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "HelioCloud_Portal_UserS3Policy" {
  name   = "HelioCloud_Portal_UserS3Policy"
  policy = local.iam_policy_document_json_UserS3Policy
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


resource "aws_iam_role" "HelioCloud_Portal_ServiceAccount" {
  name               = "HelioCloud_${var.cluster_name}_Portal_ServiceAccount"
  assume_role_policy = data.aws_iam_policy_document.pod_assume_role.json
}

resource "aws_iam_role_policy_attachment" "HelioCloud_Portal_PolicyAttachment" {
  policy_arn = aws_iam_policy.HelioCloud_Portal_UserS3Policy.arn
  role       = aws_iam_role.HelioCloud_Portal_ServiceAccount.name
}

resource "aws_eks_pod_identity_association" "HelioCloud_Portal_PodIdentityAssociation" {
  cluster_name    = var.cluster_name
  namespace       = var.kubernetes_namespace
  service_account = var.kubernetes_service_account
  role_arn        = aws_iam_role.HelioCloud_Portal_ServiceAccount.arn
}


resource "aws_iam_role_policy_attachment" "HelioCloud_Portal_UserS3Policy_Attachment" {
  policy_arn = aws_iam_policy.HelioCloud_Portal_UserS3Policy.arn
  role       = aws_iam_role.HelioCloud_Portal_UserRole.name
}

resource "aws_iam_instance_profile" "HelioCloud_Portal_UserInstanceProfile" {
  name = "PortalEc2InstanceProfile"
  role = aws_iam_role.HelioCloud_Portal_UserRole.name
}

resource "aws_security_group" "HelioCloud_Portal_UserSecurityGroup" {
  name        = "PortalEc2SecurityGroup"
  description = "SecurityGroup attached to all user spawned instances withing the HelioCloud Portal."
  vpc_id      = aws_vpc.HelioCloud_Portal_VPC.id
}

resource "aws_vpc_security_group_ingress_rule" "HelioCloud_Portal_UserSecurityGroup_IngressRule_SSH" {
  security_group_id = aws_security_group.HelioCloud_Portal_UserSecurityGroup.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

resource "aws_vpc_security_group_ingress_rule" "HelioCloud_Portal_UserSecurityGroup_IngressRule_HTTPS" {
  security_group_id = aws_security_group.HelioCloud_Portal_UserSecurityGroup.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  ip_protocol       = "tcp"
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "HelioCloud_Portal_UserSecurityGroup_IngressRule_HTTP" {
  security_group_id = aws_security_group.HelioCloud_Portal_UserSecurityGroup.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "HelioCloud_Portal_UserSecurityGroup_IngressRule_TCP_8000" {
  security_group_id = aws_security_group.HelioCloud_Portal_UserSecurityGroup.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8000
  ip_protocol       = "tcp"
  to_port           = 8000
}

resource "aws_cognito_identity_pool" "HelioCloud_Portal_IdentityPool" {
  identity_pool_name               = "IdentityPool"
  allow_unauthenticated_identities = true
  allow_classic_flow               = false

  cognito_identity_providers {
    client_id               = var.identity_provider_client_id
    provider_name           = var.identity_provider_name
    server_side_token_check = var.identity_provider_server_side_token_check
  }
}

resource "aws_iam_role" "HelioCloud_Portal_IdentityPool_AuthenticatedRole" {
  name        = "HelioCloud_Portal_IdentityPool_AuthenticatedRole"
  description = "Authenticated Role for HelioCloud Portal Identity Pool"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRoleWithWebIdentity"
      Effect    = "Allow"
      Principal = { Federated = "cognito-identity.amazonaws.com" }
      Condition = {
        StringEquals = {
          "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.HelioCloud_Portal_IdentityPool.id
        }
        "ForAnyValue:StringLike" = {
          "cognito-identity.amazonaws.com:amr" = "authenticated"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "HelioCloud_Portal_IdentityPool_AuthenticatedPolicy" {
  name   = "HelioCloud_Portal_IdentityPool_AuthenticatedPolicy"
  policy = local.iam_policy_document_json_IdentityPool_AuthenticatedPolicy
}

resource "aws_iam_role_policy_attachment" "HelioCloud_Portal_AuthenticatedPolicy_Attachment" {
  policy_arn = aws_iam_policy.HelioCloud_Portal_IdentityPool_AuthenticatedPolicy.arn
  role       = aws_iam_role.HelioCloud_Portal_IdentityPool_AuthenticatedRole.name
}

resource "aws_iam_role" "HelioCloud_Portal_IdentityPool_UnauthenticatedRole" {
  name        = "HelioCloud_Portal_IdentityPool_UnauthenticatedRole"
  description = "Unauthenticated Role for HelioCloud Portal Identity Pool"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRoleWithWebIdentity"
      Effect    = "Allow"
      Principal = { Federated = "cognito-identity.amazonaws.com" }
      Condition = {
        StringEquals = {
          "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.HelioCloud_Portal_IdentityPool.id
        }
        "ForAnyValue:StringLike" = {
          "cognito-identity.amazonaws.com:amr" = "unauthenticated"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "HelioCloud_Portal_IdentityPool_UnauthenticatedPolicy" {
  name   = "HelioCloud_Portal_IdentityPool_UnauthenticatedPolicy"
  policy = local.iam_policy_document_json_IdentityPool_UnauthenticatedPolicy
}

resource "aws_iam_role_policy_attachment" "HelioCloud_Portal_UnauthenticatedPolicy_Attachment" {
  policy_arn = aws_iam_policy.HelioCloud_Portal_IdentityPool_UnauthenticatedPolicy.arn
  role       = aws_iam_role.HelioCloud_Portal_IdentityPool_UnauthenticatedRole.name
}

resource "aws_cognito_identity_pool_roles_attachment" "HelioCloud_Portal_IdentityPool_RoleAttachment" {
  identity_pool_id = aws_cognito_identity_pool.HelioCloud_Portal_IdentityPool.id

  roles = {
    "authenticated"   = aws_iam_role.HelioCloud_Portal_IdentityPool_AuthenticatedRole.arn
    "unauthenticated" = aws_iam_role.HelioCloud_Portal_IdentityPool_UnauthenticatedRole.arn
  }
}
