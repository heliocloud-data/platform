#!/bin/bash
#
# This script will add and commit all local changes
# This script will install the system dependencies required to run
# the gitlab-ci pipelines.  Eventually, they should be migrated into
# a docker container.

echo "git status"
git status

echo "git rev-list --count origin..HEAD"
git rev-list --count origin..HEAD

COMMIT_COUNT=$(git rev-list --count origin..HEAD)

if [[ $COMMIT_COUNT != 0 ]]; then
  echo "Pushing changes"
  echo "git push -o merge_request.create"
  git push -o merge_request.create

fi
