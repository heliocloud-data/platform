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
source ./app.config

export AWS_LOAD_BALANCER_SSL_CERT="${AWS_LOAD_BALANCER_SSL_CERT}"

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

envsubst < monitoring-prometheus-values-env.yaml.template > monitoring-prometheus-values-env.yaml
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade prometheus prometheus-community/prometheus \
    --values=monitoring-prometheus-values.yaml \
    --values=monitoring-prometheus-values-env.yaml \
    --version=25.8.0 \
    --namespace=monitoring \
    --install \
    --timeout 5m30s \
    --debug || \
    (echo "error: unable to upgrade chart"; exit 1)

envsubst < monitoring-grafana-values-env.yaml.template > monitoring-grafana-values-env.yaml
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade grafana grafana/grafana \
    --values=monitoring-grafana-values.yaml \
    --values=monitoring-grafana-values-env.yaml \
    --version=7.0.9 \
    --namespace=monitoring \
    --install \
    --timeout 5m30s \
    --debug
