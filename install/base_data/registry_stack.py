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

        # Provision a staging S3 bucket for the data set registry process
        # Destroyed on removal, as this is a temporary bucket
        bucket = s3.Bucket(self,
                           "StagingBucket",
                           removal_policy=cdk.RemovalPolicy.DESTROY,
                           auto_delete_objects=True)


