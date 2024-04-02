#!/bin/bash
#
# This script will install the system dependencies required to run
# the nodejs and npm.
#
# Author: Nicholas Lenzi

# Install nodejs v18
# From: https://github.com/nodesource/distributions
sudo apt-get update &&  sudo apt-get install -y ca-certificates curl gnupg && sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/nodesource.gpg
export NODE_MAJOR=18 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
sudo apt-get update && sudo apt-get install -y nodejs

node --version
if [[ $? != 0 ]]; then
    echo "error: failed to install nodejs"
    exit 1
fi

npm --version
