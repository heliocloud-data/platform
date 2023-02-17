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

        # Provision the requested data buckets
        for data_bucket in configuration['public_data_buckets']:
            print("Creating bucket: " + data_bucket)
            bucket = s3.Bucket(self, data_bucket,
                               bucket_name=data_bucket,
                               versioned=True,
                               removal_policy=cdk.RemovalPolicy.DESTROY,
                               auto_delete_objects=True)

        # Provision the requested upload bucket
        upload_bucket = configuration['registration_upload_bucket']
        bucket = s3.Bucket(self, upload_bucket,
                           bucket_name=upload_bucket,
                           versioned=True,
                           removal_policy=cdk.RemovalPolicy.DESTROY,
                           auto_delete_objects=True)

