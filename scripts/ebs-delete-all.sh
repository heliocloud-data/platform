#!/bin/bash
#
# Deletes all EBS volumes in the given region

AWS_REGION=$1
if [[ "${AWS_REGION}" == "" ]]; then
    echo "error: AWS_REGION is unset"
    exit 1
fi

echo "Deleting all left-over EBS volumes in region ${AWS_REGION}, if this is not what you want, you have 5 seconds to abort this operation"
sleep 5

RES=$(aws ec2 describe-volumes --region ${AWS_REGION} \
    --query 'Volumes[*].VolumeId' \
    --output text)

RET=$?
if [[ $RET != 0 ]]; then
    echo "error: Unexpected error from aws cli"
    exit $RET
fi

if [[ "$RES" != "" ]]; then
    aws ec2 describe-volumes --region ${AWS_REGION} \
        --query 'Volumes[*].VolumeId' \
        --output text | \
        sed 's#[[:space:]]#\n#g' | \
        xargs -n 1 aws ec2 delete-volume  --region ${AWS_REGION} --volume-id
fi
