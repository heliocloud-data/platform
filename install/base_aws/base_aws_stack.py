import aws_cdk.custom_resources
import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_iam as iam,
)
from constructs import Construct


class BaseAwsStack(Stack):
    """
    Stack for setting up a HelioCloud's base AWS requirements: IAM roles, process accounts, etc.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        config = self.node.try_get_context("config")
        with open(config, 'r') as file:
            configuration = yaml.safe_load(file)

        registry = configuration['registry']
        public_buckets = registry.get('bucketNames')

        # TODO:  What do we need to put in here?
        # Create own VPC for HelioCloud
        self.heliocloud_vpc = ec2.Vpc(self, "HelioCloudVPC")

        self.kms = kms.Key(self, "HelioCloudKMS")
        self.kms.add_alias('heliocloud')

        ###############################################
        # Create S3 Bucket for shared user storage #
        ###############################################
        # TODO potentially make this configurable along with component in s3 policy document
        # TODO figure out retention plan, persists after stack deleted
        user_shared_bucket = s3.Bucket(self, "UserSharedBucket")

        # TODO programmatically add additional policy statements
        # based on known HelioCloud public buckets (maybe use user script to pull names?)
        # Need to iteratively adjust though, maybe lambda
        other_known_public_buckets = ['helio-public',
                                      'gov-nasa-hdrl-data1']
        public_bucket_arns = []
        for public_bucket in public_buckets + other_known_public_buckets:
            public_bucket_arns += [f"arn:aws:s3:::{public_bucket}",
                                   f"arn:aws:s3:::{public_bucket}/*"]

        s3_custom_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["s3:PutObject",
                             "s3:GetObject",
                             "s3:ListBucketMultipartUploads",
                             "s3:AbortMultipartUpload",
                             "s3:ListBucketVersions",
                             "s3:CreateBucket",
                             "s3:ListBucket",
                             "s3:DeleteObject",
                             "s3:GetBucketLocation",
                             "s3:ListMultipartUploadParts"],
                    resources=[user_shared_bucket.bucket_arn,
                               f"{user_shared_bucket.bucket_arn}/*"]
                ),
                iam.PolicyStatement(
                    actions=["s3:ListAllMyBuckets"],
                    resources=["*"]
                ),
                iam.PolicyStatement(
                    actions=["s3:GetObject",
                             "s3:ListBucketVersions",
                             "s3:ListBucket",
                             "s3:GetBucketLocation"],
                    resources=public_bucket_arns
                )
            ]
        )

        # Create S3 IAM policy that will be used on multiple modules
        # within HelioCloud. Particularly useful is the public bucket
        # IAM policies that can be modified to give users access to other
        # HelioCloud instances without having to modify IAM roles
        # Currently slated to be used as the base user role for DaskHub
        # and attached to EC2 roles for the User Portal
        self.s3_managed_policy = iam.ManagedPolicy(self, "S3ManagedPolicy",
                                              document=s3_custom_policy_document)