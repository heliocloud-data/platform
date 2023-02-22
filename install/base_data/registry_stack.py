import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from constructs import Construct


class RegistryStack(Stack):
    """
    CDK stack for setting up the data set registry within a HelioCloud deployment.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        config = self.node.try_get_context("config")
        with open(config, 'r') as file:
            configuration = yaml.safe_load(file)

        # Provision a staging bucket for use with the registry service
        bucket = s3.Bucket(self,
                           "StagingBucket",
                           removal_policy=cdk.RemovalPolicy.DESTROY,
                           auto_delete_objects=True)
        print("Created bucket " + bucket.bucket_name + " as a staging bucket.")


