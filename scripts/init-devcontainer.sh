#!/bin/bash

WORKSPACE_FOLDER=$(pwd)
devcontainer build --workspace-folder=${WORKSPACE_FOLDER}
devcontainer up --workspace-folder=${WORKSPACE_FOLDER}

echo ""
echo "Now run:"
echo "        devcontainer exec --workspace-folder $(pwd) bash"
echo ""
