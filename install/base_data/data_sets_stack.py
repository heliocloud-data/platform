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

        # get the configuration file from the context
        config_file = self.node.try_get_context("config")
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        buckets = config['registry']['bucketNames']

        # Create s3 buckets for data storage in this HelioCloud, using the names from the configuration and
        # setting the bucket open for public reading.
        # re: object_ownership - default is that the uploading account owns the object. We are being explicit here
        # to ensure there is only a *single* owner of the content in the bucket:  this heliocloud instance
        for data_bucket in buckets:
            bucket = s3.Bucket(self, data_bucket,
                               bucket_name=data_bucket,
                               public_read_access=True,
                               removal_policy=cdk.RemovalPolicy.DESTROY,
                               auto_delete_objects=True,
                               object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED)
            # Note: destroy on removal temporarily added for testing purposes

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
            print("Adding requester pays")

        # no cloud formation resources exist to configure requestor pays, so you have to make an API call
        # PUT ?requestPayment
        # HTTP / 1.1
        # Host: [BucketName].s3.amazonaws.com
        # Content - Length: 173
        # Date: Wed, 01 Mar 2009 12:00:00 GMT
        # Authorization: AWS[Signature]
        # <RequestPaymentConfiguration xmlns = "http://s3.amazonaws.com/doc/2006-03-01/>
        # <Payer>Requester</Payer>
        # </RequestPaymentConfiguration>

        # TODO: Setup inventory service: https://pypi.org/project/aws-cdk.aws-s3/
        # TODO: Setup for requestor pays: https://github.com/aws-cloudformation/cloudformation-coverage-roadmap/issues/123
        # TODO: Consider transfer acceleration?? https://pypi.org/project/aws-cdk.aws-s3/
