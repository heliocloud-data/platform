#!/usr/bin/env python3
import os

import aws_cdk as cdk

from base_data.registry_stack import RegistryStack
from base_data.data_sets_stack import DataSetsStack


# Initialize the CDK app
app = cdk.App()

# Get the configuration file to use for determining bucket count & names
config = app.node.try_get_context("config")
if config is None:
    raise Exception("No configuration file was specified. Re-run using flag '-c config=<name of config file>")
else:
    print("Using configuration file " + config)


# Create the data buckets in S3
DataSetsStack(app, "DataSetsStack")

# Instantiate the registry
RegistryStack(app, "RegistryStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()

