# HelioCloud Services Installation Project

This is a CDK project developed in Python to automate the deployment of a HelioCloud instance into an AWS account. It 
is organized as follows:

- base_aws - CDK stack(s) for configuring basic AWS services to prepare the environment (VPCs, subnets, IAM, etc) 
- base_auth - CDK stack(s) stacks for setting up HelioCloud end-user accounts, permissions & basic services
- base_data - CDK stack(s) for enabling this HelioCloud instance to register & store its own data sets, and publish those data sets as available to other HelioCloud instances
- dashboard - CDK stack(s) for deploying the HelioCloud user dashboard
- daskhub - CDK stack(s) for deploying the Daskhub as part of this HelioCloud instance
- binderhub - CDK stack(s) for deplying binderhub as part of this HelioCloud instance

`app.py` is the the CDK driver application for orchestrating the entire installation via the stacks defined above and a 
user supplied configuration file (see `config/dev.yaml` for an example). 

You can deploy the entire installation or portions of it by invoking `cdk deploy` with the config file of choice and
selection of stack(s) you wish to deploy. 

Deploying an entire HelioCloud:
```commandline
cdk deploy --all -c config=config/dev.yaml
```

Deploying just a single stack (the Data set buckets from base_data):
```commandline
cdk deploy DataSetsStack -c config=config/dev.yaml
```


# Development Instructions

## Setup Python Environment
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

## CDK Commands
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
