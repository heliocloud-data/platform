# HelioCloud Portal Module Tests

variables {
  cluster_name                              = "tofu-cluster"
  kubernetes_namespace                      = "default"
  kubernetes_service_account                = "portal-sa"
  aws_az1                                   = "us-east-1a"
  aws_az2                                   = "us-east-1b"
  identity_provider_client_id               = "client_id"
  identity_provider_name                    = "provider-name"
  identity_provider_server_side_token_check = true
}

run "plan_portal" {
  command = plan

  plan_options {
    refresh = false
  }

  # --- VPC ---
  assert {
    condition     = aws_vpc.HelioCloud_Portal_VPC.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR block mismatch."
  }

  # --- Subnets ---
  assert {
    condition     = aws_subnet.HelioCloud_Portal_Subnet_Public_01.map_public_ip_on_launch
    error_message = "Public subnet 01 should map public IPs."
  }

  assert {
    condition     = aws_subnet.HelioCloud_Portal_Subnet_Public_02.map_public_ip_on_launch
    error_message = "Public subnet 02 should map public IPs."
  }

  # --- IAM Role ---
  assert {
    condition     = aws_iam_role.HelioCloud_Portal_UserRole.name == "PortalEc2Role"
    error_message = "User role name mismatch."
  }

  # --- Pod Identity ---
  assert {
    condition     = aws_eks_pod_identity_association.HelioCloud_Portal_PodIdentityAssociation.cluster_name == "tofu-cluster"
    error_message = "Pod identity should reference correct cluster."
  }

  # --- Security Group ---
  assert {
    condition     = aws_security_group.HelioCloud_Portal_UserSecurityGroup.name == "PortalEc2SecurityGroup"
    error_message = "Security group name mismatch."
  }

  # --- Cognito Identity Pool ---
  assert {
    condition     = aws_cognito_identity_pool.HelioCloud_Portal_IdentityPool.allow_unauthenticated_identities
    error_message = "Identity pool should allow unauthenticated identities."
  }

  # --- Identity Pool Roles ---
  assert {
    condition     = aws_iam_role.HelioCloud_Portal_IdentityPool_AuthenticatedRole.name == "HelioCloud_Portal_IdentityPool_AuthenticatedRole"
    error_message = "Authenticated role name mismatch."
  }

  assert {
    condition     = aws_iam_role.HelioCloud_Portal_IdentityPool_UnauthenticatedRole.name == "HelioCloud_Portal_IdentityPool_UnauthenticatedRole"
    error_message = "Unauthenticated role name mismatch."
  }
}
