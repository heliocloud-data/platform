variables {
  aws_region         = "us-east-1"
  aws_eks_az1        = "us-east-1a"
  aws_eks_az2        = "us-east-1b"
  cluster_name       = "tofu-test-helio"
  kubernetes_version = "1.21"
}

run "plan_root_module" {
  command = plan

  assert {
    condition     = aws_vpc.myvpc.cidr_block == "192.168.0.0/16"
    error_message = "Expected the root module to keep the default VPC CIDR."
  }

  assert {
    condition     = aws_eks_cluster.private.name == "tofu-test-helio"
    error_message = "Expected the configured cluster name to be passed into the EKS cluster."
  }

  assert {
    condition     = aws_eks_node_group.mng_daskhub_service.scaling_config[0].desired_size == 2
    error_message = "Expected the daskhub service node group to keep its baseline desired size of 2."
  }

  assert {
    condition     = aws_eks_node_group.mng_daskhub_service.instance_types[0] == "t3a.medium"
    error_message = "Expected the daskhub service node group instance type to remain t3a.medium."
  }
}
