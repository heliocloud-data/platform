import aws_cdk.custom_resources
import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    custom_resources as cr,
)
from constructs import Construct


class DataSetsStack(Stack):
    """
    Stack for instantiating the AWS S3 buckets that will contain the data sets registered in this HelioCloud
    instance.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get configuration settings with rational defaults
        config_file = self.node.try_get_context("config")
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        registry = config['registry']
        buckets = registry.get('bucketNames')
        destroy_on_removal = registry.get('destroyOnRemoval', False)
        requester_pays = registry.get('requesterPays', True)

        # Option to destroy public s3 buckets on removal - helps with development (re)deployments of this stack
        if destroy_on_removal:
            rp = cdk.RemovalPolicy.DESTROY
            ado = True
        else:
            rp = cdk.RemovalPolicy.RETAIN
            ado = False

        # Create public S3 buckets for data storage in this HelioCloud, using the names from the configuration
        # re: object_ownership - default is that the uploading account owns the object, so we are being explicit
        # here to ensure this HelioCloud instance owns all its bucket contents - no matter the upload actor/mechanism
        for data_bucket in buckets:
            bucket = s3.Bucket(self, data_bucket,
                               bucket_name=data_bucket,
                               public_read_access=True,
                               removal_policy=rp,
                               auto_delete_objects=ado,
                               object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED)

            # AWS CDK doesn't allow directly setting Payer=Requester on an S3 bucket.  You have to leverage an
            # AWSCustomResource instance to invoke an AWS Lambda to execute an AWS API call against the bucket itself,
            # setting the property
            if requester_pays:
                custom = cr.AwsCustomResource(self,
                                              data_bucket + "-add-request-payer",
                                              on_create=cr.AwsSdkCall(
                                                  service='S3',
                                                  action='putBucketRequestPayment',
                                                  parameters={
                                                      "Bucket": bucket.bucket_name,
                                                      "RequestPaymentConfiguration": {
                                                          "Payer": "Requester"
                                                      }
                                                  },
                                                  physical_resource_id=cr.PhysicalResourceId.of("id")
                                              ),
                                              install_latest_aws_sdk=True,
                                              policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                                                  resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
                                              ))
                custom.node.add_dependency(bucket)

        # TODO: Setup inventory service: https://pypi.org/project/aws-cdk.aws-s3/
        # TODO: Consider transfer acceleration?? https://pypi.org/project/aws-cdk.aws-s3/
