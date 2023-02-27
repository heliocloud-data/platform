import aws_cdk.custom_resources
import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    custom_resources as resources,
)
from constructs import Construct


class AuthStack(Stack):
    """
    Stack for instantiating Authorization and Authentication services in AWS
    that are required by other HelioCloud components:  User dashboard, Daskhub, File Registration, etc"
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        config = self.node.try_get_context("config")
        with open(config, 'r') as file:
            configuration = yaml.safe_load(file)

        # TODO: What has to be setup here?