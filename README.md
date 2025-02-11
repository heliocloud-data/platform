[![Coverage](https://gitlab.smce.nasa.gov/heliocloud/platform/badges/develop/coverage.svg)](https://gitlab.smce.nasa.gov/api/v4/projects/139/jobs/artifacts/develop/download?job=coverage)
[![pylint](https://gitlab.smce.nasa.gov/heliocloud/platform/-/jobs/artifacts/develop/raw/public/pylint.svg?job=static-analysis)](https://gitlab.smce.nasa.gov/api/v4/projects/139/jobs/artifacts/develop/raw/pylint.txt?job=static-analysis)

# HelioCloud

- [Overview](#overview)
- [Deployment](#deployment)
  - [Environment Preparation](#1-environment-preparation)
  - [Configuration](#2-configuration)
  - [Deploy](#3-deploy)
  - [Validate](#4-validate)
- [Development](#development)


# Overview
This repository contains the core codebase, installer and associated tools for instantiating and managing a HelioCloud
instance in AWS. 

The HelioCloud instantiation process is implemented as an AWS CDK project that - when provided an instance configuration 
pulls in the necessary CDK Stack definitions and instantiates/updates a HelioCloud instance in a configured AWS account.

---
# Deployment
Deploying a HelioCloud instance is a simple matter of ensuring your local and AWS environments support the installation, 
setting a few configuration options to fine tune your deployment to your needs, running the CDK application and finally
doing a few quick checks to confirm your HelioCloud instance is operating correctly. 

## 1 Environment Preparation
A HelioCloud deployment requires certain pre-requisite steps be taken in your AWS and local environments to enable the CDK app to run to completion.  Please work through the following:

### 1.1 Local Environment Setup & cloning HelioCloud repository
- Install [Python 3.9](#https://www.python.org/downloads/release/python-390/) or later
- Install [Docker](#https://docs.docker.com/get-docker/)
- Install the [AWS Command Line Interface](#https://docs.aws.amazon.com/cli/index.html)
- Install and setup AWS CDK (see [AWS install instructions](https://aws.amazon.com/getting-started/guides/setup-cdk/module-two/), 
note the requirement for `npm` and `Node.js`; currently nvm == 18.0.0 stable but currently 20.* fails).  You have AWS credentials set either with environment variables or 
`aws configure` to push anything to AWS account.
- Do a `git clone` of this repository
- `cd` into the repository and instantiate a Python virtual environment:
```shell
pip install virtualenv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### VPN Warning

If you are using a VPN, you may need to turn off the VPN for the environment setup steps (ex. the AWS bootstrap CDK installation step: `cdk bootstrap aws://[account]/[region] -c instance=[something]`). However, generally you should be able to run cdk commands on VPN.

#### TLS/Self-signed certificates
On certain networks with self-signed certificates, you may see the following error message (`Error: self-signed certificate in certificate chain`) when running `cdk` commands in verbose mode (`-v`).

CDK assumes the node TLS settings.  The following command will disable all TLS validation.  This should is a brute force approach to get past this issue and should not be .
```
export NODE_TLS_REJECT_UNAUTHORIZED=0
```

### 1.2 AWS Environment
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
A HelioCloud instance runs within a single AWS region. The availability of individual AWS services 
and various images or configurations they can be deployed within can vary from region to region. 

Currently, all HelioCloud development and testing has been done using `us-east-1`, however that isn't
to say you can't _try_ to deploy it into another. Should you encounter any issues doing so, 
please reach out to the HelioCloud development team and let us know.  We are actively working to 
ensure HelioCloud is deployable to any/all AWS regions.

## 2 Configuration
A single HelioCloud deployment into an AWS account is referred to as a HelioCloud **instance**, in keeping with the idea
that you are _instantiating_ a HelioCloud using a certain set of parameters as provided by your instance's configuration file. 
Instance configuration files are stored in `instance/` of this installation project. There you will find the following:
- instance/default.yaml - A default configuration file used for ALL HelioCloud instance deployments. You can refer to this file to understand how you can fine tune your instance configuration. This file should not be altered as it is the base for deployment (add on YAML files override these settings)
- instance/example.yaml - An example configuration file showing the typical override settings that would be used when deploying a production HelioCloud instance.

The following steps will guide you through the process of creating your own instance configuration file in preparation for a deployment.

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
- The User Portal and Daskhub will require the Auth stack be installed, so we must provide an authentication `domain_prefix` (this prefix must be unique across AWS for the entire region you are deploying into, if they already exist the deploy will partially fail and you will need to change to unique names, can only contain alphanumeric or hyphen characters).  Additional settings include `deletion_protection`, which prevents this resource from being deleted (`True` is recommended for production deployments) and `removal_policy`, which specifies what should happen to the underlying cogniot resources when this stack is destroyed (`RETAIN` is recommended for production deployements, valid values are `DESTROY`, `RETAIN` and, `SNAPSHOT`):
    ```yaml
    auth:
      domain_prefix: "myorganization-helio"
      deletion_protection: True
      removal_policy: RETAIN
    ```

- The User Portal and Daskhub can optionally use the Identity stack as a means of notify your users when creating new user accounts.  To enable this feature set `use_custom_email_domain` to `True`:
    ```yaml
    email:
      use_custom_email_domain: False
      user: "no-reply"
      from_name: "My Organization"
    ```

- Registry module is still in progress, will be updated by v1.2.  It assists in making data shareable in S3 buckets.
  
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

### 2.4 Storing your instance configuration 
If multiple individuals will be managing the deployment and update of a single HelioCloud instance,
you will want to make the instance configuration in `instance/` available to them. Possible ways to 
do this are:
- Store the instance configuration in your own clone of the HelioCloud platform git repository
and check it in to whatever Git compatible source control system you are using/familiar with
- Store the instance configuration in an AWS S3 bucket in the AWS account your HelioCloud instance
has been deployed into.



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
cdk deploy heliocloud/Daskhub -c instance=heliocloud
```


### 3.3 Daskhub Installation
DaskHub has the initial infrastructure instantiated with this CDK project but currently requires the user to perform 
additional steps after logging into an admin EC2 instance.  The DaskHub installation assumes you have followed the above deployment instructions and builds upon this infrastructure. For the remainder of the installation instructions see the DaskHub 
installation instructions [here](daskhub/README.md).


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

## 1. Development Environment Setup
You can begin by following the steps in [Environment Preparation](#1-environment-preparation) as if 
you were preparing to do your own HelioCloud instance setup and deployment. This will initialize a 
proper Python3 virtual environment with the correct dependencies installed.  Following that,
you should install the development dependencies as well so you have access to the proper tools:

```shell
$ pip install -r requirements-dev.txt
$ pre-commit install
$ pre-commit autoupdate # ensures that pre-commit tools are using up-to-date versions
```

The [pre-commit](https://pre-commit.com) is required to ensure that linting and formatting tools are run against your code before committing to your local repository.

You may use whatever Python IDE you are comfortable with it,
though the core development team has preferred [PyCharm](https://www.jetbrains.com/pycharm/).

After installing your IDE and dev dependencies, you should be ready to go about making your changes.

## 2. Understanding an AWS CDK project

### 2.1 Platform codebase layout
The HelioCloud platform has been implemented as an AWS CDK project and sticks closely to the 
best practices and conventions for one. The following files & subdirectories comprise the CDK
app implementation:
- `app.py` contains the HelioCloud CDK App definition. It is required by the CDK commandline tool, 
containing all the specifics of how each CDK Stack comprising the platform is to be configured and
deployed via AWS CloudFormation templates. CDK Stacks are used to decompose the deployment of a
CDK app into manageable components that can be defined and deployed individually if you so chose - 
with some stacks referencing dependencies on others.
- `base_aws` is the foundational CDK stack for HelioCloud. It handles AWS VPC creation, as well as 
creating IAM accounts & roles used across multiple HelioCloud components.
- `base_auth` defines the instantiation of AWS Cognito to provide use authentication and 
authorization services for other HelioCloud components: Daskhub & User Portal.
- `daskhub` defines the instantiation of HelioCloud`s version of a Daskhub cluster. More details
can be found in the Daskhub [README.md](daskhub/README.md).
- `portal` defines the instantiation of and supporting resources for installing HelioCloud`s
User Portal module. More details can be found in the Portal [README.md](portal/README.md).

Each stack directory contains its own `_stack.py` Python file containing the CDK stack implementation
for that particular stack.


Additionally, you will note several other directories that comprise important part`s of the 
codebase:
- `test` contains unit and integration tests for HelioCloud platform. _Note_: Using integration tests
will require you to have deployed a development instance of HelioCloud to AWS.
- `tools` contains client side tools for administering and operating a HelioCloud instance.
- `instance` contains the default configuration file `default.yaml`, which you will want to refer
to and update if making any changes that impact HelioCloud's configurability. 


The vast majority your changes will probably go in one of `app.py`, a `_stack.py` file, or to the 
resources within the stack directories.


### 2.2 CDK Command line
You will need to develop a sound understanding of the AWS CDK command line utility in order to review
and test your changes. There are multiple CDK commands to become familiar with to aid in testing
changes locally, and deploying your updates to your HelioCloud development instance:

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



## 3 Testing
All HelioCloud test fixtures and tooling are present under `test`.  Go here for adding
unit tests, integration tests and any related code or tools.

### 3.1 Unit Testing
The `test/unit` directory contains a collection of unit and integration tests for exercising the HelioCloud codebase,
with the subdirectories within organized to match the top-level directories containing the 
code to test:
- `test/unit/tools` contains unit test code for the tools module
...and so forth.

You can run the unit tests for a particular module via the Python interpreter:
```shell
python test/unit/tools
```

All of these tests can by run locally, with no requirement of a deployed HelioCloud instance or
AWS account.


### 3.1 Integration Testing
Integration tests have been developed in `test/integration` to exercise certain features of a 
deployed HelioCloud 
development instance. These are very effect for ensuring that AWS services are being configured
correctly by the CDK, and that any module specific features leveraging AWS resources (e.g. S3) 
are working correctly.

Integration tests are invoked the same way as unit tests:
```shell
python test/integration
```

### 4 Prepping your changes as a pull or merge request

*The following is performed automatically by `pre-commit`.*

After completing and testing your changes, you will want to take some additional steps to maximize
the potential that the pull or merge request you put together is accepted. We recommend you:
- Run `black` to format all of your changes in keeping with HelioCloud's code formatting conventions
```shell
black .
```
- Run `pylint` to conduct a static code analysis of the codebase and see if you introduced any errors,
deviations from coding standards, etc. 
```shell
pylint *
```

Provided you get clean feedback from black & pylint and your tests pass, you should feel
pretty comfortable any merge request you post would get rejected for not adhering to the 
codebase conventions.
