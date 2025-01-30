#!/bin/bash
#
# This is a helper script that updates the Kubernetes version.

# Kubectl Download URL
#
# Example Value:
#   https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl
# See:
#   https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html

NEW_VERSION=$1
SKIP_KUBECTL_URL_UPDATE=$2

if [[ "${SKIP_KUBECTL_URL_UPDATE}" != "true" ]]; then
  if [[ "${NEW_VERSION}" == "" ]]; then
    echo "Attempting to auto-detected latest version of 'kubernetes'"
    NEW_VERSION=$(aws eks describe-addon-versions --query "addons[*].addonVersions[*].compatibilities[*].clusterVersion" --output text |  sed 's#[[:space:]]#\n#g' | sort | uniq | tail -n 1)
    if [[ "${NEW_VERSION}" == "" ]]; then
      echo "error: missing version"
      echo "usage: ${0} <version>"
      echo ""
      exit 1
    fi
    echo "using: ${NEW_VERSION}"
  fi

  # Search for 
  python3 scripts/update-kubectl-download-url.py --target-k8-minor-version=${NEW_VERSION} --output-file=scripts/eks_version_info
  if [[ $? != 0 ]]; then
    echo "error: failed to detect the kubectl download url"
    echo ""
    exit 1
  fi
fi

source scripts/eks_version_info

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

git add .gitlab-ci/scripts/install-deps-kube.sh
git add daskhub/deploy/00-tools.sh
git add daskhub/deploy/daskhub/values.yaml.j2
git add daskhub/deploy/eksctl/base/cluster-config.yaml
git add daskhub/deploy/kube-system/base/clusterautoscaler.yaml.j2
git add scripts/eks_version_info
git add scripts/install-deps-kube.sh
git add test/unit/resources

COMMIT_MSG="Update Kubernetes to ${NEW_VERSION}"

TICKET_NO=$(git branch --show-current | grep --perl-regexp 'platform-(\d+)' | sed 's#platform-##')
if [[ $? == 0 ]]; then
  if [[ "${TICKET_NO}" != "" ]]; then
    COMMIT_MSG="heliocloud/platform#${TICKET_NO}: ${COMMIT_MSG}"
  fi
fi

git commit -m "${COMMIT_MSG}"
