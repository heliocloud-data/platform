#!/usr/bin/env python3
import os

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
config = app.node.try_get_context("config")
if config is None:
    raise Exception("No configuration file was specified. Re-run using flag '-c config=<name of config file>")
else:
    print("Using configuration file " + config)

# First, setup base AWS environment
BaseAwsStack(app, "BaseAwsStack")

# Next comes auth & data
AuthStack(app, "AuthStack")
DataSetsStack(app, "DataSetsStack")
RegistryStack(app, "RegistryStack")

# Then,  all the "hubs"?  Dashboard?
DaskhubStack(app, "DaskhubStack")
DashboardStack(app, "DashboardStack")
BinderhubStack(app, "BinderhubStack")

app.synth()

