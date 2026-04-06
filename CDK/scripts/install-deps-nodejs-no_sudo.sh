#!/bin/bash
#
# This script will install the system dependencies required to run
# the nodejs and npm.
#
# Author: Nicholas Lenzi
# Install nodejs v18
# From: https://github.com/nodesource/distributions
apt-get update &&  apt-get install -y ca-certificates curl gnupg && mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
export NODE_MAJOR=18 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
apt-get update && apt-get install -y nodejs

node --version
if [[ $? != 0 ]]; then
    echo "error: failed to install nodejs"
    exit 1
fi

npm --version
