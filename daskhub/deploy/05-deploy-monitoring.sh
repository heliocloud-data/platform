#!/bin/bash
#
# This is an optional step to deploy the observability tools prometheus and
# grafana.

cd monitoring
helm dep update
helm upgrade \
    heliocloud-monitoring ./ \
    --create-namespace \
    --namespace monitoring \
    --values=values.yaml \
    --values=values-production.yaml \
    --install --timeout 10m30s --debug
