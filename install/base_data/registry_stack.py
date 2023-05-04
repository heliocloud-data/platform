import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    custom_resources as resources,
)
from constructs import Construct


class RegistryStack(Stack):
    """
    Instantiates a HelioCloud's Registry - a set of S3 buckets and related services for the storage, indexing,
    and sharing of data sets stored within this HelioCloud instance with:
    (a) the rest of the components of this instance (e.g. Daskhub)
    (b) other HelioCloud instances
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        config_file = self.node.try_get_context("config")
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        registry_config = config['registry']
        bucket_names = registry_config.get('bucketNames')
        destroy_on_removal = registry_config.get('destroyOnRemoval', False)
        requester_pays = registry_config.get('requesterPays', True)

        # Option to destroy public s3 buckets on removal - helps with development (re)deployments of this stack
        if destroy_on_removal:
            removal_policy = cdk.RemovalPolicy.DESTROY
            auto_delete_objects = True
        else:
            removal_policy = cdk.RemovalPolicy.RETAIN
            auto_delete_objects = False

        # Create the AWS S3 buckets for data set storage in the Registry, using provided names from the configuration
        # re: object_ownership - We are explicit here to ensure there is only a *single* owner of the content in each
        # bucket - the HelioCloud instance
        self.buckets = list[s3.Bucket]()
        # TODO:  Troubleshoot setting up public read access again. A recent change results in
        # public_read_access=True prevening the bucket from being created
        for bucket_name in bucket_names:
            bucket = s3.Bucket(self,
                               id=bucket_name,
                               bucket_name=bucket_name,
                               public_read_access=False,
                               object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
                               removal_policy=removal_policy,
                               auto_delete_objects=auto_delete_objects)
            self.buckets.append(bucket)

            # AWS CDK doesn't allow directly setting Payer=Requester on an S3 bucket.  You have to leverage an
            # AWSCustomResource instance to invoke an AWS Lambda to execute an AWS API call against the bucket itself,
            # setting the property
            if requester_pays:
                custom = resources.AwsCustomResource(self,
                                                     id=bucket_name + "-add-request-payer",
                                                     on_create=resources.AwsSdkCall(
                                                         service='S3',
                                                         action='putBucketRequestPayment',
                                                         parameters={
                                                             "Bucket": bucket.bucket_name,
                                                             "RequestPaymentConfiguration": {
                                                                 "Payer": "Requester"
                                                             }
                                                         },
                                                         physical_resource_id=resources.PhysicalResourceId.of("id")
                                                     ),
                                                     install_latest_aws_sdk=True,
                                                     policy=resources.AwsCustomResourcePolicy.from_sdk_calls(
                                                         resources=resources.AwsCustomResourcePolicy.ANY_RESOURCE
                                                     ))
                custom.node.add_dependency(bucket)

        # Install the Catalog Generator lambda
        self.cataloger = lambda_.Function(self,
                                          id="Cataloger",
                                          function_name="Cataloger",
                                          description="Helio Cloud lambda for cataloging data in public s3 data set "
                                                      "buckets.",
                                          runtime=lambda_.Runtime.PYTHON_3_9,
                                          handler="app.catalog_handler.handler",
                                          code=lambda_.Code.from_asset("base_data/lambdas"))
        # Cataloger needs read/write on registry buckets
        for bucket in self.buckets:
            bucket.grant_read_write(self.cataloger.role)

    @property
    def buckets(self) -> list[s3.Bucket]:
        """
        S3 buckets created by this stack for storing data sets
        """
        return self._buckets

    @buckets.setter
    def buckets(self, value):
        self._buckets = value

    @property
    def cataloger(self) -> lambda_.Function:
        """
        AWS Lambda created for producing the Catalog.json in the S3 buckets comprising the registry
        """
        return self._cataloger

    @cataloger.setter
    def cataloger(self, value):
        self._cataloger = value
