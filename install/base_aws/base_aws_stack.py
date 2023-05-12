from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct


class BaseAwsStack(Stack):
    """
    Stack for setting up a HelioCloud's base AWS requirements: IAM roles, process accounts, etc.
    """

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Local reference to configuration
        self.__config = config
        self.__build_vpc()

        # Single KMS key is generated for encryption needs by subsequent modules
        self.kms = kms.Key(self, "HelioCloudKMS")

        ###############################################
        # Create S3 Bucket for shared user storage #
        ###############################################
        # TODO potentially make this configurable along with component in s3 policy document
        # TODO figure out retention plan, persists after stack deleted
        destroy_on_removal = config.get("userSharedBucket").get("destroyOnRemoval")
        user_shared_bucket = s3.Bucket(self, "UserSharedBucket",
                                       removal_policy=RemovalPolicy.DESTROY if destroy_on_removal else RemovalPolicy.RETAIN)

        # TODO programmatically add additional policy statements
        # based on known HelioCloud public buckets (maybe use user script to pull names?)
        # Need to iteratively adjust though, maybe lambda
        registry = self.__config.get('registry')
        public_buckets = registry.get('bucketNames')
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

    def __build_vpc(self) -> None:
        """
        Build / Lookup the VPC that will be used for this HelioCloud installation
        """
        # TODO:
        # 1) Validate a pre-existing VPC as having at least 1 public and 1 private subnet.  Note that a private subnet
        # MUST have a NAT gateway associated to allow hosts in this subnet access to externally hosted resources
        # such as other libraries & images to aid in deployments (ex: Daskhub)
        # 2) If constructing a VPC from scratch, ensure it has at least 1 public and 1 private subnet (see #1)

        # Determine VPC configuration required
        vpc_config = self.__config.get("vpc")

        # Determine type and take action
        vpc_type = vpc_config.get("type")
        if vpc_type == "default":
            self.__heliocloud_vpc = ec2.Vpc.from_lookup(self, id="default", is_default=True)
            print(f"Using the default vpc: {self.__heliocloud_vpc.vpc_id}.")
        elif vpc_type == "existing":
            vpc_id = vpc_config.get("vpc_id")
            self.__heliocloud_vpc = ec2.Vpc.from_lookup(self, id="HelioCloud-VPC", vpc_id=vpc_id)
            print(f"Using existing vpc: {self.__heliocloud_vpc.vpc_id}.")
        elif vpc_type == "new":
            # Provision the minimal VPC configuration required
            self.__heliocloud_vpc = ec2.Vpc(self,
                                            id="HelioCloudVPC",
                                            max_azs=2,
                                            nat_gateways=1
                                            )
            print(f"Using newly created vpc: {self.__heliocloud_vpc.vpc_id}.")
        else:
            raise Exception(f"Unrecognized vpc type: {vpc_type}")

    @property
    def heliocloud_vpc(self) -> ec2.Vpc:
        return self.__heliocloud_vpc
