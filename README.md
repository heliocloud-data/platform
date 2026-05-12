To Deploy HelioCloud via OpenTofu

```
tofu init
tofu apply -var-file environments/dev/terraform.tfvars.json
```


Deploy Daskhub

```
# Create the kubectl config file:
aws eks update-kubeconfig --region $(cat environments/dev/terraform.tfvars.json | jq '.aws_region' | sed 's#"##g') --name $(cat environments/dev/terraform.tfvars.json | jq '.cluster_name' | sed 's#"##g')

# Verify connectivity into the cluster
kubectl get nodes
```

Render the environment specific k8s resources

Deploy Kube Admin
```
kustomize build kube/kubeadm/cluster-autoscaler/overlays/dev | kubectl apply -f -
kustomize build kube/kubeadm/external-dns/overlays/dev | kubectl apply -f -
```


Deploy HelioCloud
```
kustomize build kube/apps/storage/overlays/dev | kubectl apply -f -

cd kube/apps/daskhub
helm dep update
helm upgrade \
    daskhub ./ \
    --namespace daskhub \
    --values=values.yaml \
    --values=values-dev.yaml \
    --post-renderer=./kustomize-post-renderer-hook.sh \
    --install --timeout 30m30s --debug
```


Deleting a cluster
```
#collect the outputs
tofu output -json > heliocloud_deployment_outputs.json


eksctl get nodegroups 
    --cluster=$(cat heliocloud_deployment_outputs.json | jq '.eks_cluster_name.value' | sed 's#"##g') 
    --region=$(cat heliocloud_deployment_outputs.json | jq '.aws_region.value' | sed 's#"##g') -o json
    | jq '.[].Name'
    | xargs -n 1 eksctl delete nodegroup 
        --cluster=$(cat heliocloud_deployment_outputs.json | jq '.eks_cluster_name.value' | sed 's#"##g') --region=$(cat heliocloud_deployment_outputs.json | jq '.aws_region.value' | sed 's#"##g')

eksctl get nodegroups --cluster=$(cat heliocloud_deployment_outputs.json | jq '.eks_cluster_name.value' | sed 's#"##g') --region=$(cat heliocloud_deployment_outputs.json | jq '.aws
_region.value' | sed 's#"##g')
```
