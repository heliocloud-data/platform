#!/bin/bash
#
# This script will add and commit all local changes
# This script will install the system dependencies required to run
# the gitlab-ci pipelines.  Eventually, they should be migrated into
# a docker container.

git status | grep 'Your branch is up to date with'
RET=$?

if [[ $RET != 0 ]]; then
#  git pull
  echo "Pushing changes"
  echo "git push -o merge_request.create"
  git push -o merge_request.create

fi
