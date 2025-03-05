#!/bin/bash

# This script is responsible for initializing the base environment and installing
# all the required tools.
#
# Author: Nicholas Lenzi

# Installs certificate at OS level
if [ "$CA_CERT_URL" != "" ]; then
    CA_CERT=/usr/local/share/ca-certificates/CA_CERT.crt
    echo "Installing cert from url ${CA_CERT_URL}."
    sudo curl ${CA_CERT_URL} -o ${CA_CERT}
    sudo update-ca-certificates --verbose
else
    echo "No cert update necessary."
fi

# Configure PIP's global index-url
if [ "$PIP_GLOBAL_INDEX_URL" != "" ]; then
    mkdir -p ~/.pip
    echo "[global]
    index-url = ${PIP_GLOBAL_INDEX_URL}
    " > ~/.pip/pip.conf
fi

# Installs nodejs/npm
bash scripts/install-deps-nodejs.sh || exit 1

# Installs awscli, kubectl, eksctl and helm
sudo bash scripts/install-deps-kube.sh || exit 2

# Installs envsubst
sudo bash scripts/install-deps-systools.sh || exit 3

# Install docker
bash scripts/install-deps-docker.sh || exit 4

# Install CDK
if [ "$CA_CERT" != "" ]; then
    npm config set cafile ${CA_CERT}
fi
sudo -E bash scripts/install-deps-cdk.sh || exit 5

# Install the SSM client
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb || exit 6
rm -rf  session-manager-plugin.deb

# Install chrome
sudo apt install -f ./google-chrome-stable_current_amd64.deb -y || exit 7

# Install the project deps
if [ "${POST_START_PIP_INSTALL_REQUIREMENTS}" == "true" ]; then
    # If the PIP_GLOBAL_INDEX_URL is set AND REQUEST_CA_BUNDLE
    # there's a self-signed certificate in the chain, but it conflicts
    if [ "$PIP_GLOBAL_INDEX_URL" != "" ]; then
        unset REQUESTS_CA_BUNDLE
    fi

    pip install -r requirements.txt ${EXTRA_PIP_ARGS}
    pip install -r requirements-dev.txt ${EXTRA_PIP_ARGS}
fi
