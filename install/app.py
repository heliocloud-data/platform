#!/usr/bin/env python3
import os

import aws_cdk as cdk
import yaml

from base_auth.authorization_stack import AuthStack
from base_aws.base_aws_stack import BaseAwsStack
from base_data.ingester_stack import IngesterStack
from base_data.registry_stack import RegistryStack
from dashboard.dashboard_stack import DashboardStack
from daskhub.daskhub_stack import DaskhubStack


def get_aws_env() -> cdk.Environment:
    """
    Get the AWS Account & Region to deploy into
    """
    # Use what we inherit from the environment
    account = os.environ["CDK_DEFAULT_ACCOUNT"]
    region = os.environ["CDK_DEFAULT_REGION"]
    print(f"Provisioning into account: {account}, region: {region}.")
    return cdk.Environment(account=account, region=region)


def load_config(app: cdk.App) -> dict:
    """
    Loads configuration files
    """
    # First load the default config
    with open("config/default.yaml", "r") as default_file:
        configuration = yaml.safe_load(default_file)

    overide_file = app.node.try_get_context("config")
    if overide_file is None:
        raise Exception("No configuration file was specified.  Re-run using flag '-c config=<name of config file>")

    # Load & overlay any user provided config
    print(f"Applying configuration from file {overide_file}.")
    with open(overide_file, 'r') as overrides:
        configuration.update(yaml.safe_load(overrides))

    return configuration


# Initialize the CDK app
env = get_aws_env()
app = cdk.App()

# Load the config
config = load_config(app)

# Required:  Deploy the Base AWS Stack to make sure the AWS account environment is properly configured
base_aws_stack = BaseAwsStack(app, "HelioCloud-BaseAwsStack",
                              description="AWS resources necessary to deploy any HelioCloud instance",
                              config=config,
                              env=env)

# Determine optional components to deploy
components = config['components']

# Install the Registry if enabled
if components.get('enableRegistry', False):
    registry_stack = RegistryStack(app, "HelioCloud-RegistryStack",
                                   description="HelioCloud data set management.",
                                   config=config,
                                   base_aws_stack=base_aws_stack)
    registry_stack.add_dependency(base_aws_stack)

    ingester_stack = IngesterStack(app, "HelioCloud-IngesterStack",
                                   description="HelioCloud data loading and registration.",
                                   config=config,
                                   registry_stack=registry_stack)
    ingester_stack.add_dependency(base_aws_stack)
    ingester_stack.add_dependency(registry_stack)

# Check for the other stacks to deploy
daskhub = components.get('enableDaskHub', False)
dashboard = components.get('enableUserDashboard', False)
if daskhub or dashboard:

    # Each of these stacks require the Auth stack be deployed first
    auth_stack = AuthStack(app, "HelioCloud-AuthStack",
                           config=config,
                           description="HelioCloud end-user authorization capabilities. Required for other components.")
    auth_stack.add_dependency(base_aws_stack)

    # Initialize requested optional stacks
    if dashboard:
        DashboardStack(app, "HelioCloud-Dashboard",
                       description="HelioCloud User Dashboard deployment",
                       config=config,
                       base_auth=auth_stack).add_dependency(auth_stack)

    if daskhub:
        DaskhubStack(app, "HelioCloud-DaskHub",
                     description="HelioCloud Daskhub deployment",
                     config=config,
                     base_aws=base_aws_stack,
                     base_auth=auth_stack).add_dependency(auth_stack)
        # cdk.Tags.of(daskhub_stack).add("StackType", "daskhub")

# cdk.Tags.of(app).add("app", "heliocloud")

app.synth()
