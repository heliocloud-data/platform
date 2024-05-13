#!/bin/bash

NEW_VERSION=$1
if [[ "${NEW_VERSION}" == "" ]]; then
  echo "error: missing version"
  echo "usage: ${0} <ebs-csi-driver-version>"
  echo ""
  exit 1
fi

TARGET_STR=eksbuild

echo ${NEW_VERSION} | grep ${TARGET_STR} > /dev/null
if [[ $? != 0 ]]; then
  echo "error:  unable to find target string '${TARGET_STR}' in new version: '${NEW_VERSION}'"
  exit 1
fi

TARGET_DIR=daskhub/deploy/eksctl/base
TARGET_FILE=cluster-config.yaml

sed "s#version: .*${TARGET_STR}.*#version: ${NEW_VERSION}#" -i ${TARGET_DIR}/${TARGET_FILE}