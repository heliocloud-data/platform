# HelioCloud DaskHub installation instructions
These are instructions about how to install the HelioCloud version of DaskHub in AWS.

- [HelioCloud DaskHub installation instructions](#heliocloud-daskhub-installation-instructions)
- [Installing DaskHub](#installing-daskhub)
  - [Requirements](#requirements)
  - [Initial infrastructure](#initial-infrastructure)
  - [Kubernetes Installation](#kubernetes-installation)
    - [Cluster (EKS) Configuration and Deployment](#cluster-eks-configuration-and-deployment)
    - [DaskHub Helm Deployment](#daskhub-helm-deployment)
  - [Log into DaskHub](#log-into-daskhub)
  - [Create Users](#create-users)
  - [OAuth Notes](#oauth-notes)
  - [Debugging](#debugging)
- [Updating DaskHub](#updating-daskhub)
  - [Updating Kubernetes Cluster](#updating-kubernetes-cluster)
- [Deleting DaskHub](#deleting-daskhub)
  - [Tearing down HelioCloud DaskHub infrastructure](#tearing-down-heliocloud-daskhub-infrastructure)
- [Notes](#notes)
  - [Things that persist](#things-that-persist)

# Installing DaskHub
## Requirements
Must be able to deploy AWS CDK projects and we recommend but do not require that you have the SSM client set up.


## Initial infrastructure

We will setup an admin machine (an EC2 instance) and other infrastructure via AWS CDK (we assume this has been done in accordance with the HelioCloud framework install). This admin machine is where we run the Kubernetes install and interact with the DaskHub. 

1. Deploy DaskHub through CDK (instructions [here](../README.md))
   - Ensure that the DaskHub is being deployed as part of your HelioCloud instance by setting `enabled.daskhub` to `True`
in your instance configuration file stored at `instance/name_of_instance.yaml`(see [the example instance configuration file for details](../instance/example.yaml))
1. SSM into EC2 instance either through the AWS CLI command line (recommended method) or using AWS Console EC2 Instance Connect


   - <details><summary>Through SSM</summary><blockquote>
  
     - In order to SSM you must have both the [AWS CLI](https://aws.amazon.com/cli/) and the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) installed 
      - Find `<INSERT_EC2_INSTANCE>` by looking at output from your CDK deployment terminal (labeled as `HelioCloud-DaskHub.InstanceID`) or in the AWS Console under CloudFormation, it is under the stack's output under PublicDNS
        - ![finding EC2 DNS ADDRESS](instruction_images/get_instance_id_cloudformation.png)
  
      - Run the following command within a local terminal (uses default AWS credentials set up with `aws configure`):
        ~~~~
        aws ssm start-session --target <INSERT_EC2_INSTANCE>
        ~~~~
      - NOTE: if you receive CERTIFICATE_VERIFY_FAILED errors, you can optionally use the `no-ssl-verify` flag (though this is not recommended)

      </blockquote></details>
   - <details><summary>Through Instance Connect</summary><blockquote>
  
      - Find the EC2 instance in the Cloudformation stack resources, can click the highlighted launch button to jump to the instance 
        ![finding EC2 instance](instruction_images/find_cloudformation_ec2.png) 
      - Select the EC2 instance and click the Connect button
        ![finding EC2 connect button](instruction_images/ec2_connect_button.png) 
      - Start connection to be connected through SSH in browser
        ![connect screen](instruction_images/ec2_connect_screen.png)
      </blockquote></details>

## Kubernetes Installation

### Cluster (EKS) Configuration and Deployment
During this stage, we're going to standup a Kubernetes cluster in EKS using `eksctl` and `kustomize`, deploy some required resources to the `kube-system` namespace and, enable `amazon-cloudwatch`.

Move to home directory (either with `cd` or `cd ~`).  From here, each subdirectory contains a separate logical component of the deployment.  For the purposes of the EKS deployment, see the `eksctl/` directory and for Kubernetes `kube-system` namespace deployment see `kube-system/`.

These projects follow use the **bases** and **overlays** concepts descibed [here](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/#bases-and-overlays).

To automatically bring up the Kubernetes cluster w/ the required changes to the `kube-system` namespace, simply type:
> ./01-deploy-k8s.sh

This task should take around 20 minutes to complete.  Once complete, move on to the DaskHub Storage section.  Advanced users, may decompose these tests, if so, review the following steps:


1. Deploy the cluster using `eksctl`
The base layer of the cluster configuration is defined in `eksctl/base/cluster-config.yaml` with the environment specific settings stored in `eksctl/overlays/production/kustomization.yaml`.  The default configuration shouldn't
require any modifications to deploy, but can be changed as needed.  For more details how to configure EKS clusters, consult the [eksctl Config File Schema Usage](https://eksctl.io/usage/schema/).

Type the following:
```
kustomize build eksctl/overlays/production > eksctl/eksctl-kustomize.yaml && \
    eksctl create cluster -f eksctl/eksctl-kustomize.yaml
```

2. Deploy the `kube-system`` namespace
Within this step, we'll be deploying the `cluster-autoscaler` and some additional `RoleBindings` required to administer an EKS cluster from the AWS console.

Type the following:
```
kustomize build kube-system/base | kubectl apply -f -
```

3. Deploy the `amazon-cloudwatch` namespace
Within this step, we'll be deploying the `amazon-cloudwatch` namespace, which handles log aggregation and the pod and node level.  When enabled, these logs will be available from the AWS console at CloudWatch.

Type the following:
```
kustomize build amazon-cloudwatch/overlays/production | kubectl apply -f -
```

### DaskHub Storage Deployment
During this stage, we're going to deploy the daskhub namespace and the storage related resources (`persistentvolume` and `persistentvolumeclaims`) required for the HelioCloud DaskHub Deployment.  Afterwards, a separate EFS Mount Target, that's addressable from the Kubernetes Environment, will be created.

Kubernetes .  For more details on how to tailor storage for your environment, consult the [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) section of the Kubernetes Documentation.

The default configuration contains shared scratch space between all users on Dashhub (sometimes this is refered to as the "EFS mount").  This can be removed from your deployement by skipping this step and removing all `efs-persist` related references from the DaskHub Helm Chart values in the DaskHub deployment stage.

To automatically bring up the Kubernetes cluster w/ the required changes to the `kube-system` namespace, simply type:
> ./02-deploy-daskhub-storage.sh

This task should only take a few seconds to complete.  Once complete, move on to the DaskHub Helm section.  Advanced users, may decompose these tests, if so, review the following steps:


1. Creating the daskhub related storage resources
The base layer of the daskhub storage is defined in `daskhub-storage/base/` with the environment specific settings stored in `daskhub-storage/overlays/production/kustomization.yaml`.  The default configuration shouldn't
require any modifications to deploy, but can be changed as needed.

Type the following:
```
kustomize build daskhub-storage/overlays/production | kubectl apply -f -
```

2. Create an EFS Mount Target within the EKS 
Within this step, a new EFS mount target addressable from the EKS cluster will be created.

Type the following, where `EFS_ID`, `EKS_NAME`, `AWS_REGION`, `AWS_AZ_PRIMARY` are the identifier of the EFS volume, the name of the EKS cluster, the AWS region and the primary availablity zone of your EKS cluster respectively:
```
SUBNET_IDS=`aws eks describe-cluster --name $EKS_NAME --region $AWS_REGION --query cluster.resourcesVpcConfig.subnetIds --output text`
SG_ID=`aws eks describe-cluster --name $EKS_NAME --region $AWS_REGION --query cluster.resourcesVpcConfig.clusterSecurityGroupId --output text`

SUBNET_ID=`aws ec2 describe-subnets --subnet-ids $SUBNET_IDS --filters "Name=availability-zone,Values=$AWS_AZ_PRIMARY" --query "Subnets[0].SubnetId" --output text`

aws efs create-mount-target \
    --file-system-id $EFS_ID \
    --subnet-id $SUBNET_ID \
    --security-groups $SG_ID

```

### DaskHub Helm Deployment
During this stage, we're going to standup the DaskHub!

To automatically deploy the DaskHub and register the domain in Route53, simply type:
> ./03-deploy-daskhub.sh

Initial deploy of the DaskHub can take up to 30 minutes to complete.  Once complete, move on to the Log into DaskHub section.  Advanced users, may decompose these tests, if so, review the following steps:

1. Deploy the DaskHub using the Helm Chart.
The DaskHub deployment is deployed via a Helm Chart.  It consists of two sub-charts, `jupyterhub` and `dask-gateway`.  Consult the respective documentation sites for these two tools for more details [here](https://z2jh.jupyter.org/en/stable/) and [here](https://gateway.dask.org/install-kube.html).

Consult the [Using Helm](https://helm.sh/docs/intro/using_helm/) from the Helm Documentation site for more detail.  

```
cd daskhub
helm dep update
helm upgrade \
    daskhub ./ \
    --namespace ${KUBERNETES_NAMESPACE} \
    --values=values.yaml \
    --values=values-production.yaml \
    --post-renderer=./kustomize-post-renderer-hook.sh \
    --install --timeout 30m30s --debug
```


2. Update the Route53 entry.
In the previous step, an AWS Load Balancer will automatically have been created to handle ingress for DaskHub.  For this step, we're going to update a Route53 CNAME record to point to this load balancer.

```
# 1. Look up the URL to the load balancer created during the deployment.
LOADBALANCER_URL=$(kubectl --namespace=$KUBERNETES_NAMESPACE get svc proxy-public --output jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# 2. Inject the URL to the load balancer into a Route53 request
cp route53_record.json.template route53_record.json
sed -i "s|<INSERT_LOADBALANCER_URL>|$LOADBALANCER_URL|g" route53_record.json

# 3. Update the CNAME record in Route53
ROUTE53_HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name | jq --arg name "$ROUTE53_HOSTED_ZONE." -r '.HostedZones | .[] | select(.Name=="\($name)") | .Id')
aws route53 change-resource-record-sets --hosted-zone-id $ROUTE53_HOSTED_ZONE_ID --change-batch file://route53_record.json
```

See more details on [DNS routing](https://saturncloud.io/blog/jupyterhub_security/) and [https](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/security.html#set-up-automatic-https).


## Log into DaskHub

6. Go to the DaskHub Frontend URL you just configured and try logging in. (NOTE: sometimes it can take up to 5 minutes for the DNS to propagate).  If you try to load too early on Google Chrome it seems to not try to resync for several minutes (try alternate browser).

  - The URL is defined in the HelioCloud instance configuration (`/daskhub/daskhub/domain_record`.`/daskhub/daskhub/domain_url` in your HelioCloud instance configuration), default is `daskhub.</daskhub/daskhub/domain_url>`.

When successful, all pods within the `daskhub` namespace should be in `RUNNING` status, which looks something like this:
```
> sh-4.2$ kubectl --namespace daskhub get pods

NAME                                              READY   STATUS    RESTARTS   AGE
api-daskhub-dask-gateway-d4c57fdf7-96sw9          1/1     Running   0          29m
autohttps-7796dd569d-kwngk                        2/2     Running   0          29m
controller-daskhub-dask-gateway-f9d87c4f6-t7x42   1/1     Running   0          29m
hub-68d67c569d-4hbnf                              1/1     Running   0          63m
proxy-5c96bb5bb-pmnb5                             1/1     Running   0          63m
traefik-daskhub-dask-gateway-7545967cdb-zh2fw     1/1     Running   0          29m
user-scheduler-7cb7b48fdd-5rvm2                   1/1     Running   0          29m
user-scheduler-7cb7b48fdd-h26rd                   1/1     Running   0          29m
```

Congratulations! At this point you should have a working HelioCloud DaskHub environment. The following section will outline how you can create authorized users within the DaskHub.

## Create Users

If you are using AWS Cognito (our default configuration) you will have to create users for the DaskHub via the AWS Web Console or similar (e.g. AWS CLI).  
   - First find the relevant AWS Cognito User Pool
     - Log into the AWS Console
     - Find the CloudFormation Auth deployment associated with your HelioCloud instance by first going searchinging `CloudFormation` in the search bar, then select the the Auth stack associated by your instance (ex. `<instance_name>AUTH####`) and select the resources, find the associated User Pool and click on the arrow to link you to the Cognito User Pool ![finding cognito user pool](instruction_images/find_cognito_user_pool.png)
   - Once at the Cognito User Pool, click `Create User`
   ![finding create user button](instruction_images/user_pool_create_user_button.png)
   - Make an admin account that uses the same admin name as one given in the HelioCloud instance configuration (`/daskhub/daskhub/admin_users`).  Be sure to click `Invitation message: send an email invitation` if you use `generate a password` or it will not tell you what password it generated (or you can set your own password).
     - ![creating user options](instruction_images/user_pool_create_user_options.png)
   - (Optional) Make non-admin user account for testing or to populate your users' accounts

## OAuth Notes

OAuth is controlled by your institution's authorization method (AWS Cognito is described in this document) and used by JupyterHub under the hood.  The oauth access token will persist based on your authorization setup.  The default in AWS Cognito is 60 minutes.  This means that if you logout of the DaskHub and then click sign in it will auto login and bypass the login page if the token has not expired.  This is NOT a security issue, the token is behaving as set-up.  This does however mean that users cannot easily logout and have another user login on their same browser.  Institutions may adjust the token time of life in their own authorization tool per their needs.

NOTE: AWS session tokens expire but have a long expiration time. If you are trying to log in as more than 1 user (for testing), you may have to use a different browser session to avoid token clashes blocking the login.

## Debugging
Some debugging tips in no particular order. NOTE: the default `NAMESPACE` in the HelioCloud instance configuration at `/daskhub/daskhub/namespace`, which defaults to `daskhub`

- Check logs
  - Can check pod logs by first finding pod name using `kubectl -n <NAMESPACE> get pods` and then `kubectl -n <NAMESPACE> logs <POD_NAME>` with the appropriate pod name

- Restart pod by killing it
    - Can kill a pod and it will restart `kubectl -n <NAMESPACE> delete pod <POD_NAME>`

- Check helm configuration
    - Can examine if helm configuration files are not being parsed properly by adding `--dry-run --debug` to helm command, can also save to output file.  
    - Example:
    `helm upgrade daskhub dask/daskhub --namespace=<NAMESPACE> --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install --dry-run --debug > test.out`

- Check event stack
    - It can be helpful to look at the event stack for your pods using:
        `kubectl -n <NAMESPACE> get events --sort-by='{.lastTimestamp}'`

- Turn on jupyterhub debugging
    - You can also turn on `debugging` in jupyterhub. Edit the `dh-config.yaml` file so that:
    ~~~
    jupyterhub:
    debug:
        enabled: true
    ~~~

- Check AWS regional availability
    - Image pull problems can be related to regional availability. Use the following command to verify availability for your region:
      - `aws ec2 describe-instance-type-offerings --location-type availability-zone  --filters Name=instance-type,Values=c5.xlarge --region us-east-1 --output table`

- Force node to scale up
    -  `eksctl scale nodegroup --cluster <CLUSTER_NAME> --name=ng-user-compute-spot --nodes-min=1` where <CLUSTER_NAME> is set by defaults to `eks-helio`

# Updating DaskHub

To update DaskHub you can alter any value or the  `Chart.yaml` itself and then run:

```
helm upgrade upgrade \
    daskhub ./ \
    --namespace ${KUBERNETES_NAMESPACE} \
    --values=values.yaml \
    --values=values-production.yaml \
    --post-renderer=./kustomize-post-renderer-hook.sh \
    --install --timeout 30m30s --debug
```

## Updating the Kubernetes Cluster

The `cluster` and `nodeGroups` configurations of your cluster can be applied automatically from your `cluster-config.yaml` file by running the following command:
```
kustomize build eksctl/overlays/production > eksctl/eksctl-kustomize.yaml && \
        eksctl upgrade cluster -f eksctl/eksctl-kustomize.yaml --approve
```

NOTE: Some settings within your cluster configuration such as `iam`, `addons` and `iamidentitymapping` don't appear to have any effect.


# Deleting DaskHub

In order to delete DaskHub from the Kubernetes need to follow instructions (uninstall helm) here where the namespace from these instructions is "daskhub":
https://phoenixnap.com/kb/helm-delete-deployment-namespace

If used the instructions above can call `helm uninstall daskhub --namespace <NAMESPACE>` to remove daskhub


## Tearing down HelioCloud DaskHub infrastructure
1. Execute `99-delete-daskhub.sh` by running `./99-delete-daskhub.sh`
   - Uninstalls the helm chart, detaches the EFS mount, and tears down the Kubernetes cluster
   - If any failures can look in the AWS console for further debugging, most common failure is the EFS mounted target is still present and using the EKS VPC so the cluster is taken down (which will show cluster delete complete) but the cloudformation stack is still up with the VPC.  If this is the case, go into EFS > network and delete the troublesome mounted target.  Another issue may be that there is an existing Elastic Network Interface still up can go find these through EC2 > Network Interfaces
   - Note that some resources will persist and if you truly want them deleted you will need to delete them by hand (their retention policy is set to not delete by default). See [list of AWS resources](#things-that-persist) that persist.
2. Tear down the HelioCloud install DaskHub stack by calling `cdk destroy -c config=<CONFIGURING_FILE> HelioCloud-DaskHub` in your local terminal in the same way you deploy your cdk install

Make sure resources no longer exist before proceeding to next step as this can cause the infrastructure to get stuck in a dependency loop and require extensive troubleshooting.

# Notes

## Things that persist
- EFS
- Persistent volume in EBS (under EC2)
- KMS
- S3 bucket