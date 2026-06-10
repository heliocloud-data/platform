# HelioCloud EKS JupyterHub User Compute Node Group Tests

# Fake AWS provider to allow plan without real credentials
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "mock"
  secret_key                  = "mock"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

variables {
  cluster_name  = "tofu-cluster"
  node_role_arn = "arn:aws:iam::123456789012:role/test-role"
  subnet_ids    = ["subnet-123", "subnet-456"]
}

run "plan_nodegroups" {
  command = plan

  plan_options {
    refresh = false
  }

  # --- small user nodes ---
  assert {
    condition     = aws_eks_node_group.mng_jupyterhub_user_compute.node_group_name == "mng_jupyterhub_user_compute"
    error_message = "Small node group name mismatch."
  }

  assert {
    condition     = aws_eks_node_group.mng_jupyterhub_user_compute.scaling_config[0].max_size == 15
    error_message = "Small node group max size should be 15."
  }

  assert {
    condition     = aws_eks_node_group.mng_jupyterhub_user_compute.labels["node-purpose"] == "user"
    error_message = "Small node group should be labeled for user workloads."
  }

  # --- big user nodes ---
  assert {
    condition     = aws_eks_node_group.mng_jupyterhub_user_compute_big.instance_types[0] == "m5.4xlarge"
    error_message = "Big node group instance type mismatch."
  }

  assert {
    condition     = aws_eks_node_group.mng_jupyterhub_user_compute_big.labels["heliocloud.org/instance-type"] == "4xlarge"
    error_message = "Big node group instance label incorrect."
  }

  # --- GPU nodes ---
  assert {
    condition     = aws_eks_node_group.mng_jupyterhub_user_compute_gpu_2xlarge.instance_types[0] == "g4dn.2xlarge"
    error_message = "GPU node group instance type mismatch."
  }

  assert {
    condition     = aws_eks_node_group.mng_jupyterhub_user_compute_gpu_2xlarge.labels["nvidia.com/gpu"] == "true"
    error_message = "GPU node group must have GPU label."
  }

  assert {
    condition     = aws_eks_node_group.mng_jupyterhub_user_compute_gpu_2xlarge.scaling_config[0].max_size == 4
    error_message = "GPU node group max size should be 4."
  }
}
