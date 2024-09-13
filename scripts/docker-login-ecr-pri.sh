#!/bin/bash

AWS_ECR_REPOSITORY=$1
AWS_REGION=$2
if [[ "${AWS_ECR_REPOSITORY}" == "" ]]; then
    echo "error: AWS_ECR_REPOSITORY is unset"
    exit 1
fi
if [[ "${AWS_REGION}" == "" ]]; then
    echo "error: AWS_REGION is unset"
    exit 2
fi


aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ECR_REPOSITORY}
