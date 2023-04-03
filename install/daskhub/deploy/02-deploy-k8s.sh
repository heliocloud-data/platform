#!/bin/bash

AWS_REGION=$(curl -s curl http://169.254.169.254/latest/meta-data/placement/region)

aws configure set output json
aws configure set region $AWS_REGION

NAMESPACE='daskhub'
EKS_NAME='eks-helio'

# Get region (should be in configure file after running 01-tools.sh)
# and availability zone
#AWS_REGION=`aws configure get region`
AWS_AZ_PRIMARY=`aws ec2 describe-availability-zones --region $AWS_REGION --query "AvailabilityZones[0].ZoneName" --output text`
AWS_AZ_SECONDARY=`aws ec2 describe-availability-zones --region $AWS_REGION --query "AvailabilityZones[1].ZoneName" --output text`

# Get instance id associated with EC2 instance currently logged into
INSTANCE_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)

CLOUDFORMATION_ARN=$(aws ec2 describe-instances --region $AWS_REGION --instance-id $INSTANCE_ID --query "Reservations[0].Instances[0].Tags[?Key=='aws:cloudformation:stack-id'].Value | [0]" --output text)
CLOUDFORMATION_NAME=$(echo $CLOUDFORMATION_ARN | sed 's/^.*stack\///' | cut -d'/' -f1)

#CLOUDFORMATION_RESOURCES=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME)
KMS_ARN=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`KMSArn`].OutputValue' --output text)
K8S_ASG_POLICY_ARN=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`ASGArn`].OutputValue' --output text)
HELIO_S3_POLICY_ARN=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`CustomS3Arn`].OutputValue' --output text)
ADMIN_ROLE_ARN=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`AdminRoleArn`].OutputValue' --output text)
EFS_ID=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`EFSId`].OutputValue' --output text)

echo ------------------------------
echo Checking cluster status...
init_cluster_query=$(aws eks list-clusters | jq -r '.clusters[]')
if [[ " ${init_cluster_query[*]} " =~ " ${EKS_NAME} " ]]; then
    echo Cluster - $EKS_NAME - already exists, skipping cluster creation
else
    echo ------------------------------
    echo Cluster - $EKS_NAME - needs to be created, starting process...

    echo ------------------------------
    echo Setting up cluster configuration...
    cp cluster-config.yaml.template cluster-config.yaml

    sed -i "s|<INSERT_EKS_NAME>|$EKS_NAME|g" cluster-config.yaml
    sed -i "s|<INSERT_KMS_ARN>|$KMS_ARN|g" cluster-config.yaml
    sed -i "s|<INSERT_REGION>|$AWS_REGION|g" cluster-config.yaml
    sed -i "s|<INSERT_PRIMARY_AVAILABILITY_ZONE>|$AWS_AZ_PRIMARY|g" cluster-config.yaml
    sed -i "s|<INSERT_SECONDARY_AVAILABILITY_ZONE>|$AWS_AZ_SECONDARY|g" cluster-config.yaml
    sed -i "s|<INSERT_helio-s3-policy_ARN>|$HELIO_S3_POLICY_ARN|g" cluster-config.yaml
    sed -i "s|<INSERT_k8s-asg-policy_ARN>|$K8S_ASG_POLICY_ARN|g" cluster-config.yaml

    echo ------------------------------
    echo Removing instance types not present in $AWS_REGION from cluster configuration...
    all_config_instance_types=$(grep -n "instanceTypes" cluster-config.yaml | cut -d':' -f 3 | tr '\n' ','| tr -d "]" | tr -d "[" | tr "," "|" | tr -d ' ' | tr -d '"' | tr "|" " ")
    IFS=' ' read -a arr <<< "$all_config_instance_types"
    sorted_unique_instance_types=($(echo "${arr[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

    all_aws_region_instance_types=$(aws ec2 describe-instance-types --query InstanceTypes[].InstanceType | tr "," "|" | tr -d "\n" | tr -d '"' | tr -d "[" | tr -d "]" | tr -d " " | tr "|" " ")
    IFS=' ' read -a aws_arr <<< "$all_aws_region_instance_types"
    sorted_unique_aws_instance_types=($(echo "${aws_arr[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

    missing_instance_types=$(echo ${sorted_unique_aws_instance_types[@]} ${sorted_unique_instance_types[@]} | sed 's/ /\n/g' | sort | uniq -d | xargs echo ${sorted_unique_instance_types[@]} | sed 's/ /\n/g' | sort | uniq -u)
    instances_to_replace=($missing_instance_types)

    for i in "${instances_to_replace[@]}"
    do
        echo Removing instance type $i from cluster-config.yaml does not exist in $AWS_REGION
    	sed -i "s|\"$i\"\,||g" cluster-config.yaml
        sed -i "s|\"$i\"||g" cluster-config.yaml
    done

    echo ------------------------------
    echo Creating Kubernetes cluster...  
    eksctl create cluster -f cluster-config.yaml
fi

echo ------------------------------
echo Verifying cluster status...
final_cluster_query=$(aws eks list-clusters | jq -r '.clusters[]')
if [[ " ${final_cluster_query[*]} " =~ " ${EKS_NAME} " ]]; then
    echo Cluster - $EKS_NAME - created, continuing...

    echo ------------------------------
    echo Creating cluster admin user...
    eksctl create iamidentitymapping --cluster $EKS_NAME --arn $ADMIN_ROLE_ARN --group system:masters --username admin --region $AWS_REGION

    echo ------------------------------
    echo Creating EFS with mounted target...
    # Creates Elastic File System (EFS) - creation token ensures that there is only
    # one EFS created in case this file is executed multiple times

    # Get EFS, subnet, and SG ids. Network has to be associated with EKS DNS
    SUBNET_IDS=`aws eks describe-cluster --name $EKS_NAME --region $AWS_REGION --query cluster.resourcesVpcConfig.subnetIds --output text`
    SG_ID=`aws eks describe-cluster --name $EKS_NAME --region $AWS_REGION --query cluster.resourcesVpcConfig.clusterSecurityGroupId --output text`

    SUBNET_ID=`aws ec2 describe-subnets --subnet-ids $SUBNET_IDS --filters "Name=availability-zone,Values=$AWS_AZ_PRIMARY" --query "Subnets[0].SubnetId" --output text`

    # Attaches mount target to newly created EFS
    aws efs create-mount-target \
        --file-system-id $EFS_ID \
        --subnet-id $SUBNET_ID \
        --security-groups $SG_ID 

    echo ------------------------------
    echo Setting up persistent volume configuration...
    cp efs-pv.yaml.template efs-pv.yaml

    sed -i "s|<INSERT_EKS_DNS_NAME>|$EFS_ID.efs.$AWS_REGION.amazonaws.com|g" efs-pv.yaml


    echo ------------------------------
    echo Attaching autoscaling to cluster...
    # Creates autoscaling for cluster
    cp clusterautoscaler.yaml.template clusterautoscaler.yaml
    sed -i "s|<INSERT_EKS_NAME>|$EKS_NAME|g" clusterautoscaler.yaml
    kubectl apply -f clusterautoscaler.yaml

    kubectl -n kube-system \
        annotate --overwrite deployment.apps/cluster-autoscaler \
        cluster-autoscaler.kubernetes.io/safe-to-evict="false"

    ##### Below this specific to namespace #####
    kubectl create namespace $NAMESPACE

    echo ------------------------------ 
    echo Attaching same service role of default namespace to desired namespace
    eksctl create iamserviceaccount \
        --name helio-dh-role \
        --namespace $NAMESPACE \
        --cluster $EKS_NAME \
        --attach-policy-arn $HELIO_S3_POLICY_ARN \
        --approve \
        --override-existing-serviceaccounts


    echo ------------------------------
    echo Attaching persistent volume to cluster...
    # Creates Elastic File System on K8s
    kubectl -n $NAMESPACE apply -f efs-pvc.yaml
    kubectl -n $NAMESPACE apply -f efs-pv.yaml
else
    echo ------------------------------
    echo ERROR: Cluster - $EKS_NAME - was not created, skipped all subsequent steps, debug required!
fi

# Setup Daskhub configuration files (copy templates and add API keys to secrets)
API_KEY1=$(openssl rand -hex 32)
API_KEY2=$(openssl rand -hex 32)

cp dh-secrets.yaml.template dh-secrets.yaml

sed -i "s|<INSERT_API_KEY1>|$API_KEY1|g" dh-secrets.yaml
sed -i "s|<INSERT_API_KEY2>|$API_KEY2|g" dh-secrets.yaml

cp dh-config.yaml.template dh-config.yaml
cp dh-auth.yaml.template dh-auth.yaml

# Add helm repo
helm repo add dask https://helm.dask.org/