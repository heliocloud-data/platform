#!/bin/bash
#
# The following script is responsible for standing up an EKS cluster
# and install the required kube-system and monitoring tools to support
# a subsequent HelioCloud/Daskhub deployment.
#
# Author: Nicholas Lenzi

AWS_REGION=$(aws ec2 describe-availability-zones --output text --query 'AvailabilityZones[0].[RegionName]')

aws configure set output json
aws configure set region $AWS_REGION


# The following command will create an eks cluster based on the configuration.
# This command can only be run once.  It is possible to run an upgrade using
# this configuration file, but only the control plane and nodegroups will be
# updated.
#
# The following command is an easy way to determine if the cluster exists.
#    eksctl get cluster --region us-west-2 --name eks-helio
#
# The following command can perform an update on an existing cluster:
#    kustomize build eksctl/overlays/production > eksctl/eksctl-kustomize.yaml && \
#        eksctl upgrade cluster -f eksctl/eksctl-kustomize.yaml --approve
#
# See:
#   https://stackoverflow.com/questions/68470318/how-to-parameterize-the-config-file-for-eksctl
kustomize build eksctl/overlays/production > eksctl/eksctl-kustomize.yaml && \
    eksctl create cluster -f eksctl/eksctl-kustomize.yaml
RET=$?
if [[ $RET != 0 ]]; then
    echo "error: failed to deploy eks cluster"
    exit 1
fi


# The following command will register any iamidentitymappings configured in the heliocloud
# instance configuration.
kustomize build eksctl-iamidentitymappings/overlays/production > eksctl-iamidentitymappings/iamidentitymappings-kustomize.yaml && \
    eksctl create iamidentitymapping -f eksctl-iamidentitymappings/iamidentitymappings-kustomize.yaml
RET=$?
if [[ $RET != 0 ]]; then
    echo "error: failed to deploy eks iamidentitymappings"
    exit 1
fi

# Within this step, we'll be deploying the `cluster-autoscaler` and some
# additional `RoleBindings` required to administer an EKS cluster from
# the AWS console.
#
# Failure to execute this step, will result in a cluster that will
# be unable to scale up based on load.
kustomize build kube-system/base | kubectl apply -f -

# Within this step, we'll be deploying the `amazon-cloudwatch` namespace,
# which handles log aggregation and the pod and node level.  When enabled,
# these logs will be available from the AWS console at CloudWatch.
#
# This step can be skipped if log aggregation or live monitoring is not
# needed.
kustomize build amazon-cloudwatch/overlays/production | kubectl apply -f -
