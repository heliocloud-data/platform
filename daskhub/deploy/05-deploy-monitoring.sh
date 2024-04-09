#!/bin/bash
#
# This is an optional step to deploy the observability tools prometheus and
# grafana.
#
# See Also:
#   https://sweetcode.io/how-to-integrate-prometheus-and-grafana-on-kubernetes-with-helm/
#   https://stackoverflow.com/questions/63906429/how-to-access-prometheus-and-grafana-installed-in-the-ingress-nginx-namespace-on
#   https://github.com/prometheus-community/helm-charts/blob/main/charts/prometheus/templates/service.yaml
#   https://github.com/grafana/helm-charts/blob/main/charts/grafana/templates/service.yaml
#   https://aws.amazon.com/blogs/opensource/network-load-balancer-support-in-kubernetes-1-9/

cd monitoring
helm dep update
helm upgrade \
    heliocloud-monitoring ./ \
    --namespace monitoring \
    --values=values.yaml \
    --values=values-production.yaml \
    --install --timeout 10m30s --debug
