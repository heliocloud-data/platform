# HelioCloud Services Installation Project

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

This is an AWS CDK project developed in Python to automate the deployment of a HelioCloud instance into an AWS account.
It is implemented as a collection of AWS CDK Stacks that provision key components of a HelioCloud instance as single,
deployable units via AWS Cloud Formation. The project is organized as follows:

_CDK Deployment Codebase_
- base_aws - CDK stack(s) for configuring certain AWS services depended upon by all (or most) of the HelioCloud's components
- base_auth - CDK stack(s) for configuring AWS services to enable HelioCloud end-user authentication and authorization
- base_data - CDK stack(s) for deploying HelioCloud's Data Set Registry component for ingesting, storing and sharing heliophysics data sets across HelioCloud instances
- portal - CDK stack(s) for deploying HelioCloud's User Portal component
- daskhub - CDK stack(s) for deploying HelioCloud's Daskhub component
- config - default and example config files to use when invoking this CDK package. See `config/dev.yaml` for current defaults and required fields.
- `app.py` - main CDK driver


_Other_
- tests - contains various unit and integration tests for the CDK project. Run the `runtests.sh` shell script to execute the Python unit tests. These are not required for deployment.

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

If you are using a VPN, you may need to turn off the VPN for the environment setup steps (ex. the AWS bootstrap CDK installation step: `cdk boostrap aws://ACC/us-east-1`). However, generally you should be able to run cdk commands on VPN.



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

You may also refer to `instance/default.yaml` to gain a full understanding of all the configurable elements of your HelioCloud instance deployment. 

Finally, note that multiple instances of a HelioCloud can be deployed into a single AWS account by creating additional
instance config files stored in the `instance/` directory. This is especially useful when collaboratively developing
the platform within one AWS account, or allowing individual (sub)departments within an organization to have their own
HelioCloud instance deployed into an organization wide AWS account.

## 3 Deploy
Deployment of a HelioCloud instance is potentially a 2 step process consisting of:
- Running the CDK to install the CloudFormation stacks for your HelioCloud instance into your AWS account
- (if deploying the DaskHub) Executing the DaskHub follow up deployment steps

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
Note that the name's of each CDK Stack representing HelioCloud components have been returned with a prefix of `heliocloud/`, 
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
# Operations

## Ingester
The HelioCloud's Registry component is capable of ingesting and registering heliophysics data sets within your HelioCloud 
instance, thereby making them available the Registry's public S3 buckets and via the HelioCloud data sets API.  This also
makes said datasets available to other deployed HelioCloud instances. This is accomplished by way of the _Ingester_ lambda
function deployed as part of the Registry stack.

The _Ingester_ lambda is currently intended to be invoked via the AWS CLI. Invocation is expecting an upload package 
comprised of:
1. An S3 bucket with a sub-folder containing a directory tree of files to ingest into the Registry. 
Example: `s3://my.upload.bucket/upload`
2. A manifest CSV file `manifest.csv` containing a list of the files in the tree to ingest, along with key metadata. The
manifest file should sit at the root of the subfolder in the S3 bucket: `s3://my.upload.bucket/upload/manifest.csv`
3. An entry JSON file `entry.json` that provides meta-data about the data set in the Registry into which this upload
should be installed. Example:
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
    Example `s3://my.upload.bucket/upload/entry.json`

Once the upload package is in place, the Ingester can be invoked from the AWS CLI as follows:
```commandline
aws lambda invoke \
    --cli-binary-format raw-in-base64-out \
    --invocation-type Event \
    --function-name Ingester \
    --payload '{ "upload_path" : "s3://my.upload.bucket/upload/", "manifest" : "manifest.csv", "entry" : "entry.json" }' \
    results.json
```
Note that we invoke the AWS Lambda asynchronously via `invocation-type Event`. This is intentional as most upload jobs 
will take several minutes - dependent of course on the volume of data being processed. Synchronous calls would be 
prone to timing out on the command line.

Completion of the upload job can be confirmed by looking at the destination bucket subfolder (`s3://my.public.heliocloud.bucket/mds`)
to see if the ingested data is present and a CSV placed in the destination bucket subfolder named `<id_year>.cvs`. 
Example `s3://my.public.heliocloud.bucket/mds/MyDataSet_2023.csv`.

TODO: Add instructions for tailing the Ingest Lambda logs.



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


## AWS CDK Commands
There are multiple CDK commands to become familiar with to aid in testing and deploying 
a HelioCloud instance.

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

The `cdk.json` file tells the CDK Toolkit how to execute your app. 

## Code Structure
Per the introduction above, this project is divided into individual CDK Stacks for each major component of a HelioCloud
installation - data, auth, daskhub, etc.  As such, extending the HelioCloud installation means adding your Stack implementation to a sub-folder 
of the `install` directory under which this project exists, then updating `app.py` to call your additional CDK Stack(s).