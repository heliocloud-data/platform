# HelioCloud DaskHub installation instructions

- [HelioCloud DaskHub installation instructions](#heliocloud-daskhub-installation-instructions)
  - [About](#about)
  - [Preparation](#preparation)
    - [Single purpose region warning:](#single-purpose-region-warning)
    - [Configure your setup / tooling](#configure-your-setup--tooling)
      - [Initial infrastructure](#initial-infrastructure)
        - [Method 1: CloudFormation Template](#method-1-cloudformation-template)
        - [Method 2: AWS Console](#method-2-aws-console)
      - [Tooling](#tooling)
  - [Installation](#installation)
    - [Cluster (EKS) and Supporting Service (EFS, S3) Configuration and Deployment](#cluster-eks-and-supporting-service-efs-s3-configuration-and-deployment)
    - [(Optional but recommended) Set up Authentication and Authorization](#optional-but-recommended-set-up-authentication-and-authorization)
    - [AWS Cognito](#aws-cognito)
    - [DaskHub Deployment](#daskhub-deployment)
      - [(Optional but recommended) Domain Routing](#optional-but-recommended-domain-routing)
  - [Debugging](#debugging)
  - [Updating Daskhub](#updating-daskhub)
  - [Updating Kubernetes Cluster](#updating-kubernetes-cluster)
  - [Deleting Daskhub](#deleting-daskhub)
  - [Tearing down HelioCloud](#tearing-down-heliocloud)
  - [Notes](#notes)
    - [OAuth Auto Login](#oauth-auto-login)

## About
These are instructions about how to install the HelioCloud version of DaskHub in AWS.

## Preparation


### Single purpose region warning:

WARNING: you will want to pick a region in your account to deploy the HelioCloud Daskhub. The use of other AWS services like SageMaker in that same region should be avoided. Try to isolate use to only DaskHub in that region to make your life easier.

### Configure your setup / tooling

After you have selected a region in your account for Helio Daskhub to be operating in, you will need to configure your setup and tooling. 

Setup your admin machine as a new EC2 instance. This admin machine is where you will be running the Kubernetes install  and interacting with the Daskhub so it needs to have appropriate permissions (e.g. EKS). Our default image has SSM agent and we use a small instance (t2.micro).

There are 2 methods to set up the initial infrastructure: (1) CloudFormation template and (2) AWS console/CLI guide.  We suggest using our CloudFormation template for most users.  This method is intended to be used on a clean system that does not have any of the HelioCloud AWS resources already spun up and for those who do not need any significant configuration alterations.  We include alternative infrastructure setup instructions to use the AWS console. These are useful if you have some AWS resources partially setup (updated CloudFormation script does not rely on named roles).  Everything described using the AWS Console can also be done on the command line with AWS CLI, we do not include instructions on the AWS CLI for this portion of the guide but they can be found in the [AWS documentation](https://aws.amazon.com/cli/).

#### Initial infrastructure
##### Method 1: CloudFormation Template
0. [Create KeyPair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/create-key-pairs.html) or ensure that there is a KeyPair that you have the *.pem file for (this ensures you can log into the EC2 instance we are going to create and finish installation steps for).

1. Use AWS console or AWS CLI to generate a CloudFormation stack
    - This will create all the necessary AWS resources for our initial setup (EC2, S3, IAM roles and policies), we describe the steps in the AWS Console but can just use link if signed into AWS (list the us regions but can use for any region using the generic link or just changing the region once launched into the Console)
    -   | Region      | Launch Link |
        | ----------- | ----------- |
        | us-east-1      | [![alt text](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png "Title")](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=heliocloud-daskhub&templateURL=https://s3.amazonaws.com/helio-public/cloudformation_templates/cloudformation-ec2.yaml)       |
        | us-east-2      | [![alt text](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png "Title")](https://console.aws.amazon.com/cloudformation/home?region=us-east-2#/stacks/new?stackName=heliocloud-daskhub&templateURL=https://s3.amazonaws.com/helio-public/cloudformation_templates/cloudformation-ec2.yaml)       |
        | us-west-1      | [![alt text](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png "Title")](https://console.aws.amazon.com/cloudformation/home?region=us-west-1#/stacks/new?stackName=heliocloud-daskhub&templateURL=https://s3.amazonaws.com/helio-public/cloudformation_templates/cloudformation-ec2.yaml)       |
        | us-west-2      | [![alt text](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png "Title")](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=heliocloud-daskhub&templateURL=https://s3.amazonaws.com/helio-public/cloudformation_templates/cloudformation-ec2.yaml)       |                
        |generic (uses region you are logged into on AWS Console - can alter in Console)   | <details><summary>Generic launch link</summary><blockquote>[![alt text](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png "Title")](https://console.aws.amazon.com/cloudformation/home?#/stacks/new?stackName=heliocloud-daskhub&templateURL=https://s3.amazonaws.com/helio-public/cloudformation_templates/cloudformation-ec2.yaml) </blockquote></details>|
    - Search for CloudFormation in the AWS toolbar
    - Select "Create stack" > "With new resources(standard)"
    - Specify "Upload a template file" and upload the file in this repo - "deploy/cloudformation-ec2.yaml"
    - On the next page enter a stack name and select a KeyName (KeyPair), the rest of the parameters have default values, modify if necessary
    - Click through rest of pages and accept the disclaimer
    - This stack may take 5 minutes to complete, if it fails you can troubleshoot in the console or delete the stack and try Method 2


##### Method 2: AWS Console
This section is collapsed because it is not the preferred method.  This method is only recommended if Method 1 fails or partial AWS resources for HelioCloud have already been created.

<details><summary>Instructions</summary><blockquote>

1. Use AWS console to create S3 bucket
    - Search for S3 in the AWS toolbar
    - Select "Create bucket"
    - Enter a name (choose anything not already used)
    - Use the rest of the defaults and create bucket
    - Navigate to the S3 Properties and copy Amazon Resource Name (ARN) for next step

2. Use AWS console to create IAM policy named "helio-dh-policy"
    - Search for IAM in the AWS toolbar
    - Select policies
    - Select "Create policy"
    - Select JSON
    - Paste in the following json:
        ~~~~~
        {
          "Version": "2012-10-17",
          "Statement": [
              {
                  "Sid": "VisualEditor0",
                  "Effect": "Allow",
                  "Action": [
                      "s3:PutObject",
                      "s3:GetObject",
                      "s3:ListBucketMultipartUploads",
                      "s3:AbortMultipartUpload",
                      "s3:ListBucketVersions",
                      "s3:CreateBucket",
                      "s3:ListBucket",
                      "s3:DeleteObject",
                      "s3:GetBucketLocation",
                      "s3:ListMultipartUploadParts"
                  ],
                  "Resource": [
                      "<INSERT_S3_BUCKET_ARN>",
                      "<INSERT_S3_BUCKET_ARN>/*"
                  ]
              },
              {
                  "Sid": "VisualEditor1",
                  "Effect": "Allow",
                  "Action": "s3:ListAllMyBuckets",
                  "Resource": "*"
              }
          ]
        }
        ~~~~~
        - Replace `<INSERT_S3_BUCKET_ARN>` from previous step in json
        - Skip tag, select next, enter name "helio-dh-policy" and "Create policy"

3. Use AWS console to create IAM policy named "k8s-asg-policy"
    - Search for IAM in the AWS toolbar
    - Select policies
    - Select "Create policy"
    - Select JSON
    - Paste in the following json:
        ~~~~~
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "autoscaling:DescribeAutoScalingGroups",
                        "autoscaling:DescribeAutoScalingInstances",
                        "autoscaling:DescribeLaunchConfigurations",
                        "autoscaling:DescribeTags",
                        "autoscaling:SetDesiredCapacity",
                        "autoscaling:TerminateInstanceInAutoScalingGroup",
                        "ec2:DescribeLaunchTemplateVersions"
                    ],
                    "Resource": "*",
                    "Effect": "Allow"
                }
            ]
        }
        ~~~~~
        - Skip tag, select next, enter name "k8s-asg-policy" and "Create policy"      

4. Use AWS console to create IAM role named "Daskhub_admin"
    - Search for IAM in the AWS toolbar
    - Select roles
    - Select "Create role"
    - Use default AWS service
    - Select EC2 use case
    - Add the following policies to the role:
        - AdminstratorAccess
        - CloudWatchAgentAdminPolicy
        - CloudWatchAgentServerPolicy
        - AmazonSSMMangagedInstanceCore
    - Name: Daskhub_admin


5. Use AWS console to create an EC2 instance (virtual computer)
    - Search for EC2 in the AWS toolbar
    - Enter a name (choose anything not already used)
    - Select Linux AMI (can use default free level version, our default is “Amazon Linux 2 Kernel 5.10 AMI 2.0.20220719.0 x86_64 HVM gp2”))
    - Select instance type (we use default of t2.micro)
    - Select key pair or create one (you need access to the pem file from this key pair in order to SSH into the EC2 instance and complete rest of installation)
    - Rest of security groups and SSH traffic configurations can be left to default values

6. Use AWS console to attach "Daskhub_admin" to newly created EC2 instance
    - Search for EC2 in the AWS toolbar
    - Select newly create EC2 instance (with the name you chose)
    - Go to "Actions" > "Security" > "Modify IAM Role"
    - Find IAM role (Daskhub_admin) in drop down and click update
</blockquote></details>


#### Tooling
2. SSH into EC2 instance
    ~~~~
      ssh -i "<INSERT_PEM_FILENAME>" ec2-user@<INSERT_EC2_DNS_ADDRESS>
    ~~~~
    - In order to SSH you must point to the local copy of your pem file specified in the EC2 setup
    (must `chmod 400 <INSERT_PEM_FILENAME>` to have the correct permissions)
    - Can find `<INSERT_EC2_DNS_ADDRESS>` by looking under the EC2 AWS console under "Public IPv4 DNS" (only available if instance is running) or if you use CloudFormation, it is under the stack's output under PublicDNS

3. Get installation scripts on EC2 machine
    - Install git `sudo yum install git -y`
    - Clone installation repo `git clone https://git.mysmce.com/heliocloud/helio-daskhub-test.git`
        - Move into git repo `cd helio-daskhub-test`
        - While instructions under development must checkout working branch `git checkout origin/cloudformation_k8sconfig`


4. Install tools on EC2 machine
    - Move into installation repo `cd ~/helio-daskhub-test/deploy`
    - Execute `01-tools.sh`
      - This installs relevant command line tools (AWS CLI, kubectl - way to manage Kubernetes, eksctl - way to manage AWS clusters, helm - package manager for Kubernetes)
      - Also configures region for AWS CLI

## Installation

### Cluster (EKS) and Supporting Service (EFS, S3) Configuration and Deployment

5. Setup and deploy Kubernetes (K8s) on EC2 machine
    - Must have installed tools on EC2 machine per above instructions and be in the deploy folder of the repo
    - Can alter nodeGroups and managaedNodeGroups in `cluster-config.yaml.template` to suit your cluster (default has master and nodes where uses have spot nodes and users have 3 types of nodes - high compute user, high GPU user, and high compute burst)
    - Execute `02-deploy-k8s.sh`
        - May fail if region deploying in does not have those instance types, can modify the `cluster-config.yaml.template` file to remove or replace instance types that are available in region and rerun script
        - Can ensure persistent volumes are created by running `kubectl get pv` and `kubectl get pvc --namespace daskhub`
        - Can ensure autoscaling set by running `kubectl get deployments --namespace kube-system`


### (Optional but recommended) Set up Authentication and Authorization
### AWS Cognito

Optional but recommended (our Daskhub configuration files are written to assume authentication is through AWS Cognito but can be adjusted to use other standard authentication methods). Daskhub can be built without any authentication but this is not recommended. We highly recommend using some sort of authentication (see details for different authentication methods: [github](https://tljh.jupyter.org/en/latest/howto/auth/github.html), [google](https://tljh.jupyter.org/en/latest/howto/auth/google.html), [native auth](https://tljh.jupyter.org/en/latest/howto/auth/nativeauth.html), and more information on [Cognito](https://tljh.jupyter.org/en/latest/howto/auth/awscognito.html) - we do not recommend the other methods covered by that guide for security purposes)

If your institution already has an existing Cognito User Pool that matches the users you want to give Daskhub access you can skip to step 7

1. Use AWS Console to set up Cognito User Pool to manage credentials for log in/log out
    - Search for Cognito in the AWS toolbar
    - Create a user pool
    - Enter a name
    - Review defaults
        - Can choose to set up multi-factor authentication (MFA) if that is of interest to the institution
        - We change the following defaults:
          - Disable "User sign ups allowed?" (want to control who has access to Daskhub)
          - Add app client
            - Enter a name (this will be for the Daskhub application)
    - Finish

2. Set up domain name for Amazon Cognito to use in Daskhub configuration
    - Navigate to our newly created Cognito user pool (or existing)
    - Go to App integration > Domain name
    - Enter a domain prefix (this can be a unique name related to your institution)
    - Finish

3. Set up App Client under Cognito User Pool 
    - Navigate to our newly created Cognito user pool (or existing)
    - Go to App integration > App client settings
    - Check "Cognito User Pool" under Enable Identity Provider
    - Enter `https://<INSERT_HOST_NAME>/hub/oauth_callback` for the callback URL using your own hosted domain (required for this setup) as `INSERT_HOST_NAME`
        - Can use `https://localhost:80` for testing - will not work when daskhub is deployed
    - Enter `https://<INSERT_HOST_NAME>/logout` for the sign out url
        - Can use `https://localhost:80` for testing - will not work when daskhub is deployed
    - Check "Authorization code grant" under Allowed OAuth Flows
    - Check all allowed scopes (our default is to check all Allowed OAuth Scopes)

### DaskHub Deployment

https://saturncloud.io/blog/jupyterhub_security/

**Daskhub (and JupyterHub) can be set-up so that there is no authentication.  We do NOT recommend this as this will leave a public facing entrypoint to your AWS instance where malicious users can access your Daskhub**.  The current checked in DaskHub configuration leaves the authentication sections commented out.  Users can standup DaskHubs using this configuration file for testing but we recommend tearing it down immediately after debugging is complete.

See [AWS Cognito section](#aws-cognito) to set-up authentication through AWS. Also see https://saturncloud.io/blog/jupyterhub_security/ for detailed information about setting up DNS routing for DaskHub.

9. Alter Daskhub configuration file
    - Execute `03-daskhub-configs.sh` to copy and populate configuration file from our template
        - This generates copies of 3 configuration files
            - `dh-config.yaml` - this file contains the specifications of our exact Daskhub build and we will modify the template file as we perform updates.  This file assumes you have built K8s as above specifically the EFS and serviceaccount naming conventions (if this is not the case alter these sections)
            - `dh-secrets.yaml` - this file contains randomly generated API keys for JupyterHub and DaskHub, if you have specific API keys replace those instead
            - `dh-auth.yaml` - this file contains authentication components of the Daskhub.  This is optional but highly recommended (do this as soon as possible!).  Must replace all values that contain `<INSERT_******>`  and see comments for any other changes. NOTE: you can set this up right away if you've set up AWS Cognito and have an external domain, if not you will have to update the Daskhub after deploying without authentication
                - Template shows how to configure authentication through AWS Cognito see [here] (https://z2jh.jupyter.org/en/latest/administrator/authentication.html) for alternative authentication options
                - Edit the following commented out sections of "dh-config.yaml" 
                -  Need to grab `client_id` and `client_secret` from AWS Cognito App clients.  `oauth_callback_url` needs to be `https://<INSERT_HOST_NAME>/hub/oauth_callback` for the callback URL using your own hosted domain.  The `authorize_url`, `token_url`, and `userdata_url` need to be changed so the front part of the url aligns with what is specified in AWS Cognito Domain name.  Change scope to match AWS Cognito App client settings 
                - For more details about HTTPS see [details](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/security.html#set-up-automatic-https)
                - Example of populated `dh-auth.yaml`:
                ``` yaml
                jupyterhub:
                    hub:
                        config:
                        Authenticator:
                            auto_login: true
                        GenericOAuthenticator:
                            admin_users:
                            - admin1@institution.org
                            - admin2@test.com
                            login_service: "AWS Cognito"
                            client_id: 111111111
                            client_secret: 123456789101112
                            oauth_callback_url: https://hub.mydomain.org/hub/oauth_callback
                            authorize_url: https://domain-test.auth.us-east-1.amazoncognito.com/oauth2/authorize
                            token_url: https://domain-test.auth.us-east-1.amazoncognito.com/oauth2/token
                            userdata_url: https://domain-test.auth.us-east-1.amazoncognito.com/oauth2/userInfo
                            scope:
                            - openid
                            - phone
                            - profile
                            - email
                        JupyterHub:
                            authenticator_class: generic-oauth
                    proxy:
                        https:
                        enabled: true
                        hosts:
                            - hub.mydomain.org
                        letsencrypt:
                            contactEmail: admin2@test.com
                ```

10. Install and deploy the Daskhub helm chart
    - This will use Helm (a K8s package manager) to get Daskhub running on our cluster
    - Run `helm repo add dask https://helm.dask.org/`
    - Run `helm upgrade daskhub dask/daskhub --namespace=daskhub --values=dh-config.yaml --values=dh-secrets.yaml --version=2022.8.2 --install `
      - If you have all AWS Cognito setup,an external domain, and have altered `dh-auth.yaml` accordingly (see priot step) then you can instead run `helm upgrade daskhub dask/daskhub --namespace=daskhub --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install` 
      - If you receive an error on this execute see this [link](https://stackoverflow.com/questions/72126048/circleci-message-error-exec-plugin-invalid-apiversion-client-authentication)

11. Get Daskhub LoadBalancer url
    - Get URL to access Daskhub
    - Run `kubectl --namespace=daskhub get svc proxy-public`
      - May need to wait until pods are full spun up, can check if they are in a ready state with `kubectl --namespace=daskhub get pod`
    - Enter url into web browser to ensure it is accessible (may take a few minutes even if the pods are in ready state)


#### (Optional but recommended) Domain Routing
If you want to be able to access the daskhub from a human readable URL can get or use an existing domain in Route 53

See https://saturncloud.io/blog/jupyterhub_security/ for detailed information about setting up DNS routing for DaskHub.

12.	To use Route 53 navigate to it in AWS Console
	- Create a hosted zone using your domain (if you purchase through AWS it automatically sets up a hosted zone)
        - If you have an existing domain you must port it through
    - Create a new alias record with the copied URL from step 12 (Kubernetes load balancer proxy-public).  
        - Use CNAME (this means the record will map to another hostname, in this case this is the `proxy-public EXTERNAL-IP` generated by Daskhub - the LoadBalancer url)
        - This name will be the site that users navigate to get to the spun up daskhub

13.	May need to update DaskHub with this new DNS.
    - Replace new alias name in `dh-auth.yaml` in the `https.hosts` (from `example.com` to your actual domain name) and `GenericOAuthenticator.oauth_callback_url` (to your actual domain name plus `/hub/oauth_callback` this part is a built-in linkage in jupyterhub)
    - To update Daskhub run `helm upgrade daskhub dask/daskhub --namespace=daskhub --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install` again

14.	If using AWS Cognito update App client
    - Navigate to your Cognito user pool
    - Go to App integration > App client settings
    - Check "Cognito User Pool" under Enable Identity Provider
    - Enter `https://<INSERT_HOST_NAME>/hub/oauth_callback` for the callback URL in `dh-auth.yaml` using your own hosted domain (what you just put in step 13 under `GenericOAuthenticator.oauth_callback_url`)
    - Enter `https://<INSERT_HOST_NAME>/logout` in `dh-auth.yaml` for the sign out url (same host name as above)
    - Check "Authorization code grant" under Allowed OAuth Flows
    - Check all allowed scopes (our default is to check all Allowed OAuth Scopes)
    - Edit Appclient settings in AWS Cognito App client so that the callbacks use the new hostname (App client settings)


Congratulations! At this point you should have a working HelioCloud DaskHub environment.
Go to the Daskhub Frontend URL you just configured or the DNS you just created and try logging in.


## Debugging
Some debugging tips in no particular order

- Check logs
Can check pod logs by first finding pod name using `kubectl -n daskhub get pods` and then `kubectl -n daskhub logs <pod_name>`

- Restart pod by killing it
    - Can kill a pod and it will restart `kubectl -n daskhub delete pod <pod_name>`

- Check helm configuration
    - Can examine if helm configuration files are not being parsed properly by adding `--dry-run --debug` to helm command, can also save to output file.  

    - Example:
    `helm upgrade daskhub dask/daskhub --namespace=daskhub --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install --dry-run --debug > test.out`

- Check event stack
    - It can be helpful to look at the event stack for your pods using:
        ~~~~~
        kubectl -n daskhub get events --sort-by='{.lastTimestamp}'
        ~~~~~

- Turn on jupyterhub debugging
    You can also turn on 'debugging' in jupyterhub. Edit the dh-config.yaml file so that:
    ~~~
    jupyterhub:
    debug:
        enabled: true
    ~~~

- Check AWS regional availability
    - Image pull problems can be related to regional availability. Use the following command to verify availability for your region.
    -
        ~~~~
        aws ec2 describe-instance-type-offerings --location-type availability-zone  --filters Name=instance-type,Values=c5.xlarge --region us-east-1 --output table
        ~~~~


- Force node to scale up
   -  
    ~~~~
    eksctl scale nodegroup --cluster helio-dask-alt --name=ng-user-compute-spot --nodes-min=1
    ~~~~

## Updating Daskhub

To update Daskhub you can alter any of the configuration files and then run `helm upgrade daskhub dask/daskhub --namespace=daskhub --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install`

NOTE: often changes can take a minute or two to propogate through the system.

## Updating Kubernetes Cluster

1. Find nodes
   -  To list the worker nodes registered to the Amazon EKS control plane, run the following command:

        ```
        [centos@ip-172-31-90-70 ~]$ eksctl get nodegroup --cluster <clusterName>
        CLUSTER		NODEGROUP		STATUS		CREATED			MIN SIZE	MAX SIZE	DESIRED CAPACITY	INSTANCE TYPE	IMAGE ID		ASG NAME		TYPE
        eks-helio	ng-burst-compute-spot	CREATE_COMPLETE	2022-10-11T16:19:55Z	0		10		0			m5.8xlarge	ami-099c768b04001b983	eksctl-eks-helio-nodegroup-ng-burst-compute-spot-NodeGroup-1CBEMPEXLSKOS	unmanaged
        eks-helio	ng-daskhub-services	ACTIVE		2022-10-11T16:20:28Z	1		1		1			t3a.medium	AL2_x86_64		eks-ng-daskhub-services-98c1e3ec-7689-7a38-830d-011e2be4cbc6			managed
        eks-helio	ng-user-compute-spot	CREATE_COMPLETE	2022-10-11T16:19:55Z	0		15		0			m5.xlarge	ami-099c768b04001b983	eksctl-eks-helio-nodegroup-ng-user-compute-spot-NodeGroup-1B379X9Q74QA9		unmanaged
        eks-helio	ng-user-gpu-spot	CREATE_COMPLETE	2022-10-11T16:19:55Z	0		5		0			g4dn.xlarge	ami-0cb17a7e952cabb92	eksctl-eks-helio-nodegroup-ng-user-gpu-spot-NodeGroup-1E03TASV0OF6E		unmanaged
        ```
1. Drain nodes
   - Drain each node using `eksctl drain nodegroup --cluster=<clusterName> --name=<nodegroupName> `
      - Ex. `eksctl drain nodegroup --cluster eks-helio --name ng-user-compute-spot`
2. Delete nodes
   - DO NOT DELETE managed node (`ng-daskhub-services`)
   - Delete each node using `eksctl delete nodegroup --cluster<clusterName> --name=<nodegroupName>`

NOTE: pay attention to the output from above steps!, you may get a FAIL.
In this case you may want to go to AWS console, CloudFormation and look at stack status. Make sure all stacks are successfully deleted, trigger a delete from the console for the stack in question

1. Stop managed node
   - `eksctl scale nodegroup --cluster=eks-helio --name=ng-daskhub-services --nodes-min 0`

2. Upgrade cluster through AWS Console
   - Search for EKS in the AWS toolbar
   - Select 'upgrade' on the cluster (as needed)

3. Update tooling
   - Execute `01-tools.sh` from `helio-daskhub-test/deploy` on EC2 instance

4. Rebuild nodegroups (TO DO: test doing this without having individual nodegroup files, can we update cluster with cluster-config.yaml?)
   - Alter version in node yaml files so the yaml version matches version changed to in EKS AWS Console
   - `eksctl create nodegroup -f 08-ng-user-compute.yaml`
   - `eksctl create nodegroup -f 08-ng-user-gpu.yaml`

5. Update helm chart  
   - `helm install --version 2022.4.1 myrelease dask/dask`
   - OPTIONAL NOTE: IF you do 'helm repo update' you get a later version of daskhub `helm repo update`

6. Update config of dh-config to use latest container
   - ```
     cd helio-daskhub
     git pull origin main
     ```

7. Verify change and edit the 'dh-config.yaml' file
8.  Run helm
    - `helm upgrade daskhub dask/daskhub --namespace=daskhub --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install --debug`

9.  Find and kill 'autohttps' pod
    - List the pods `kubectl --namespace=daskhub get pod`
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
      - `kubectl -n daskhub delete pod autohttps-9f776485c-vpncw`
    - Verify it restarts


IF THINGS GO WRONG: try the following to help debug
`kubectl -n daskhub get events --sort-by='{.lastTimestamp}'`



## Deleting Daskhub

In order to delete Daskhub from the Kubernetes need to follow instructions (uninstall helm) here where the namespace from these instructions is "daskhub":
https://phoenixnap.com/kb/helm-delete-deployment-namespace

If used the instructions above can call `helm uninstall daskhub --namespace daskhub` to remove daskhub


## Tearing down HelioCloud
1. [Delete Daskhub](#deleting-daskhub)
2. Delete the EFS either through the AWS console or AWS CLI
    - Search EFS in the AWS Console
    - Select filesystem (default name is eks-helio-test) and click delete
3. Can delete EKS through eksctl (recommended) or through the AWS console of AWS CLI
    - In a SSH session on the EC2 admin machine run `eksctl delete cluster --name <EKS_CLUSTER>`
      - Can find `<EKS_CLUSTER>` through `eksctl get clusters` or through the AWS EKS console on by looking at the `02-deploy-k8s.sh` value for `EKS_NAME`
    - Alternative method (Less recommended)
      - Search Cloudformation in the AWS Console
      - Delete stacks with the relevant name (default is eks-helio-test), delete all of these in the reverse order they were created.  Order doesn't necessarily matter except "eksctl-eks-helio-test-cluster" or if using another name the one ending in "cluster" must deleted last
4. Delete EC2 related cloudformation stack (MUST BE DONE LAST OTHERWISE CAN CAUSE DEPENDENCY ISSUES)
    - Search Cloudformation in the AWS Console
    - Delete stack created in [initial infrastructure](#initial-infrastructure) default name is "heliocloud-daskhub"

Make sure resources no longer exist before proceeding to next step as this can cause the infrastructure to get stuck in a dependency loop and require extensive troubleshooting.

## Notes

### OAuth Auto Login
OAuth is controlled by your institution's authorization method (AWS Cognito is described in this document) and used by JupyterHub under the hood.  The oauth access token will persist based on your authorization setup.  The default in AWS Cognito is 60 minutes.  This means that if you logout of the Daskhub and then click sign in it will auto login and bypass the login page if the token has not expired.  This is NOT a security issue, the token is behaving as set-up.  This does however mean that users cannot easily logout and have another user login on their same browser.  Institutions may adjust the token time of life in their own authorization tool per their needs.