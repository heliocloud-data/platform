import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as lambda_,
    aws_s3 as s3,
    RemovalPolicy,
    Stack
)
from constructs import Construct

from .registry_stack import RegistryStack


class IngesterStack(Stack):
    """
    CDK stack for setting up the data set registry within a HelioCloud deployment.
    """

    def __init__(self, scope: Construct, construct_id: str, config: dict, registry_stack: RegistryStack,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        registry_config = config['registry']
        upload_bucket_name = registry_config.get('uploadBucketName', None)

        # Provision an upload bucket for the ingest capability
        upload_bucket = s3.Bucket(self,
                                  id="Ingester-Upload",
                                  bucket_name=upload_bucket_name,
                                  removal_policy=RemovalPolicy.DESTROY,
                                  auto_delete_objects=True)

        # Create the Ingester lambda, noting that:
        # (1) It must be supported by an AWS Layer containing the Pandas libraries
        # (2) It needs read/write access to the objects in the upload bucket
        ingester = lambda_.Function(self,
                                    id="Ingester",
                                    description="HelioCloud lambda for data set ingest",
                                    runtime=lambda_.Runtime.PYTHON_3_9,
                                    handler="app.ingest_handler.handler",
                                    code=lambda_.Code.from_asset("registry/lambdas"),
                                    layers=[
                                        lambda_.LayerVersion.from_layer_version_arn(
                                            self,
                                            id="Pandas Layer",
                                            layer_version_arn="arn:aws:lambda:us-east-1:336392948345:layer"
                                                              ":AWSSDKPandas-Python39:6"
                                        )
                                    ],
                                    memory_size=1024,
                                    timeout=cdk.Duration.minutes(15))

        # Ingester needs read/write on the upload bucket
        upload_bucket.grant_read_write(ingester)

        # Ingester needs read/write on registry buckets
        for registry_bucket in registry_stack.buckets:
            registry_bucket.grant_read_write(ingester)
