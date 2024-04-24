#!/bin/bash

bash scripts/install-deps-systools.sh || exit 1
bash scripts/install-deps-kube.sh || exit 1
bash scripts/install-deps-nodejs-no_sudo.sh || exit 1
bash scripts/install-deps-cdk.sh || exit 1
