import os.path

from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_s3 as s3,
    aws_lambda as lambda_
)

from constructs import Construct

from .registry_stack import RegistryStack


class IngesterStack(Stack):
    """
    CDK stack for setting up the data set registry within a HelioCloud deployment.
    """

    def __init__(self, scope: Construct, construct_id: str, registry_stack: RegistryStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Provision a staging S3 bucket for the data set registry process
        # Destroyed on removal, as this is a temporary bucket
        bucket = s3.Bucket(self,
                           "StagingBucket",
                           removal_policy=RemovalPolicy.DESTROY,
                           auto_delete_objects=True)

        # TODO: Assemble the policy for this lambda that allows full read/write to each public S3 data set bucket
        # and the upload/staging bucket (and *only*) these buckets

        # TODO:  Create an IAM Role that this Lambda will use to access HelioCloud buckets (read/write)
        # Note that an IAM role will need a Trust Policy created to say which principals can use the role
        # (e.g. which principals does the IAM Role 'trust')

        # Install the Ingest Lambda, supported by a Layer containing the Pandas libs
        pandas_layer_arn = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:6"
        pandas_layer = lambda_.LayerVersion.from_layer_version_arn(self, id="Pandas Layer",
                                                                   layer_version_arn=pandas_layer_arn)

        ingester = lambda_.Function(self,
                                    id="Ingester",
                                    function_name="Ingester",
                                    description="HelioCloud lambda for data set ingest",
                                    runtime=lambda_.Runtime.PYTHON_3_9,
                                    handler="app.ingest_handler.handler",
                                    code=lambda_.Code.from_asset("base_data/lambdas"),
                                    layers=[pandas_layer],
                                    memory_size=1024)

        ingester.role.add_managed_policy(registry_stack.read_policy)
        ingester.role.add_managed_policy(registry_stack.write_policy)

        #
        # policy = iam.PolicyStatement(
        #    actions=["s3:GetObject", "s3:GetBucket"],
        #    resources=[ingester.function_arn]
        # )
        # ingester.add_to_role_policy(statement=policy)
