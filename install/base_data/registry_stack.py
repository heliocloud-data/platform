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
        registry = config['registry']
        bucket_names = registry.get('bucketNames')
        destroy_on_removal = registry.get('destroyOnRemoval', False)
        requester_pays = registry.get('requesterPays', True)

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
        # TODO:  Troubleshoot setting up public read access.  AWS not permitting it?
        for bucket in bucket_names:
            new_bucket = s3.Bucket(self, bucket,
                                   bucket_name=bucket,
                                   public_read_access=True,
                                   object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
                                   removal_policy=removal_policy,
                                   auto_delete_objects=auto_delete_objects)
            self.buckets.append(new_bucket)

            # AWS CDK doesn't allow directly setting Payer=Requester on an S3 bucket.  You have to leverage an
            # AWSCustomResource instance to invoke an AWS Lambda to execute an AWS API call against the bucket itself,
            # setting the property
            if requester_pays:
                custom = resources.AwsCustomResource(self,
                                                     bucket.bucket_name + "-add-request-payer",
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

        # Create a read policy for the buckets, for use by other HelioCloud components
        self.read_policy = iam.ManagedPolicy(
            self,
            id="HelioCloud-Registry-DataSetBuckets-Read",
            managed_policy_name="HelioCloud-Registry-DataSetBuckets-Read",
            statements=[
                iam.PolicyStatement(
                    actions=["s3:ListBucket"],
                    resources=[bucket.bucket_arn for bucket in self.buckets]
                ),
                iam.PolicyStatement(
                    actions=['s3:GetObject'],
                    resources=[bucket.bucket_arn + "/*" for bucket in self.buckets]
                )
            ]
        )

        # Create a write policy for the buckets, for use by other HelioCloud components
        self.write_policy = iam.ManagedPolicy(
            self,
            id="HelioCloud-Registry-DataSetBuckets-Write",
            managed_policy_name="HelioCloud-Registry-DataSetBuckets-Write",
            statements=[
                iam.PolicyStatement(
                    actions=["s3:PutObject", "s3:DeleteObject"],
                    resources=[bucket.bucket_arn + "/*" for bucket in self.buckets]
                )
            ]
        )

        # Install the Catalog Generator lambda
        self.cataloger = lambda_.Function(self,
                                          id="Cataloger",
                                          function_name="Cataloger",
                                          description="Helio Cloud lambda for cataloging data in public s3 data set "
                                                      "buckets.",
                                          runtime=lambda_.Runtime.PYTHON_3_9,
                                          handler="app.catalog_handler.handler",
                                          code=lambda_.Code.from_asset("base_data/lambdas"))
        self.cataloger.role.add_managed_policy(self.read_policy)
        self.cataloger.role.add_managed_policy(self.write_policy)

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
    def read_policy(self) -> iam.ManagedPolicy:
        """
        IAM Policy created for reading from the S3 buckets comprising the registry
        """
        return self._read_policy

    @read_policy.setter
    def read_policy(self, value):
        self._read_policy = value

    @property
    def write_policy(self) -> iam.ManagedPolicy:
        """
        IAM Policy created for writing to the S3 buckets comprising the registry
        """
        return self._write_policy

    @write_policy.setter
    def write_policy(self, value):
        self._write_policy = value

    @property
    def cataloger(self) -> lambda_.Function:
        """
        AWS Lambda created for producing the Catalog.json in the S3 buckets comprising the registry
        """
        return self._cataloger

    @cataloger.setter
    def cataloger(self, value):
        self._cataloger = value
