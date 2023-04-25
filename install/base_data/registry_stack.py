import os.path

import yaml
from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_s3 as s3,
    aws_lambda as lambda_
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
                           removal_policy=RemovalPolicy.DESTROY,
                           auto_delete_objects=True)

        # Install the Ingest Lambda, supported by a Layer containins the Pandas libs
        pandas_layer_arn = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:6"
        pandas_layer = lambda_.LayerVersion.from_layer_version_arn(self, id="Pandas Layer",
                                                                   layer_version_arn=pandas_layer_arn)
        lambda_.Function(self,
                         id="Ingester",
                         function_name="Ingester",
                         description="HelioCloud lambda for data set ingest",
                         runtime=lambda_.Runtime.PYTHON_3_9,
                         handler="ingest_handler.handler",
                         code=lambda_.Code.from_asset("base_data/lambda/"),
                         layers=[pandas_layer],
                         memory_size=1024)

        # Install the Catalog Generator lambda
        lambda_.Function(self,
                         id="Cataloger",
                         function_name="Cataloger",
                         description="Helio Cloud lambda for cataloging data in public s3 data set buckets.",
                         runtime=lambda_.Runtime.PYTHON_3_9,
                         handler="catalog_handler.handler",
                         code=lambda_.Code.from_asset("base_data/lambda"))
