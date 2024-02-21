#!/bin/bash

# Installs certificate at OS level
if [ "$CA_CERT_URL" != "" ]; then
    CA_CERT=/usr/local/share/ca-certificates/CA_CERT.crt
    echo "Installing cert from url ${CA_CERT_URL}."
    curl ${CA_CERT_URL} -o ${CA_CERT}
    update-ca-certificates --verbose
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
bash .gitlab-ci/scripts/install-deps.sh

# Installs awscli, kubectl, eksctl and helm
bash .gitlab-ci/scripts/install-deps-kube.sh

# Installs envsubst
apt-get update && apt-get install -y gettext

# Install docker
curl -sSL https://get.docker.com/ | sh

# Install CDK
npm install -g aws-cdk

# Install the SSM client
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
dpkg -i session-manager-plugin.deb
rm -rf  session-manager-plugin.deb

# Install chrome
apt install -f ./google-chrome-stable_current_amd64.deb -y

# Install the project deps
if [ "${POST_START_PIP_INSTALL_REQUIREMENTS}" == "true" ]; then
    # If the PIP_GLOBAL_INDEX_URL is set AND REQUEST_CA_BUNDLE
    # there's a self-signed certificate in the chain, but it conflicts
    if [ "$PIP_GLOBAL_INDEX_URL" != "" ]; then
        unset REQUESTS_CA_BUNDLE

        pip install -r requirements.txt 
        pip install -r requirements-dev.txt 
    fi
fi

# TODO: Install chromioum