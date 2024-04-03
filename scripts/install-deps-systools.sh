#!/bin/bash
#
# This script will install the various system tools.
#
# Author: Nicholas Lenzi

apt-get update
apt-get install -y gettext

envsubst --version
if [[ $? != 0 ]]; then
    echo "error: failed to install envsubst"
    exit 1
fi
exit 0