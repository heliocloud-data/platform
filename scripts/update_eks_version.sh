#!/bin/bash
#
# This is a helper script that updates the Kubernetes version.

# Kubectl Download URL
#
# Example Value:
#   https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl
# See:
#   https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html
NEW_K8_VERSION=1.31
NEW_URL=https://s3.us-west-2.amazonaws.com/amazon-eks/1.31.0/2024-09-12/bin/linux/amd64/kubectl

NEW_CLUSTER_AUTOSCALER_VERSION=$(curl https://registry.k8s.io/v2/autoscaling/cluster-autoscaler/tags/list -L | jq '.[]'| grep v${NEW_K8_VERSION} | sed 's#[[:space:]]*"\(.*\)",*#\1#' | sort | uniq | tail -n 1)
if [[ $? != 0 ]]; then
  echo "error: unable to detect the new cluster autoscaler version"
  exit 1
fi

NEW_KUBE_SCHEDULER_VERSION=$(curl https://registry.k8s.io/v2/kube-scheduler/tags/list -L | jq '.[]'| grep v${NEW_K8_VERSION} | sed 's#[[:space:]]*"\(.*\)",*#\1#' | grep -v alpha | grep -v beta | grep -v rc | sort | uniq | tail -n 1)
if [[ $? != 0 ]]; then
  echo "error: unable to detect the new kube-scheduler"
  exit 1
fi

# EKS cluster config
echo "Updating file daskhub/deploy/eksctl/base/cluster-config.yaml..."
sed -i "s#^  version: \"1.*#  version: \"${NEW_K8_VERSION}\"#" daskhub/deploy/eksctl/base/cluster-config.yaml

# Update the cluster autoscaler version
echo "Updating file daskhub/deploy/kube-system/base/clusterautoscaler.yaml.j2..."
sed -i "s#registry.k8s.io/autoscaling/cluster-autoscaler:.*#registry.k8s.io/autoscaling/cluster-autoscaler:${NEW_CLUSTER_AUTOSCALER_VERSION}#" daskhub/deploy/kube-system/base/clusterautoscaler.yaml.j2

# Update the kube-scheduler version
echo "Updating file daskhub/deploy/daskhub/values.yaml.j2..."
sed -i "s#tag: v1..*#tag: ${NEW_KUBE_SCHEDULER_VERSION}#" daskhub/deploy/daskhub/values.yaml.j2

# Search for the Amazon EKS URL that's litered throughout the project.
for FILE in `grep -lr 's3.us-west-2.amazonaws.com/amazon-eks' | grep .sh | grep -v release | grep -v jhuapl-operations | grep -v cdk.out | grep -v temp | grep -v $0`; do
  echo "Updating file ${FILE}..."
  sed -i "s#https://s3.us-west-2.amazonaws.com/amazon-eks.*bin/linux/amd64/kubectl#${NEW_URL}#" ${FILE}
done

# Re-generate the snapshots
export PYTHONPATH=.:test/unit
pytest -c pytest-unit.ini  --snapshot-update

# Re-run the tests
pytest -c pytest-unit.ini --debug --verbose
