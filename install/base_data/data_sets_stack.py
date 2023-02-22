import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from constructs import Construct


class DataSetsStack(Stack):
    """
    Stack for instantiating the AWS S3 buckets that will contain the data sets registered in this HelioCloud
    instance.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        config = self.node.try_get_context("config")
        with open(config, 'r') as file:
            configuration = yaml.safe_load(file)

        # Provision the requested data buckets
        for data_bucket in configuration['public_data_buckets']['names']:
            print("Creating bucket: " + data_bucket)
            bucket = s3.Bucket(self, data_bucket,
                               bucket_name=data_bucket,
                               public_read_access=True,
                               removal_policy=cdk.RemovalPolicy.RETAIN,
                               object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
                               versioned=True)

            # TODO: Setup inventory service: https://pypi.org/project/aws-cdk.aws-s3/
            # TODO: Setup for requestor pays: https://github.com/aws-cloudformation/cloudformation-coverage-roadmap/issues/123
            # TODO: Consider transfer acceleration?? https://pypi.org/project/aws-cdk.aws-s3/