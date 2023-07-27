# HelioCloud

- [Overview](#overview)
- [Deployment](#deployment)
  - [Environment Preparation](#1-environment-preparation)
  - [Configuration](#2-configuration)
  - [Deploy](#3-deploy)
  - [Validate](#4-validate)
- [Operations](#operations)
  - [Ingester](#ingester)
- [Development](#development)


# Overview
This repository contains the core codebase, installer and associated tools for instantiating and managing a HelioCloud
instance in AWS. 

The HelioCloud instantiation process is implemented as an AWS CDK project that - when provided an instance configuration 
pulls in the necessary CDK Stack definitions and instantiates/updates a HelioCloud instance in a configured AWS account.

# Repository Organization
The Heliocloud deployment codebase is comprised of the following directories and related artifacts:
- `app.py` - the main CDK driver
- `instance/` - instance configuration files are stored here  (defaults and user provided overrides)
- `base_aws/` - the foundational CDK Stack for HelioCloud. This stack addresses VPC creation, foundational IAM accounts
and roles.
- `base_auth/` - CDK stack definition for provisioning user authentication and authorization services via Cognito. These
services are consumed by later Stacks:  Daskhub and User Portal namely. 
- `binderhub/` - contains a CDK Stack implementation and related tools for installing the Binderhub module
- `daskhub/` - contains a CDK Stack implementation & supporting scripts for installing HelioCloud's version of Daskhub. 
More details can be found in the Daskhub module [README.md](daskhub/README.md)
- `portal/` - contains a CDK Stack implementation & supporting scripts for installing HelioCloud's User Portal module. 
More details can be found in the Portal module's [README.md](portal/README.md)
- `registry/`- contains a CDK Stack implementation, Python code & supporting scripts for installing HelioCloud's Registry
module. More details can be found in the Registry module's [README.md](registry/README.md)
- `test/` - contains unit & integration tests for exercising the HelioCloud codebase.  Note:  Integration tests
require you have deployed a development instance of HelioCloud to AWS. 
- `tools/` - client side tools for administering and operating a Heliocloud instance


---
# Deployment
Deploying a HelioCloud instance is a simple matter of ensuring your local and AWS environments support the installation, 
setting a few configuration options to fine tune your deployment to your needs, running the CDK application and finally
doing a few quick checks to confirm your HelioCloud instance is operating correctly. 

## 1 Environment Preparation
A HelioCloud deployment requires certain pre-requesite steps be taken in your AWS and local environments to enable the CDK app to run to completion.  Please work through the following:
### Local Environment
- Install [Python 3.9](#https://www.python.org/downloads/release/python-390/) or later
- Install the [AWS Command Line Interface](#https://docs.aws.amazon.com/cli/index.html)
- Install and setup CDK (see [AWS install instructions](https://aws.amazon.com/getting-started/guides/setup-cdk/module-two/), 
note the requirement for `npm` and `Node.js`; currently nvm == 18.0.0 stable but currently 20.* fails).  You have AWS credentials set either with environment variables or 
`aws configure` to push anything to AWS account.
- `git clone` of the entire HelioCloud-Services repository.  `cd` into the `install` sub-dir for running the CDK project
- Install python virtual environment for the CDK deployment
  - `pip install virtualenv`
  - Once in the `install` subdirectory: `python -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -r requirements.txt`

### VPN Warning

If you are using a VPN, you may need to turn off the VPN for the environment setup steps (ex. the AWS bootstrap CDK installation step: `cdk bootstrap aws://[account]/[region] -c instance=[something]`). However, generally you should be able to run cdk commands on VPN.

#### TLS/Self-signed certificates
On certain networks with self-signed certificates, you may see the following error message (`Error: self-signed certificate in certificate chain`) when running `cdk` commands in verbose mode (`-v`).

CDK assumes the node TLS settings.  The following command will disable all TLS validation.  This should is a brute force approach to get past this issue and should not be .
```
export NODE_TLS_REJECT_UNAUTHORIZED=0
```

### AWS Environment
#### IAM Role
Your AWS permissions must allow you to create/modify/delete IAM roles and AWS resources, so verify that you have these permissions before beginning.  Our development roles are set such that our policy is:

- <details><summary>IAM Policy</summary><blockquote>
  
    ~~~
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "NotAction": [
                    "iam:*",
                    "organizations:*",
                    "account:*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iam:List*",
                    "iam:Get*",
                    "iam:Tag*",
                    "iam:Attach*",
                    "iam:Detach*",
                    "iam:Put*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iam:CreateServiceLinkedRole",
                    "iam:DeleteServiceLinkedRole",
                    "iam:ListInstanceProfilesForRole",
                    "organizations:DescribeOrganization",
                    "account:ListRegions"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iam:CreatePolicy",
                    "iam:CreatePolicyVersion",
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:CreateInstanceProfile",
                    "iam:AddRoleToInstanceProfile",
                    "iam:PassRole",
                    "iam:RemoveRoleFromInstanceProfile",
                    "iam:DeleteAccountPasswordPolicy",
                    "iam:DeleteGroupPolicy",
                    "iam:DeletePolicy",
                    "iam:DeletePolicyVersion",
                    "iam:DeleteRolePermissionsBoundary",
                    "iam:DeleteRolePolicy",
                    "iam:DeleteUserPermissionsBoundary",
                    "iam:DeleteUserPolicy",
                    "iam:DeleteInstanceProfile",
                    "iam:UpdateAssumeRolePolicy"
                ],
                "Resource": "*"
            }
        ]
    }
    ~~~
   </blockquote></details>
This is a very open role and not necessarily what you should set for your default user.  However, in order to run these instructions you must have IAM roles that allow creation/deletion of both IAM roles and policies.

#### Region
A HelioCloud instance runs within a single AWS region. Since the availability of individual AWS services can vary region to region, 
we have compiled below the list of AWS regions we know a HelioCloud instance can successfully operate within.
- us-east-1 (_preferred: the data for initial HelioClouds are here and there will be no egress costs_)

TODO: Get a list of regions a HelioCloud instance _should_ be able to be deployed into successfully

## 2 Configuration
A single HelioCloud deployment into an AWS account is referred to as a HelioCloud **instance**, in keeping with the idea
that you are _instantiating_ a HelioCloud using a certain set of parameters as provided by your instance's configuration file. 
Instance configuration files are stored in `instance/` of this installation project. There you will find the following:
- instance/default.yaml - A default configuration file used for ALL HelioCloud instance deployments. You can refer to this file to understand how you can fine tune your instance configuration. This file should not be altered as it is the base for deployment (add on YAML files override these settings)
- instance/example.yaml - An example configuration file showing the typical override settings that would be used when deploying a production HelioCloud instance.

The following steps will guide you through the process of making your own instance configuration file. 

### 2.1 Creating instance configuration
Make your own copy of the instance configuration example file found at `instance/example.yaml` using a name
you think appropriate for identifying your instance. In this example, we will call our instance `heliocloud`:
```commandline
cp instance/example.yaml instance/heliocloud.yaml
```

### 2.2 AWS Account ID & Region
First you need to obtain and specify the AWS Account ID and Region you want to deploy your HelioCloud instance into in your configuration file. In many cases, this is likely to be the Account ID and Region used when during your installation of the AWS CLI. However, the Account ID and Region is configurable to account for cases wherein you may deploy to other accounts/regions.

Obtaining your AWS Account ID can be accomplished via one of the following:
- Login to the AWS Console. Click on your username in the upper right hand corner. Select "Account". Your account id
will be presented on the billing screen.
- If have you installed and configured the AWS CLI, you can use the `sts` service to obtain your account id.  On the 
command line, run:
    ```commandline
    aws sts get-caller-identity
    ```
  This should return a response like:
    ```commandline
    {
        "UserId": "XYZ.......",
        "Account": "00.....",
        "Arn": "arn:aws:iam::00....."
    }
    ```
  The Account field is your AWS Account Id.

A valid region can be obtained by looking at the list of valid regions for HelioCloud deployment cited above. Additionally,
you can obtain your default AWS region via the AWS config file generated during installation of the AWS CLI. Run the 
following command on the command line:
```commandline
cat ~/.aws/credentials
```
You should get a response like:
```commandline
[default]
region = us-east-1
```

Now modify your instance configuration file to set the following from the above steps:
- AWS Account ID &  Region:
    ```yaml
    env:
      account: 12345678
      region: us-east-1
    ```

### 2.3 Modify instance configuration

Modify your newly created instance configuration to suit your HelioCloud instance. The following are common configuration changes that you either must alter or may want to consider altering:

- Your preference for VPC settings. Here we allow the AWS CDK to create a new VPC for our HelioCloud instance:
    ```yaml
    vpc:
      type: new
    ```
- Which HelioCloud modules you want activated. Here we will activate all of them:
    ```yaml
    enabled:
      registry: True
      portal: True
      daskhub: True
    ```
- The User Portal and Daskhub will require the Auth stack be installed, so we must provide an authentication domain prefix (this prefix must be unique across AWS for the entire region you are deploying into, if they already exist the deploy will partially fail and you will need to change to unique names, can only contain alphanumeric or hyphen characters:
    ```yaml
    auth:
      domain_prefix: "myorganization-helio"
    ```
- Registry module will require names for its public S3 buckets (these buckets must be unique across AWS for the entire region you are deploying into, if they already exist the deploy will partially fail and you will need to change to unique names, can only contain alphanumeric, hyphen, or period characters):
    ```yaml
    registry:
      bucketNames: [
                     "edu-myorganization-helio1",
                     "edu-myorganization-helio2"
                   ]
    ```
  
- The User Portal requires a domain URL, record, and the ARN corresponding to an active SSL certificate. 
    ```yaml
    portal:
      domain_url: "myorganization-domain.org"
      domain_record: "portal"
      domain_certificate_arn: "arn:aws:acm:[region]:[account]:certificate/[certificate-id]"
    ```
  For how to request a public certificate for your domain, see [here](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html#:~:text=Sign%20in%20to%20the%20AWS,name%20such%20as%20example.com%20.). 
  The user portal will be hosted at `[domain_record].[domain_url]` (e.g. `portal.myorganization-domain.org`). Make sure this is globally unique, otherwise deployment will not complete.

You may also refer to `instance/default.yaml` to gain a full understanding of all the configurable elements of your HelioCloud instance deployment. 

Finally, note that multiple instances of a HelioCloud can be deployed into a single AWS account by creating additional
instance config files stored in the `instance/` directory. This is especially useful when collaboratively developing
the platform within one AWS account, or allowing individual (sub)departments within an organization to have their own
HelioCloud instance deployed into an organization wide AWS account.

## 3 Deploy
Deployment of a HelioCloud instance is potentially a 2 step process consisting of:
- Running the CDK to install the CloudFormation stacks for your HelioCloud instance into your AWS account
- (if deploying the DaskHub) Executing the DaskHub follow up deployment steps
- (if deploying the User Portal) Make sure your machine is running Docker and that you are logged in. To set up, see [here](https://www.docker.com).

### 3.1 Check via AWS CDK
Deploying your configured HelioCloud instance is done via the AWS CDK, passing in your instance name as a context
variable. Getting started, it is useful to run the `cdk ls` command to see the names of the CloudFormation Stacks
that will be installed based on your instance configuration. 

Assuming your instance name is `heliocloud` and it is configured per the example in the previous section, try running:
```commandline
cdk ls -c instance=heliocloud
```
The following should appear:
```commandline
Using instance configured AWS account 12345678 and region us-east-1
Using newly created vpc: ${Token[TOKEN.608]}.
Deploying buckets: ['edu-myorganization-helio1', 'edu-myorganization-helio2']
heliocloud/Base
heliocloud/Auth
heliocloud/Registry
heliocloud/Daskhub
heliocloud/Ingester
heliocloud/Portal
```
Note that the names of each CDK Stack representing HelioCloud components have been returned with a prefix of `heliocloud/`, 
per the name of the HelioCloud instance being installed. This helps uniquely name and identify these Stacks should you 
install multiple HelioCloud instances in one AWS account. 

NOTE: This does not deploy your HelioCloud instance, it is verification that the project has compiled correctly.

(You can also use 'cdk synth' to see if everything will compile first, or just go right to the deploy.)

### 3.2 Deploy via AWS CDK

You can deploy your configured HelioCloud instance by running `cdk deploy` from the root of the `install` directory,
passing in the name of your instance as a context variable, along with the `-all` flag to tell CDK to deploy all the 
CloudFormation stacks required based on your instance's configuration. The following command would deploy a 
HelioCloud instance using the configuration at `instance/heliocloud.yaml`:

NOTE: deployment can take 10+ minutes depending on your configurations.

```commandline
cdk deploy --all -c instance=heliocloud
```

Subsequent an initial installation, you may want to (re)install some of the individual modules following a configuration
change or update. You can (re)deploy a single component in CDK by providing its FULL stack name to the deploy command.
Note that the full Stack name includes the instance name prefix (e.g. `heliocloud/`), as we saw when running `cdk ls`:

```commandline
cdk deploy heliocloud/Registry -c instance=heliocloud
```


### 3.3 Daskhub Installation
DaskHub has the initial infrastructure instantiated with this CDK project but currently requires the user to perform 
additional steps after logging into an admin EC2 instance.  The DaskHub installation assumes you have followed the above deployment instructions and builds upon this infrastructure. For the remainder of the installation instructions see the DaskHub 
installation instructions [here](daskhub/README.md).


## 4 Validate
TODO: I've just a deployment, so what should I check?
- Do an initial manual run of the Cataloger?  Make sure that the Data Set catalog has been produced?
- Login to Daskhub / User portal, start up an instance and run an example analytic?
- Check the CloudFormation templates in AWS console?
----
# Operations: Using your HelioCloud

## Registering DataSets
The HelioCloud's registry component is capable of ingesting and registering heliophysics data sets within your HelioCloud 
instance, thereby making them available via the registry's public S3 buckets and via the HelioCloud data sets API.  
This also makes said datasets available to other deployed HelioCloud instances. There are two steps to execute to 
register a new or updated data set within a HelioCloud:
- Execute an ingest job
- Run a catalog update

### Executing an ingest job
New or updated datasets are ingested into a HelioCloud registry via that Heliocloud's Ingest service - an AWS Lambda
deployed and configured as part of a HelioCloud. The ingest service executes a _job_, which is constructed by putting
your dataset files and accompanying metadata in a subfolder within the ingest service's s3 bucket, then running the 
ingest service via a commandline tool. The process of constructing and executing an ingest job is as follows:
1. Create a sub-folder in the ingest s3 bucket. For example, if your bucket was named `my.upload.bucket` in your 
instance configuration, a valid ingest job location would be `s3://my.upload.bucket/my_job`.

2. Upload the dataset files with an accompanying manifest CSV `manifest.csv` listing those
files along with the relevant metadata. The manifest file should sit at the root of the subfolder in the 
S3 bucket: `s3://my.upload.bucket/my_job/manifest.csv`. Example manifest file:
    ```text
    test, test, test
    more data
    ```
3. Create and upload a dataset entry file `entry.json` to provide the necessary meta-data about the data set in 
Registry this ingest job should update.  Example:
    ```json
    {
      "id" : "MyDataSet",
      "loc": "s3://my.public.heliocloud.bucket/mds",
      "title" : "My DataSet",
      "ownership" : {
        "description" : "Something about the data I want to upload ",
        "resource_id" : "SPASE-XYZ-124",
        "creation_date" : "2015-09-01T00:00:00",
        "citation": ".....",
        "contact": "Dr. Me, ephemerus.me@my_institution.edu",
        "about_url": "..."
      }
    }
    ```
   Fields should be filled out as follows:
   
    - **id** - the Registry identifier of the Data Set to add this data to.  Should be unique to this HelioCloud instance.
    - **loc** - the public s3 bucket and subfolder for the Data Set to add this data to (should be 1-to-1 with the **id**)
    - **title** - a short, human readable, descriptive name for the Data Set
    - **ownership** - this is a block of additional descriptive metadata about the DataSet (optional)

    The `entry.json` file should be placed adjacent to the `manifest.csv` at the root of the s3 upload bucket sub-folder.
    Example `s3://my.upload.bucket/my_job/entry.json`

4. Once the upload package is in place, the Ingest service can be invoked using the Python script
at `tools/ingest.py`, providing it the name of the HelioCloud instance and the sub-folder in 
in the S3 ingest bucket that the job is in:
    ```commandline
   python tools/ingest.py my_instance my_job
    
    ```
5. Completion of the ingest job can be confirmed by looking at either the ingest job sub-folder 
to confirm it is empty, or by checking the public S3 buckets in the HelioCloud registry to
confirm the new data was incorporated. 

### Updating the Catalog
After running an ingest job (or several),  updating the HelioCLoud's Registry catalog is necessary to make the data 
available through the HelioCloud data API:
TODO: Finish




-------
# Development 
HelioCloud is an open source offering and as such, we encourage community participation in its continued development. 
If you want to contribute to the HelioCloud installation CDK codebase, you will need to have a solid base of skills 
in the following:
- Amazon Web Services 
- The [AWS Cloud Development Kit](#https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html)
- [Python 3](#https://docs.python.org/3.9/index.html)
- [AWS SDK for Python (Boto3)](#https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- Git

Provided below are instructions for setting up your Python environment, familiarizing yourself with AWS CDK and 
understanding the layout of the codebase.

## Python Environment
This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Testing

### Unit Testing
The `test` directory contains a collection of unit and integration tests for exercising the HelioCloud codebase
and any development instance installed and operating in your AWS account. The `test/unit` sub-directory contains 
unit tests intended to cover any code developed for components of individual HelioCloud stacks, such as the `base_data` 
stack's Ingester & Registry lambda implemetations.  You can run the unit tests by invoking the Python interpreter with 
a sub-directory arguement for the stack sub-dir who's tests you want to run:
```commandline
% python test/unit/base_data
```
These tests can be run locally and have no requirement of access to an AWS account.


### Integration Testing
A few integration tests have been deployed to test certain modules of a deployed HelioCloud instance, such as its Registry.
These are very effective for helping ensure AWS services are being configured correctly by the CDK, and that any 
module specific features leveraging AWS resources (e.g. S3) are working correctly.  

The integration tests can be run by invoking the Python interpreter wth a sub-directory arguement of `test/integration`:
```commandline
% python test/integration
```


## AWS CDK Commands
There are multiple CDK commands to become familiar with to aid in testing and deploying 
a HelioCloud instance.

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

The `cdk.json` file tells the CDK Toolkit how to execute your app.

Typically, deploying a development HelioCloud instance using the codebase you are actively developing on means (re)deploying
using an instance configuration you have created for development purposes:
```commandline
% cdk deploy --all -c instance=my_dev_instance_name
```
.....where you have an instance configuration created at `instance/my_dev_instance_name.yaml`.

