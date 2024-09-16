#!/bin/bash
#
# Deletes all Elastic File Systems in the given region

AWS_REGION=$1
if [[ "${AWS_REGION}" == "" ]]; then
    echo "error: AWS_REGION is unset"
    exit 1
fi

echo "Deleting all left-over Elastic File Systems (EFS) in region ${AWS_REGION}, if this is not what you want, you have 5 seconds to abort this operation"
sleep 5

RES=$(aws efs describe-file-systems --region ${AWS_DEFAULT_REGION} \
        --query 'FileSystems[?NumberOfMountTargets==`0`].FileSystemId' \
        --output text)

RET=$?
if [[ $RET != 0 ]]; then
    echo "error: Unexpected error from aws cli"
    exit $RET
fi

if [[ "$RES" != "" ]]; then
    aws efs describe-file-systems --region ${AWS_DEFAULT_REGION} \
        --query 'FileSystems[?NumberOfMountTargets==`0`].FileSystemId' \
        --output text | \
        sed 's#[[:space:]]#\n#g' | \
        xargs -n 1 aws efs delete-file-system --region ${AWS_DEFAULT_REGION}  --file-system-id
fi