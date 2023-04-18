# HelioCloud DaskHub installation instructions
These are instructions about how to install the HelioCloud version of DaskHub in AWS.

- [HelioCloud DaskHub installation instructions](#heliocloud-daskhub-installation-instructions)
- [Installing Daskhub](#installing-daskhub)
  - [Requirements](#requirements)
  - [Initial infrastructure](#initial-infrastructure)
  - [Kubernetes Installation](#kubernetes-installation)
    - [Cluster (EKS) Configuration and Deployment](#cluster-eks-configuration-and-deployment)
    - [DaskHub Helm Deployment](#daskhub-helm-deployment)
  - [Debugging](#debugging)
- [Updating Daskhub](#updating-daskhub)
  - [Updating Kubernetes Cluster](#updating-kubernetes-cluster)
- [Deleting Daskhub](#deleting-daskhub)
  - [Tearing down HelioCloud Daskhub infrastructure](#tearing-down-heliocloud-daskhub-infrastructure)
- [Notes](#notes)
  - [OAuth Auto Login](#oauth-auto-login)
  - [Things that persist](#things-that-persist)

# Installing Daskhub
## Requirements
Must be able to deploy AWS CDK projects and we recommend but do not require that you have the SSM client set up.


## Initial infrastructure

We will setup an admin machine (an EC2 instance) and other infrastructure via AWS CDK (we assume this has been done in accordance with the HelioCloud framework install). This admin machine is where we run the Kubernetes install and interact with the Daskhub. 

1. Deploy Daskhub through CDK (instructions [here](../README.md))
   - Ensure that the DaskHub is being deployed with the configuration file (see [the sample configuration file for details](../config/dev.yaml))
     - Must set `components.enableDaskHub` to `True` in the HelioCloud install configuration as well as any necessary parameters in the `daskhub` block 
2. SSM into EC2 instance either through command line or using AWS Console EC2 Instance Connect
   - <details><summary>Through SSM</summary><blockquote>
  
        ~~~~
        aws ssm start-session --target <INSERT_EC2_INSTANCE>
        ~~~~
    
      - In order to SSM you must have both the [AWS CLI](https://aws.amazon.com/cli/) and the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) installed 
      - Can find `<INSERT_EC2_INSTANCE>` by looking at output from CDK terminal (labeled as `HelioCloud-Daskhub.InstanceID`) or in the AWS Console under CloudFormation, it is under the stack's output under PublicDNS
        - ![finding EC2 DNS ADDRESS](instruction_images/get_instance_id_cloudformation.png)
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
3. Move to home directory (either with `cd` or `cd ~`) and alter configuration file `app.config`
    - Assumes that Daskhub will be deployed to a DNS that is linked in AWS Route 53. Can deploy if this is not the case but these instructions do not support alternative methods
    - Can alter the following variables (`NAMESPACE` - the kubernetes namespace to deploy application to - and `EKS_NAME` - the name of the AWS Elastic Kubernetes Service we are deploying) at top of file if they already exist or don't reflect your name choice

4. Setup and deploy Kubernetes (K8s) on EC2 machine
    - Can alter nodeGroups and managaedNodeGroups in `cluster-config.yaml.template` to suit your cluster (default has master and nodes where uses have spot nodes and users have 3 types of nodes - high compute user, high GPU user, and high compute burst)
    - Execute `01-deploy-k8s.sh` by running `./01-deploy-k8s.sh`
        - May fail if region deploying in does not have those instance types, can modify the `cluster-config.yaml.template` file to remove or replace instance types that are available in region and rerun script 
        - TODO do the following in a verification script and throw error if not working
        - Can ensure persistent volumes are created by running `kubectl get pv` and `kubectl get pvc --namespace <NAMESPACE>`
        - Can ensure autoscaling set by running `kubectl get deployments --namespace kube-system`

### DaskHub Helm Deployment

**Daskhub (and JupyterHub) can be set-up so that there is no authentication.  We do NOT recommend this as this will leave a public facing entrypoint to your AWS instance where malicious users can access your Daskhub**.  The current HelioCloud DaskHub configuration is set-up for authentication (but can be run without).  If users standup DaskHubs without authentication (ex. for testing), we recommend tearing it down immediately after debugging is complete.

This deployment assumes that Daskhub uses AWS Cognito for Authentication and Authorization that is initialized in step 1.  Other methods of Authentication and Authorization can be used but we do not detail them here. We also assume that the user wants domain routing to a DNS address purchased and available in AWS Route 53.  This is so the DaskHub can be accessed from a human readable URL.  We assume the user wants the DaskHub to sit on a subdomain of the DNS address that is configured in step 3.

See more details on [DNS routing](https://saturncloud.io/blog/jupyterhub_security/) and [https](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/security.html#set-up-automatic-https).


5. Execute `02-deploy-daskhub.sh` by running `./02-deploy-daskhub.sh`
    - This script  generates copies and fills in configurable values of 3 Daskhub configuration files (can alter manually if have alternate configurations):
        <details>
        <summary>dh-config.yaml </summary>

        - this file contains the specifications of our exact Daskhub build and we will modify the template file as we perform updates.  This file assumes you have built K8s as above specifically the EFS and serviceaccount naming conventions (if this is not the case alter these sections)
        -  Only need to adjust `dh-config.yaml` if you did not follow the standard deployment instructions

        </details>

        <details>
        <summary>dh-secrets.yaml</summary>

        - this file contains randomly generated API keys for JupyterHub and DaskHub, if you have specific API keys replace those instead
        -  Only need to adjust `dh-secrets.yaml` if you want to specify your own API keys for Daskhub

        </details>

        <details>
        <summary>dh-auth.yaml</summary>

        - this file contains authentication components of the Daskhub.  This is optional but highly recommended and done by default in this set-up. 

        </details>
    - This will use Helm (a K8s package manager) to get Daskhub running on our cluster
    - Default first deploys without Authentication and Authorization then gets the URL for our DNS routing and reruns with Authentication and Authorization specified in `dh-auth.yaml`, can alter `02-deploy-daskhub.sh` according to comments to run without authentication
    - If you receive an error on executing the helm chart see this [link](https://stackoverflow.com/questions/72126048/circleci-message-error-exec-plugin-invalid-apiversion-client-authentication)


Congratulations! At this point you should have a working HelioCloud DaskHub environment.
Go to the Daskhub Frontend URL you just configured and try logging in.
- If this does not work after waiting a moment for the changes to propagate through try running: `helm upgrade daskhub dask/daskhub --namespace=<NAMESPACE> --values=dh-config.yaml --values=dh-secrets.yaml --version=2022.8.2 --install` and checking that the daskhub is working without auth then run `helm upgrade daskhub dask/daskhub --namespace=<NAMESPACE> --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install` and try the link again.  Sometimes it takes a few deploys.


## Debugging
Some debugging tips in no particular order. NOTE: the default `NAMESPACE` in `app.config` is `daskhub`

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
    -  `eksctl scale nodegroup --cluster <CLUSTER_NAME> --name=ng-user-compute-spot --nodes-min=1` where <CLUSTER_NAME> is set by default to `eks-helio` in `app.config`

# Updating Daskhub

To update Daskhub you can alter any of the configuration files (NOTE: not the ones with the suffix .template) and then run `helm upgrade daskhub dask/daskhub --namespace=<NAMESPACE> --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install`

NOTE: often changes can take a minute or two to propogate through the system.

## Updating Kubernetes Cluster

1. Find nodes
   -  To list the worker nodes registered to the Amazon EKS control plane, run the following command:
      - `eksctl get nodegroup --cluster <clusterName>` where <CLUSTER_NAME> is set by default to `eks-helio` in `app.config`.  The following is an example output

        ```
        [centos@ip-172-31-90-70 ~]$ eksctl get nodegroup --cluster <clusterName>
        CLUSTER		NODEGROUP		STATUS		CREATED			MIN SIZE	MAX SIZE	DESIRED CAPACITY	INSTANCE TYPE	IMAGE ID		ASG NAME		TYPE
        eks-helio	ng-burst-compute-spot	CREATE_COMPLETE	2022-10-11T16:19:55Z	0		10		0			m5.8xlarge	ami-099c768b04001b983	eksctl-eks-helio-nodegroup-ng-burst-compute-spot-NodeGroup-1CBEMPEXLSKOS	unmanaged
        eks-helio	ng-daskhub-services	ACTIVE		2022-10-11T16:20:28Z	1		1		1			t3a.medium	AL2_x86_64		eks-ng-daskhub-services-98c1e3ec-7689-7a38-830d-011e2be4cbc6			managed
        eks-helio	ng-user-compute-spot	CREATE_COMPLETE	2022-10-11T16:19:55Z	0		15		0			m5.xlarge	ami-099c768b04001b983	eksctl-eks-helio-nodegroup-ng-user-compute-spot-NodeGroup-1B379X9Q74QA9		unmanaged
        eks-helio	ng-user-gpu-spot	CREATE_COMPLETE	2022-10-11T16:19:55Z	0		5		0			g4dn.xlarge	ami-0cb17a7e952cabb92	eksctl-eks-helio-nodegroup-ng-user-gpu-spot-NodeGroup-1E03TASV0OF6E		unmanaged
        ```
2. Drain nodes
   - Drain each node using `eksctl drain nodegroup --cluster=<CLUSTER_NAME> --name=<NODE_GROUP_NAME> `
      - Ex. `eksctl drain nodegroup --cluster <CLUSTER_NAME> --name ng-user-compute-spot`
3. Delete nodes
   - DO NOT DELETE managed node (`ng-daskhub-services`)
   - Can delete each node using `eksctl delete nodegroup --cluster=<CLUSTER_NAME> --name=<NODE_GROUP_NAME>`

NOTE: If you get a FAIL from any above commands, you may want to go to AWS console to CloudFormation and look at stack status. Make sure all stacks are successfully deleted, then trigger a delete from the console for the stack in question

1. Stop managed node
   - `eksctl scale nodegroup --cluster=<CLUSTER_NAME> --name=<NODE_GROUP_NAME> --nodes-min 0`

2. Upgrade cluster through AWS Console
   - Search for EKS in the AWS toolbar
   - Select 'upgrade' on the cluster (as needed)

3. Update tooling
   - Execute `00-tools.sh` on EC2 instance

4. Rebuild nodegroups
   - Alter version in `cluster-config.yaml` files so the yaml version matches version changed to in EKS AWS Console
   - `eksctl upgrade cluster --name=<CLUSTER_NAME> --config-file cluster-config.yaml`

5. Update helm chart  
   - `helm install --version 2022.8.2 myrelease dask/dask`
   - OPTIONAL NOTE: IF you do 'helm repo update' you get a later version of daskhub `helm repo update`

6. Update the `dh-config.yaml` file to use latest container (TODO make this configurable and in `app.config`)
   
7.  Run helm
    - `helm upgrade daskhub dask/daskhub --namespace=<NAMESPACE> --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install --debug`

8.  Find and kill 'autohttps' pod
    - List the pods `kubectl --namespace=<NAMESPACE> get pod`
    - Identify 'autohttps'
        ```
        NAME                                              READY   STATUS    RESTARTS   AGE
        api-daskhub-dask-gateway-777666cfc7-dn6cx         1/1     Running   0          46m
        autohttps-9f776485c-vpncw                         2/2     Running   0          46m
        continuous-image-puller-49xxz                     1/1     Running   0          4m36s
        controller-daskhub-dask-gateway-b465c66df-jmjxl   1/1     Running   0          46m
        hub-6ffd77f4-hzzj6                                1/1     Running   0          4m34s
        proxy-75b958f4f4-q8j9t                            1/1     Running   0          4m35s
        traefik-daskhub-dask-gateway-6d6b6479c8-6drdw     1/1     Running   0          4m36s
        user-scheduler-698cd85687-jnm7h                   1/1     Running   0          46m
        user-scheduler-698cd85687-vzc2r                   1/1     Running   0          45m
        ```
    - Kill autohttps pod (it will auto-restart)
      - `kubectl -n <NAMESPACE> delete pod <POD_NAME>`
    - Verify it restarts

IF THINGS GO WRONG: try the following to help debug
`kubectl -n <NAMESPACE> get events --sort-by='{.lastTimestamp}'`


# Deleting Daskhub

In order to delete Daskhub from the Kubernetes need to follow instructions (uninstall helm) here where the namespace from these instructions is "daskhub":
https://phoenixnap.com/kb/helm-delete-deployment-namespace

If used the instructions above can call `helm uninstall daskhub --namespace <NAMESPACE>` to remove daskhub


## Tearing down HelioCloud Daskhub infrastructure
TODO edit this now, make a script that does this
1. Execute `99-delete-daskhub.sh` by running `./99-delete-daskhub.sh`
   - Uninstalls the helm chart, detaches the EFS mount, and tears down the Kubernetes cluster
   - If any failures can look in the AWS console for further debugging, most common failure is the EFS mounted target is still present and using the EKS VPC so the cluster is taken down (which will show cluster delete complete) but the cloudformation stack is still up with the VPC.  If this is the case, go into EFS > network and delete the troublesome mounted target.  Another issue may be that there is an existing Elastic Network Interface still up can go find these through EC2 > Network Interfaces
   - Note that some resources will persist and if you truly want them deleted you will need to delete them by hand (their retention policy is set to not delete by default). See [list of AWS resources](#things-that-persist) that persist.
2. Tear down the HelioCloud install Daskhub stack by calling `cdk destroy -c config=<CONFIGURING_FILE> HelioCloud-DaskHub` in your local terminal in the same way you deploy your cdk install

Make sure resources no longer exist before proceeding to next step as this can cause the infrastructure to get stuck in a dependency loop and require extensive troubleshooting.

# Notes

## OAuth Auto Login
OAuth is controlled by your institution's authorization method (AWS Cognito is described in this document) and used by JupyterHub under the hood.  The oauth access token will persist based on your authorization setup.  The default in AWS Cognito is 60 minutes.  This means that if you logout of the Daskhub and then click sign in it will auto login and bypass the login page if the token has not expired.  This is NOT a security issue, the token is behaving as set-up.  This does however mean that users cannot easily logout and have another user login on their same browser.  Institutions may adjust the token time of life in their own authorization tool per their needs.

## Things that persist
- EFS
- Persistent volume in EBS (under EC2)
- KMS
- S3 bucket