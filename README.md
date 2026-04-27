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

Deploy Kube Admin
```
kustomize build kube/kubeadm/cluster-autoscaler/overlays/dev | kubectl apply -f -
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
