#!/bin/bash

AWS_REGION=$(aws ec2 describe-availability-zones --output text --query 'AvailabilityZones[0].[RegionName]')

source ./app.config

helm uninstall daskhub --namespace $KUBERNETES_NAMESPACE

LOADBALANCER_URL=$(kubectl --namespace=$KUBERNETES_NAMESPACE get svc proxy-public --output jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo ------------------------------
echo Ping for loadbalancer address to ensure daskhub uninstalled...
while [[ $LOADBALANCER_URL == *.com ]]
do
    sleep 20s
    echo Still exists, waiting another 20 seconds
    LOADBALANCER_URL=$(kubectl --namespace=$KUBERNETES_NAMESPACE get svc proxy-public --output jsonpath='{.status.loadBalancer.ingress[0].hostname}')
done

echo ------------------------------
echo Daskhub helm chart uninstalled...

# Get instance id associated with EC2 instance currently logged into
INSTANCE_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)

CLOUDFORMATION_ARN=$(aws ec2 describe-instances --region $AWS_REGION --instance-id $INSTANCE_ID --query "Reservations[0].Instances[0].Tags[?Key=='aws:cloudformation:stack-id'].Value | [0]" --output text)
CLOUDFORMATION_NAME=$(echo $CLOUDFORMATION_ARN | sed 's/^.*stack\///' | cut -d'/' -f1)

EFS_ID=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`EFSId`].OutputValue' --output text)
EKS_VPC=`aws eks describe-cluster --name $EKS_NAME --query cluster.resourcesVpcConfig.vpcId --output text`
EFS_VPC=\"${EFS_VPC}\"

echo ------------------------------
echo Finding EFS mounted targets within VPC
# Find EFS mounted targets within the EKS VPC (cannot delete cluster if there is a remaining connection)
mounted_targets_to_delete=$(aws efs describe-mount-targets --file-system-id $EFS_ID --query "MountTargets[?VpcId == '$EKS_VPC'].MountTargetId" --output text)
IFS=' ' read -a arr <<< "$mounted_targets_to_delete"
sorted_unique_mounted_targets=($(echo "${arr[@]}" | tr ' ' '\n' | sort -u  | tr '\n' ' '))

echo ------------------------------
for i in "${sorted_unique_mounted_targets[@]}"
do
    echo Removing EFS mounted target $i that is within cluster VPC
    aws efs delete-mount-target --region $AWS_REGION --mount-target-id $i
done

# Make sure deleted mounted targets have enough time to be deleted from system
while [[ -n "$mounted_targets_to_delete" ]]
do
    sleep 20s
    mounted_targets_to_delete=$(aws efs describe-mount-targets --file-system-id $EFS_ID --query 'MountTargets[?VpcId!=`$EKS_VPC`].MountTargetId' --output text)
done

echo ------------------------------
echo Checking cluster status and deleting...
init_cluster_query=$(aws eks list-clusters | jq -r '.clusters[]')

if [[ " ${init_cluster_query[*]} " =~ " ${EKS_NAME} " ]]; then
    eksctl delete cluster --name $EKS_NAME
fi

echo ------------------------------
echo Checking cluster status after deleting...
init_cluster_query=$(aws eks list-clusters | jq -r '.clusters[]')
iterator=0
while [[ " ${init_cluster_query[*]} " =~ " ${EKS_NAME} " ]]
do
    if [[ $iterator -gt 60 ]]; then
      echo Breaking due to exceeding time, check if cluster actually deleted
      break
    fi

    sleep 30s
    echo Still exists, waiting another 30 seconds
    init_cluster_query=$(aws eks list-clusters | jq -r '.clusters[]')
    iterator=$((iterator + 1))
    echo $iterator
done

echo ------------------------------
echo Cluster delete complete!