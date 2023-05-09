import aws_cdk.aws_docdb
import yaml
import aws_cdk as cdk
from aws_cdk import (
    aws_docdb as docdb,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_lambda as lambda_,
    custom_resources as resources,
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

    def __init__(self, scope: Construct, construct_id: str, config: dict, base_aws_stack: BaseAwsStack,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Hold a reference to the base stack
        self.__base_aws_stack = base_aws_stack
        self.__buckets = None
        self.__catalog_db = None
        self.__cataloger = None

        self.__registry_config = config['registry']

        # Build the buckets
        self.__build_registry_buckets()

        # Build catalog database
        self.__build_catalog_db()

        # Build the Cataloger lambda
        self.__build_cataloger()

    def __build_registry_buckets(self):
        """
        Build the s3 buckets that act as the storage for the Registry.
        """

        bucket_names = self.__registry_config.get('bucketNames')
        destroy_on_removal = self.__registry_config.get('destroyOnRemoval', False)
        requester_pays = self.__registry_config.get('requesterPays', True)

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
        self.__buckets = list[s3.Bucket]()
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

    def __build_catalog_db(self):
        """
        Builds and installs an instance of AWS Document DB to function as the backing store for the
        Catalog.
        """
        # Document DB supports a subset of instance classes
        # As of this development, the T4G is the Latest Generation of Burstable Performance Instance Class
        # and has the cheapest ($$) cost profile. It is supported in Medium size.

        self.__catalog_db = docdb.DatabaseCluster(
            self,
            id="CatalogDB",
            db_cluster_name="CatalogDB",
            instances=1,
            master_user=docdb.Login(
                username="catalog_master"
            ),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MEDIUM),
            vpc=self.__base_aws_stack.heliocloud_vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            parameter_group=docdb.ClusterParameterGroup(self, "CatalogDBClusterParameters",
                                                        family="docdb4.0",
                                                        parameters={
                                                            "audit_logs": "all"
                                                        }
                                                        ),
            export_audit_logs_to_cloud_watch=True,
            removal_policy=cdk.RemovalPolicy.DESTROY  # destroy for now..
        )
        print(f"Building the catalog db {self.__catalog_db}")

    def __build_cataloger(self):
        """
        Builds and installs the Cataloger lambda, responsible for generating the Catalog files
        at the root of each registry bucket.
        """
        cataloger = lambda_.Function(self,
                                     id="Cataloger",
                                     function_name="Cataloger",
                                     description="Helio Cloud lambda for cataloging data in public s3 data set "
                                                 "buckets.",
                                     runtime=lambda_.Runtime.PYTHON_3_9,
                                     handler="app.catalog_handler.handler",
                                     code=lambda_.Code.from_asset("base_data/lambdas"))

        # Cataloger needs read/write on registry buckets
        for bucket in self.buckets:
            bucket.grant_read_write(cataloger)

    @property
    def buckets(self) -> list[s3.Bucket]:
        """
        S3 buckets created by this stack for storing data sets
        """
        return self.__buckets

    @property
    def catalog_db(self) -> docdb.DatabaseCluster:
        """
        Catalog database (an AWS Document DB instance)
        """
        return self.__catalog_db

    @property
    def cataloger(self) -> lambda_.Function:
        """
        AWS Lambda created for producing the Catalog.json in the S3 buckets comprising the registry
        """
        return self.__cataloger
