#!/bin/bash

NAMESPACE='daskhub'
EKS_NAME='eks-helio'
KMS_NAME='helio-kms'

# Get region (should be in configure file after running 01-tools.sh)
# and availability zone
AWS_REGION=`aws configure get region`
AWS_AZ_PRIMARY=`aws ec2 describe-availability-zones --region $AWS_REGION --query "AvailabilityZones[0].ZoneName" --output text`
AWS_AZ_SECONDARY=`aws ec2 describe-availability-zones --region $AWS_REGION --query "AvailabilityZones[1].ZoneName" --output text`

# Get instance id associated with EC2 instance currently logged into
INSTANCE_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)

CLOUDFORMATION_ARN=$(aws ec2 describe-instances --region $AWS_REGION --instance-id $INSTANCE_ID --query "Reservations[0].Instances[0].Tags[?Key=='aws:cloudformation:stack-id'].Value | [0]" --output text)
CLOUDFORMATION_NAME=$(echo $CLOUDFORMATION_ARN | sed 's/^.*stack\///' | cut -d'/' -f1)

CLOUDFORMATION_RESOURCES=$(aws cloudformation describe-stack-resources --stack-name $CLOUDFORMATION_NAME)

# Create Key Management System alias if it doesn't exist
aws kms create-alias --alias-name alias/$KMS_NAME --target-key-id $(aws kms create-key --query KeyMetadata.Arn --output text)

KMS_ARN=`aws kms describe-key --key-id alias/$KMS_NAME --query KeyMetadata.Arn --output text`
echo ------------------------------
echo Created KMS key: $KMS_ARN


HELIO_S3_POLICY_ARN=$(aws cloudformation describe-stack-resources --stack-name $CLOUDFORMATION_NAME --logical-resource-id HelioS3Policy --query StackResources[0].PhysicalResourceId --output text)
K8S_ASG_POLICY_ARN=$(aws cloudformation describe-stack-resources --stack-name $CLOUDFORMATION_NAME --logical-resource-id K8AutoScalingPolicy --query StackResources[0].PhysicalResourceId --output text)

TEMP=$(aws sts get-caller-identity --query Arn --output text)
IAM_ROLE_NAME=$(echo $TEMP | sed 's/\/i-.*//' | rev | cut -d'/' -f1 | rev)
ADMIN_ROLE_ARN=$(aws iam get-role --role-name $IAM_ROLE_NAME --query 'Role.Arn' --output text)

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
    aws efs create-file-system \
        --creation-token $EKS_NAME \
        --performance-mode generalPurpose \
        --throughput-mode bursting \
        --encrypted \
        --backup \
        --availability-zone-name $AWS_AZ_PRIMARY \
        --tags Key=Name,Value=$EKS_NAME

    # Get EFS, subnet, and SG ids. Network has to be associated with EKS DNS
    EFS_ID=`aws efs  describe-file-systems --creation-token $EKS_NAME --query "FileSystems[0].FileSystemId" --output text`
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