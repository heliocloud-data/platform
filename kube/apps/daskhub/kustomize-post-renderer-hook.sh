#!/bin/bash

cat <&0 > all.yaml

kustomize build . | \
    # This awfulness comes from what appears to be a bug in kustomize's
    # ability to handle multi-line string values in patch files.
    sed 's/config.yaml: |-/config.yaml: |/' && \
    rm all.yaml
