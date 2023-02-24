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
RegistryStack(app, "RegistryStack")

app.synth()

