# Import existing resources

```
tofu init
tofu import  -var-file=environments/dev/terraform.tfvars.json aws_route53_zone.HelioCloud_PrimaryZone <HOSTED_ZONE_ID>
tofu plan -var-file environments/dev/terraform.tfvars.json
```

# Deploy HelioCloud

## Deploy the AWS resources

To Deploy HelioCloud via OpenTofu

```
tofu init
tofu apply -var-file environments/dev/terraform.tfvars.json
```

## Deploy the Kubernetes Applications


### Local configurations

The first step is to configure your local environment to authenticate with the Kubernetes Cluster you deployed during the previous step.  Kubernetes uses a local file called the `kubeconfig`, typically located in `~/.kube/config`.  The `aws` CLI application will generate one of these automatically for you via the following command:

```
# Create the kubectl config file:
aws eks update-kubeconfig --region $(cat environments/dev/terraform.tfvars.json | jq '.aws_region' | sed 's#"##g') --name $(cat environments/dev/terraform.tfvars.json | jq '.cluster_name' | sed 's#"##g')
```

Once you've updated your `kubeconfig`, run any `kubectl` to verify connectivity.

```
kubectl get nodes
```

### Deploy the Kube Admin Kubernetes Applications

Render the environment specific k8s resources

```
kustomize build kube/kubeadm/cluster-autoscaler/overlays/dev | kubectl apply -f -
kustomize build kube/kubeadm/external-dns/overlays/dev | kubectl apply -f -
```

### Deploy the HelioCloud Kubernetes Applications

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

# Tear Down HelioCloud

## Delete the EKS Cluster

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
