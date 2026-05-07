#!/bin/bash

# This script is responsible for initializing the base environment and installing
# all the required tools.
#
# Author: Nicholas Lenzi

# Installs certificate at OS level
if [ "$CA_CERT_URL" != "" ]; then
    CA_CERT=/usr/local/share/ca-certificates/CA_CERT.crt
    echo "Installing cert from url ${CA_CERT_URL} ..."
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

wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo tee /etc/apt/trusted.gpg.d/google.asc >/dev/null


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

# Install the SSM client
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb || exit 6
rm -rf  session-manager-plugin.deb

# Install chrome
if [[ -f ".devcontainer/bin/google-chrome-stable_current_amd64.deb" ]]; then
  sudo DEBIAN_FRONTEND=noninteractive apt install -f ./.devcontainer/bin/google-chrome-stable_current_amd64.deb -y || exit 7
else
  # TODO: Add support for downloading this
  echo "warning: Unable to locate 'google-chrome-stable_current_amd64.deb' installer, attempting to continue"
fi

if [[ "${POST_START_PIP_INSTALL_REQUIREMENTS}" == "true" ]]; then
  for pip_req_file in ./requirements*.txt; do
    echo "Installing deps of ${pip_req_file} ..."
    pip install --user -r ${pip_req_file} || exit 8
  done
 
fi

if [[ "${POST_START_PRE_COMMIT_INSTALL_HOOKS}" == "true" ]]; then
  pre-commit install || exit 9
fi
