import aws_cdk.custom_resources
import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    custom_resources as resources,
)
from constructs import Construct


class BaseAwsStack(Stack):
    """
    Stack for setting up a HelioCloud's base AWS requirements: IAM roles, process accounts, etc.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        config = self.node.try_get_context("config")
        with open(config, 'r') as file:
            configuration = yaml.safe_load(file)


        # TODO:  What do we need to put in here?