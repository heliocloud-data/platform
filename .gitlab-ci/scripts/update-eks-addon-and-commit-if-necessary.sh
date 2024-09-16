#!/bin/bash

git checkout -b ${INTEGRATION_BRANCH}

if [[ $? == 0 ]]; then
  # We're going to need the aws-cli, kustomize and, helm (for the snapshot unit tests)
  bash scripts/install-deps-no_sudo.sh
  python -m pip install -r requirements.txt
  python -m pip install -r requirements-dev.txt

  # Run the update addon script, it will make commits to perform the upgrade
  bash ./scripts/update-eks-addon.sh ${ADDON_NAME}

  git status | grep 'Your branch is up to date with'
  if [[ $? != 0 ]]; then
    # Push the changes and create a pull request
    bash .gitlab-ci/scripts/git-push.sh || exit 1
    bash .gitlab-ci/scripts/send-slack-msg.sh ${SLACK_WEBHOOK_URL} ${TEMPLATE_FILE}
  else
    echo "$0: No changed detected"
  fi
else
  echo "$0: Integration branch ${INTEGRATION_BRANCH} already exists"
fi
