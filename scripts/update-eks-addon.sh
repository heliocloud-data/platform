#!/bin/bash

ADDON_NAME=$1
NEW_VERSION=$2
if [[ "${ADDON_NAME}" == "" ]]; then
  echo "error: missing addon-name"
  echo "usage: ${0} <addon-name> <version>"
  exit 1
fi

if [[ "${NEW_VERSION}" == "" ]]; then
  echo "Attempting to auto-detected latest version of '${ADDON_NAME}'"
  NEW_VERSION=$(aws eks describe-addon-versions --addon-name ${ADDON_NAME} --query 'addons[0].addonVersions[*].addonVersion' --output text | sed 's#[[:space:]]#\n#g' | head -n 1)
  if [[ "${NEW_VERSION}" == "" ]]; then
    echo "error: missing version"
    echo "usage: ${0} <addon-name> <version>"
    echo ""
    exit 1
  fi
  echo "using: ${NEW_VERSION}"
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

# Re-generate the snapshots
export PYTHONPATH=.:test/unit
pytest -c pytest-unit.ini  --snapshot-update

# Re-run the tests
pytest -c pytest-unit.ini --debug --verbose


git add daskhub/deploy/eksctl/base/cluster-config.yaml
git add test/unit/resources/test_eksctl_templating/snapshots/test_eksctl_default.yaml

COMMIT_MSG="Update ${ADDON_NAME} to ${NEW_VERSION}"

TICKET_NO=$(git branch --show-current | grep --perl-regexp 'platform-(\d+)' | sed 's#platform-##')
if [[ $? == 0 ]]; then
  if [[ "${TICKET_NO}" != "" ]]; then
    COMMIT_MSG="heliocloud/platform#${TICKET_NO}: ${COMMIT_MSG}"
  fi
fi

git commit -m "${COMMIT_MSG}"
