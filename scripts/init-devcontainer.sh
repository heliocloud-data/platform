#!/bin/bash

# The devcontainer has support for local overrides, which are optional.  Most commonly,
# these are used to communicate with private proxy artifact repositories for docker.io
# and pypi.org.
touch ${USER}.env

# The devcontainer mounts the .aws and .kube folders, which contin their configurations.
mkdir -p ~/.aws
mkdir -p ~/.kube

WORKSPACE_FOLDER=$(pwd)
devcontainer build --workspace-folder=${WORKSPACE_FOLDER}
devcontainer up --workspace-folder=${WORKSPACE_FOLDER}

echo ""
echo "Now run:"
echo "        devcontainer exec --workspace-folder $(pwd) bash"
echo ""

# To run the dev container
#docker run -it --rm -v `pwd`:/workspaces/`basename $(pwd)` opentofu:latest bash
