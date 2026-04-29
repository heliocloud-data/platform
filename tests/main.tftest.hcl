# Covers: root-stack integration wiring with a minimal realistic variable set.
# Mode: plan only with refresh disabled.
# Real AWS resources: no creates, but provider/data-source access may still be required.
# Intended use: regular CI after smoke tests or pre-merge verification.

variables {
    aws_region          = "us-east-1"
    cluster_name        = "test-cluster"
    kubernetes_version  = "1.29"
    aws_eks_az1         = "us-east-1a"
    aws_eks_az2         = "us-east-1b"
    cognito_callback_urls = ["https://example.com/callback"]
    cognito_logout_urls   = ["https://example.com/logout"]
    tags = {
      Environment = "test"
    }
  }

run "plan_basic_infra" {
  command = plan

  

  assert {
    condition = aws_vpc.myvpc.cidr_block == "192.168.0.0/16"
    error_message = "VPC CIDR block is incorrect"
  }

  assert {
    condition = aws_subnet.subnet_private_01.id != ""
    error_message = "Private subnet 01 not created"
  }

  assert {
    condition = length(aws_subnet.subnet_public_01.id) > 0
    error_message = "Public subnet 01 not created"
  }

  assert {
    condition = aws_eks_cluster.private.name == var.cluster_name
    error_message = "EKS cluster name mismatch"
  }

  assert {
    condition = aws_eks_cluster.private.vpc_config[0].endpoint_public_access == true
    error_message = "EKS public endpoint should be enabled"
  }

  assert {
    condition = aws_eks_node_group.mng_daskhub_service.scaling_config[0].desired_size == 2
    error_message = "Node group desired size should be 2"
  }
}
