# This node group is responsible for hosting the "user" jupyterhub servers that are
# small.  Schedule on can is done via the following:
#
#  taint/toleration(s)
#   * hub.jupyter.org/dedicated=user:NoSchedule
resource "aws_eks_node_group" "mng_jupyterhub_user_compute" {
  cluster_name    = var.cluster_name
  node_group_name = "mng_jupyterhub_user_compute"
  node_role_arn   = var.node_role_arn

  subnet_ids = var.subnet_ids

  instance_types = ["m5.2xlarge"]

  scaling_config {
    desired_size = 0
    min_size     = 0
    max_size     = 15
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    lifecycle                      = "OnDemand"
    intent                         = "apps"
    "nvidia.com/gpu"               = "false"
    "node-purpose"                 = "user"
    "hub.jupyter.org/node-purpose" = "user"
  }

  taint {
    key    = "hub.jupyter.org/dedicated"
    value  = "user"
    effect = "NO_SCHEDULE"
  }

  tags = {
    "k8s.io/cluster-autoscaler/node-template/label/lifecycle"                    = "OnDemand"
    "k8s.io/cluster-autoscaler/node-template/label/intent"                       = "apps"
    "k8s.io/cluster-autoscaler/node-template/label/nvidia.com/gpu"               = "false"
    "k8s.io/cluster-autoscaler/node-template/label/node-purpose"                 = "user"
    "k8s.io/cluster-autoscaler/node-template/label/hub.jupyter.org/node-purpose" = "user"
    "k8s.io/cluster-autoscaler/node-template/taint/hub.jupyter.org/dedicated"    = "user:NoSchedule"
  }

}

# This node group is responsible for hosting the "user" jupyterhub servers that are
# large.  Schedule on can is done via the following:
#
#  taint/toleration(s)
#   * hub.jupyter.org/dedicated=big-user:NoSchedule
resource "aws_eks_node_group" "mng_jupyterhub_user_compute_big" {
  cluster_name    = var.cluster_name
  node_group_name = "mng_jupyterhub_user_compute_big"
  node_role_arn   = var.node_role_arn

  subnet_ids = var.subnet_ids

  instance_types = ["m5.4xlarge"]

  scaling_config {
    desired_size = 0
    min_size     = 0
    max_size     = 15
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    lifecycle                      = "OnDemand"
    intent                         = "apps"
    "nvidia.com/gpu"               = "false"
    "node-purpose"                 = "user"
    "hub.jupyter.org/node-purpose" = "user"
    "heliocloud.org/instance-type" = "4xlarge"
  }

  taint {
    key    = "hub.jupyter.org/dedicated"
    value  = "big-user"
    effect = "NO_SCHEDULE"
  }

  tags = {
    "k8s.io/cluster-autoscaler/node-template/label/lifecycle"                    = "OnDemand"
    "k8s.io/cluster-autoscaler/node-template/label/intent"                       = "apps"
    "k8s.io/cluster-autoscaler/node-template/label/nvidia.com/gpu"               = "false"
    "k8s.io/cluster-autoscaler/node-template/label/node-purpose"                 = "user"
    "k8s.io/cluster-autoscaler/node-template/label/hub.jupyter.org/node-purpose" = "user"
    "k8s.io/cluster-autoscaler/node-template/label/heliocloud.org/instance-type" = "4xlarge"
    "k8s.io/cluster-autoscaler/node-template/taint/hub.jupyter.org/dedicated"    = "big-user:NoSchedule"
  }

}

# This node group is responsible for hosting the "user" jupyterhub servers that have
# GPUs.  Schedule on can is done via the following:
#
#  affinity (any)
#   * heliocloud.org/instance-type: [2xlarge, 4xlarge]
#  taint/toleration(s)
#   * nvidia.com/gpu=true:NoSchedule
#   * hub.jupyter.org/dedicated=user:NoSchedule
resource "aws_eks_node_group" "mng_jupyterhub_user_compute_gpu_2xlarge" {
  cluster_name    = var.cluster_name
  node_group_name = "mng_jupyterhub_user_compute_gpu_2xlarge"
  node_role_arn   = var.node_role_arn

  subnet_ids = var.subnet_ids

  instance_types = ["g4dn.2xlarge"]

  scaling_config {
    desired_size = 0
    min_size     = 0
    max_size     = 4
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    lifecycle                       = "OnDemand"
    intent                          = "apps"
    "nvidia.com/gpu"                = "true"
    "k8s.amazonaws.com/accelerator" = "nvidia-tesla-t4"
    "node-purpose"                  = "user"
    "hub.jupyter.org/node-purpose"  = "user"
    "heliocloud.org/instance-type"  = "2xlarge"
  }

  taint {
    key    = "nvidia.com/gpu"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  taint {
    key    = "hub.jupyter.org/dedicated"
    value  = "user"
    effect = "NO_SCHEDULE"
  }

  tags = {
    "k8s.io/cluster-autoscaler/node-template/label/lifecycle"                    = "OnDemand"
    "k8s.io/cluster-autoscaler/node-template/label/intent"                       = "apps"
    "k8s.io/cluster-autoscaler/node-template/label/nvidia.com/gpu"               = "false"
    "k8s.io/cluster-autoscaler/node-template/label/node-purpose"                 = "user"
    "k8s.io/cluster-autoscaler/node-template/label/hub.jupyter.org/node-purpose" = "user"
    "k8s.io/cluster-autoscaler/node-template/label/heliocloud.org/instance-type" = "2xlarge"
    "k8s.io/cluster-autoscaler/node-template/taint/nvidia.com/gpu"               = "true:NoSchedule"
    "k8s.io/cluster-autoscaler/node-template/taint/hub.jupyter.org/dedicated"    = "user:NoSchedule"
  }

}
