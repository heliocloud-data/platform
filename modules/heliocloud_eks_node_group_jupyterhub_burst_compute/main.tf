data "aws_ec2_instance_type_offerings" "mng_jupyterhub_burst_compute_instance_types" {
  filter {
    name   = "instance-type"
    values = var.mng_jupyterhub_burst_compute_instance_types
  }

  location_type = "region"
}

data "aws_ec2_instance_type_offerings" "mng_jupyterhub_burst_compute_gpu_xlarge_instance_types" {
  filter {
    name   = "instance-type"
    values = var.mng_jupyterhub_burst_compute_gpu_xlarge_instance_types
  }

  location_type = "region"
}

# This node group is responsible for hosting the burst jobs "user" created by "dask" jobs.
# At the moment it's not entirely clear why this node group is selected, as historically
# no affinity/anti-affinity settings are applied to task.  Theoretically, is can be schedule
# via the following:
#
#  affinity (any)
#   * heliocloud.org/dask-worker=true
#   * nvidia.com/gpu=false
#  taint/toleration(s)
#   * heliocloud.org/dask-worker-profile=gpu-xlarge:NoSchedule
resource "aws_eks_node_group" "mng_jupyterhub_burst_compute" {
  cluster_name    = var.cluster_name
  node_group_name = "mng_jupyterhub_burst_compute"
  node_role_arn   = var.node_role_arn

  ami_type  = "AL2023_x86_64_STANDARD"
  disk_size = 80

  subnet_ids = var.subnet_ids

  instance_types = data.aws_ec2_instance_type_offerings.mng_jupyterhub_burst_compute_instance_types.instance_types

  scaling_config {
    desired_size = 0
    min_size     = 0
    max_size     = 10
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    lifecycle                    = "Ec2Spot"
    intent                       = "apps"
    "nvidia.com/gpu"             = "false"
    "aws.amazon.com/spot"        = "true"
    "heliocloud.org/dask-worker" = "true"
  }

  taint {
    key    = "heliocloud.org/dask-worker-profile"
    value  = "default"
    effect = "NO_SCHEDULE"
  }

  tags = {
    "k8s.io/cluster-autoscaler/node-template/label/lifecycle"                          = "Ec2Spot"
    "k8s.io/cluster-autoscaler/node-template/label/intent"                             = "apps"
    "k8s.io/cluster-autoscaler/node-template/label/nvidia.com/gpu"                     = "false"
    "k8s.io/cluster-autoscaler/node-template/label/aws.amazon.com/spot"                = "true"
    "k8s.io/cluster-autoscaler/node-template/label/heliocloud.org/dask-worker"         = "true"
    "k8s.io/cluster-autoscaler/node-template/taint/heliocloud.org/dask-worker-profile" = "default:NoSchedule"
  }

}



# This node group is responsible for hosting the burst jobs "user" created by "dask" jobs.
# At the moment it's not entirely clear why this node group is selected, as historically
# no affinity/anti-affinity settings are applied to task.  Theoretically, is can be schedule
# via the following:
#
#  affinity (any)
#   * heliocloud.org/dask-worker=true
#   * nvidia.com/gpu=false
#  taint/toleration(s)
#   * heliocloud.org/dask-worker-profile=gpu-xlarge:NoSchedule
resource "aws_eks_node_group" "mng_jupyterhub_burst_compute_gpu_xlarge" {
  cluster_name    = var.cluster_name
  node_group_name = "mng_jupyterhub_burst_compute_gpu_xlarge"
  node_role_arn   = var.node_role_arn

  ami_type  = "AL2023_x86_64_NVIDIA"
  disk_size = 80

  subnet_ids = var.subnet_ids

  instance_types = data.aws_ec2_instance_type_offerings.mng_jupyterhub_burst_compute_gpu_xlarge_instance_types.instance_types

  scaling_config {
    desired_size = 0
    min_size     = 0
    max_size     = 10
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    lifecycle                       = "Ec2Spot"
    intent                          = "apps"
    "nvidia.com/gpu"                = "true"
    "k8s.amazonaws.com/accelerator" = "nvidia-tesla-t4"
    "aws.amazon.com/spot"           = "true"
    "heliocloud.org/dask-worker"    = "true"
  }

  taint {
    key    = "heliocloud.org/dask-worker-profile"
    value  = "gpu-xlarge"
    effect = "NO_SCHEDULE"
  }

  tags = {
    "k8s.io/cluster-autoscaler/node-template/label/lifecycle"                          = "Ec2Spot"
    "k8s.io/cluster-autoscaler/node-template/label/intent"                             = "apps"
    "k8s.io/cluster-autoscaler/node-template/label/nvidia.com/gpu"                     = "true"
    "k8s.io/cluster-autoscaler/node-template/label/k8s.amazonaws.com/accelerator"      = "nvidia-tesla-t4"
    "k8s.io/cluster-autoscaler/node-template/label/aws.amazon.com/spot"                = "true"
    "k8s.io/cluster-autoscaler/node-template/label/heliocloud.org/dask-worker"         = "true"
    "k8s.io/cluster-autoscaler/node-template/taint/heliocloud.org/dask-worker-profile" = "gpu-xlarge:NoSchedule"

  }

}
