#!/bin/bash

AWS_ECR_REPOSITORY=$1
if [[ "${AWS_ECR_REPOSITORY}" == "" ]]; then
    echo "error: AWS_ECR_REPOSITORY is unset"
    exit 1
fi


aws ecr-public get-login-password | docker login --username AWS --password-stdin ${AWS_ECR_REPOSITORY}
