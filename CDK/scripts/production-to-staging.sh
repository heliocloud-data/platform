BASE_DIR=temp/daskhub/deploy

K8_APPS=(\
    amazon-cloudwatch
    daskhub-storage
    eksctl
    eksctl-iamidentitymappings
)

HELM_APPS=(\
    daskhub
    monitoring
)

for K8_APP in "${K8_APPS[@]}"
do
    mv ${BASE_DIR}/$K8_APP/overlays/production ${BASE_DIR}/$K8_APP/overlays/staging 2> /dev/null

done

for HELM_APP in "${HELM_APPS[@]}"
do
    echo "mv ${BASE_DIR}/$HELM_APP/values-production.yaml ${BASE_DIR}/$HELM_APP/values-staging.yaml"
    mv ${BASE_DIR}/$HELM_APP/values-production.yaml ${BASE_DIR}/$HELM_APP/values-staging.yaml 2> /dev/null

done

