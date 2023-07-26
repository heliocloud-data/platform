import os.path

import aws_cdk as cdk
from aws_cdk import (
    aws_docdb as docdb,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_lambda as lambda_,
    custom_resources as resources,
    RemovalPolicy,
    Stack
)
from constructs import Construct

from base_aws.base_aws_stack import BaseAwsStack


class RegistryStack(Stack):
    """
    Instantiates a HelioCloud's Registry - a set of S3 buckets and related services for the storage, indexing,
    and sharing of data sets stored within this HelioCloud instance with:
    (a) the rest of the components of this instance (e.g. Daskhub)
    (b) other HelioCloud instances
    """

    # ARN for a Pandas Lambda Layer (used by multiple HelioCloud lambdas)
    # TODO:  This ARN is in us-east-1.  Need a better way to obtain this that is region neutral
    pandas_layer_arn = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:6"

    def __init__(self, scope: Construct, construct_id: str, config: dict, base_aws_stack: BaseAwsStack,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Registry config
        self.__registry_config = config['registry']
        self.__removal_policy = self.__registry_config['destroyOnRemoval']

        # Hold a reference to the base stack
        self.__base_aws_stack = base_aws_stack

        # Internal fields
        self.__buckets = list[s3.Bucket]()
        self.__ingest_bucket = None

        # Build the buckets
        self.__build_ingest_bucket()
        self.__build_registry_buckets()

        # Build the Catalog database
        self.__build_catalog_db()

        # Build lambdas
        self.__build_lambdas()

    def __build_ingest_bucket(self):
        """
        Build the AWS S3 bucket that will support the ingest process.
        Users of this HelioCloud instance can upload their datasets here.
        """
        bucket_name = self.__registry_config.get("ingestBucketName", None)
        removal_policy, auto_delete_objects = (RemovalPolicy.DESTROY, True) if self.__removal_policy else \
            (RemovalPolicy.RETAIN, False)

        if bucket_name is None:
            self.__ingest_bucket = s3.Bucket(self, id="Ingest-Bucket",
                                             removal_policy=removal_policy,
                                             auto_delete_objects=auto_delete_objects)
        else:
            self.__ingest_bucket = s3.Bucket(self, id="Ingest-Bucket",
                                             bucket_name=bucket_name,
                                             removal_policy=removal_policy,
                                             auto_delete_objects=auto_delete_objects)

    def __build_registry_buckets(self):
        """
        Build the s3 buckets that act as the storage for the Registry.
        """
        bucket_names = self.__registry_config.get('datasetBucketNames')
        requester_pays = self.__registry_config.get("requesterPays")

        # If buckets should be destroyed on removal, objects must be automatically deleted
        removal_policy, auto_delete_objects = (RemovalPolicy.DESTROY, True) if self.__removal_policy \
            else (RemovalPolicy.RETAIN, False)

        # Create the AWS S3 buckets for data set storage in the Registry, using provided names from the configuration
        # re: object_ownership - We are explicit here to ensure there is only a *single* owner of the content in each
        # bucket - the HelioCloud instance
        print(f"Deploying buckets: {bucket_names}")
        for bucket_name in bucket_names:
            bucket = s3.Bucket(self,
                               id=f"Registry Bucket: {bucket_name}",
                               bucket_name=bucket_name,
                               public_read_access=False,# TODO: Not honoring config here. True is causing a failure.
                               object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
                               removal_policy=removal_policy,
                               auto_delete_objects=auto_delete_objects)
            self.__buckets.append(bucket)

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

    def __build_catalog_db(self) -> None:
        """
        Builds a Document DB cluster to service as the database for cataloging datasets.
        The built cluster is kept very lean to minimize costs. It is hosted on a single EC2 instance
        in the T-series.
        """

        # Create the AWS Document DB resource to act as the catalog database
        master_user = self.__registry_config['catalogDb']['masterUser']
        removal_policy, delete_protection = (RemovalPolicy.DESTROY, False) \
            if self.__registry_config['destroyOnRemoval'] else (RemovalPolicy.RETAIN, True)

        self.__catalog_db = docdb.DatabaseCluster(
            self,
            id="CatalogDB",

            # Single instance deployment into a private subnet within the supplied VPC
            # Security group must
            instances=1,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
            vpc=self.__base_aws_stack.heliocloud_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),

            # TODO: Add individual user accounts for processes
            master_user=docdb.Login(username=master_user),

            # Setup logging to Cloudwatch
            parameter_group=docdb.ClusterParameterGroup(
                self,
                id="CatalogDB Parameters",
                family="docdb5.0",
                parameters={
                    "audit_logs": "all"
                },
                description="Parameters to enable audit log creation & storage in Cloudwatch."
            ),
            export_audit_logs_to_cloud_watch=True,

            # TODO: Retain?  Keeping it simple right now to facilitate development.
            deletion_protection=delete_protection,
            removal_policy=removal_policy
        )

    def __build_lambdas(self) -> None:
        """
        Builds the Ingester lambda, responsible for ingesting datasets placed in the ingest S3 bucket.
        """

        # Lambdas need to be able to import PyMongo and Pandas
        pymongo_layer = lambda_.LayerVersion(self,
                                             id="PyMongo",
                                             code=lambda_.Code.from_asset(os.path.dirname(__file__)
                                                                          + "/resources/pymongo_layer.zip"),
                                             description="Pymongo Layer")
        pandas_layer = lambda_.LayerVersion.from_layer_version_arn(self,
                                                                   id="Pandas Layer",
                                                                   layer_version_arn=RegistryStack.pandas_layer_arn)

        # Build the Ingester lambda
        ingester_lambda = lambda_.Function(self,
                                           id="Ingester",
                                           description="HelioCloud lambda for data set ingest",

                                           # Runtime environment with dependencies (pandas)
                                           runtime=lambda_.Runtime.PYTHON_3_9,
                                           handler="app.ingest_function.handler",
                                           code=lambda_.Code.from_asset("registry/lambdas"),
                                           layers=[pandas_layer, pymongo_layer],

                                           # Lambda must run in the VPC so it can reach the catalog db
                                           vpc=self.__base_aws_stack.heliocloud_vpc,
                                           vpc_subnets=ec2.SubnetSelection(
                                               subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                                           environment={
                                               "CATALOG_DB_SECRET": self.__catalog_db.secret.secret_name,
                                               "ingest_bucket": self.__ingest_bucket.bucket_name,
                                           },

                                           # Allow for max runtime with a decent amount of memory
                                           # so as to handle large ingest jobs
                                           memory_size=1024,
                                           timeout=cdk.Duration.minutes(15))

        # Build cataloger lambda
        cataloger_lambda = lambda_.Function(self,
                                            id="Cataloger",
                                            description="HelioCloud lambda for producing catalog files for datasets",

                                            # Runtime environment with dependencies (PyMongo)
                                            runtime=lambda_.Runtime.PYTHON_3_9,
                                            handler="app.catalog_function.handler",
                                            code=lambda_.Code.from_asset("registry/lambdas"),
                                            layers=[pymongo_layer, pandas_layer],

                                            # Must run in the VPC so the catalog database is accessible
                                            vpc=self.__base_aws_stack.heliocloud_vpc,
                                            vpc_subnets=ec2.SubnetSelection(
                                                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                                            environment={"CATALOG_DB_SECRET": self.__catalog_db.secret.secret_name},
                                            timeout=cdk.Duration.minutes(15))

        # Make sure the lambdas can reach the catalog db
        self.__catalog_db.connections.allow_default_port_from(ingester_lambda)
        self.__catalog_db.connections.allow_default_port_from(cataloger_lambda)
        self.__catalog_db.secret.grant_read(ingester_lambda)
        self.__catalog_db.secret.grant_read(cataloger_lambda)

        # Both lambdas need read/write to the registry buckets
        for bucket in self.__buckets:
            bucket.grant_read_write(ingester_lambda)
            bucket.grant_read_write(cataloger_lambda)

        # Ingester needs read/write on ingest bucket
        self.__ingest_bucket.grant_read_write(ingester_lambda)

    @property
    def buckets(self) -> list[s3.Bucket]:
        """
        S3 buckets created by this stack for storing data sets
        """
        return self.__buckets
