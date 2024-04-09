#!/bin/bash
#
# The following script is responsible for deleting all EFS mount targets,
# which is an initial requirement before deploying daskhub.  The current
# implementation of the daskhub_stack, will create an EFS volume which
# automatically mounts it to the default VPC.
#
# There is a restriction that an EFS volume can only be mounted to one
# VPC at a time.  Because daskhub is deployed within a kubernetes cluster,
# it will reside within a different VPC, the EFS volume won't be reachable
# by daskhub without some intervention.
#
# The snippit below, will locate the EFSId attached as an output for the
# daskhub_stack CloudFormation template and remove all mount targets
# attached to it.  This should happen once, before any deployment is
# attempted.
#
# Author: Nicholas Lenzi

AWS_REGION=$(aws ec2 describe-availability-zones --output text --query 'AvailabilityZones[0].[RegionName]')

EFS_ID="<<CNF_OUTPUT_EFSId>>"

# Find EFS mounted targets not within the EKS VPC (this causes issues, can remove once VPC consistent across HelioCloud instance)
mounted_targets_to_delete=$(aws efs describe-mount-targets --file-system-id $EFS_ID --query "MountTargets[*].MountTargetId" --output text)
IFS=' ' read -a arr <<< "$mounted_targets_to_delete"
sorted_unique_mounted_targets=($(echo "${arr[@]}" | tr ' ' '\n' | sort -u  | tr '\n' ' '))

for i in "${sorted_unique_mounted_targets[@]}"
do
    echo Removing EFS mounted target $i that is not within VPC
    aws efs delete-mount-target --region $AWS_REGION --mount-target-id $i
done

# Deleting a mount target does not happen immediately, the next snippit
# will poll the AWS CLI until it gets confirmation that all EFS mount targets
# for this EFSId have been removed.
while [[ -n "$mounted_targets_to_delete" ]]
do
    sleep 20s
    mounted_targets_to_delete=$(aws efs describe-mount-targets --file-system-id $EFS_ID --query "MountTargets[*].MountTargetId" --output text)
done
