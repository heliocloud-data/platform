#!/usr/bin/env python3
import os
import yaml
import aws_cdk as cdk

from base_aws.base_aws_stack import BaseAwsStack
from base_auth.authorization_stack import AuthStack
from base_data.data_sets_stack import DataSetsStack
from base_data.registry_stack import RegistryStack
from daskhub.daskhub_stack import DaskhubStack
from dashboard.dashboard_stack import DashboardStack
from binderhub.binderhub_stack import BinderhubStack

# Initialize the CDK app
app = cdk.App()

# Get the configuration file to use for determining bucket count & names
config_file = app.node.try_get_context("config")
if config_file is None:
    raise Exception("No configuration file was specified. Re-run using flag '-c config=<name of config file>")

print("Using configuration file " + config_file)
with open(config_file, 'r') as file:
    config = yaml.safe_load(file)

# Required:  Deploy the Base AWS Stack to make sure the AWS account environment is properly configured
base_stack = BaseAwsStack(app, "HelioCloud-BaseAwsStack",
                          description="AWS resources necessary to deploy any HelioCloud instance")

# Determine optional components to deploy
components = config['components']

# Enable registry?
if components.get('enableRegistry', False):
    DataSetsStack(app, "HelioCloud-PublicDataStorage",
                  description="HelioCloud public S3 buckets").add_dependency(base_stack)
    RegistryStack(app, "HelioCloud-PublicDataRegistry",
                  description="HelioCloud data loading & registration").add_dependency(base_stack)

# Check for the other stacks to deploy
daskhub = components.get('enableDaskHub', False)
binderhub = components.get('enableBinderHub', False)
dashboard = components.get('enableUserDashboard', False)
if daskhub or binderhub or dashboard:

    # Each of these stacks require the Auth stack be deployed first
    auth_stack = AuthStack(app, "HelioCloud-AuthStack",
                           description="HelioCloud end-user authorization capabilities. Required for other components.")
    auth_stack.add_dependency(base_stack)

    # Initialize requested optional stacks
    if dashboard:
        DashboardStack(app, "HelioCloud-Dashboard",
                       description="HelioCloud User Dashboard deployment").add_dependency(auth_stack)
    if binderhub:
        BinderhubStack(app, "HelioCloud-BinderHub",
                       description="HelioCloud Binderhub deployment").add_dependency(auth_stack)
    if daskhub:
        DaskhubStack(app, "HelioCloud-DaskHub",
                     description="HelioCloud Daskhub deployment").add_dependency(auth_stack)

app.synth()
