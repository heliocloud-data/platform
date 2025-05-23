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

#!/bin/bash
# This is a mandatory step to ensure deployment of ingress/authentication proxies

cd ../ingress
helm dep update
helm upgrade \
    heliocloud-ingress ./ \
    --create-namespace \
    --namespace ingress \
    --values=values.yaml \
    --values=values-production.yaml \
    --install --timeout 10m30s --debug
