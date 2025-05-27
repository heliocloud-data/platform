#!/bin/bash
# This is a mandatory step to ensure deployment of ingress/authentication proxies

cd ingress
helm dep update
helm upgrade \
    heliocloud-ingress ./ \
    --create-namespace \
    --namespace ingress \
    --values=values.yaml \
    --values=values-production.yaml \
    --install --timeout 5m --debug
