import aws_cdk.custom_resources
import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    custom_resources as resources,
    aws_iam as iam,
    aws_eks as eks,
    aws_ec2 as ec2,
)
from constructs import Construct


class DaskhubStack(Stack):
    """
    CDK stack for installing DaskHub for a HelioCloud instance
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        config = self.node.try_get_context("config")
        with open(config, "r") as file:
            configuration = yaml.safe_load(file)

        registry = configuration['registry']
        public_buckets = registry.get('bucketNames')

        #############################
        # Create EC2 Admin instance #
        #############################
        # EC2 admin instance can create AWS resources needed to control
        # EKS (Kubernetes) backing Daskhub, can access through SSM opposed to SSH
        # for tighter control

        # Create admin role for EC2 so we can create an EC2 instance to control
        # what is deployed on EKS
        ec2_admin_role = iam.Role(self, "EC2AdminRole",
                                  assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        ec2_admin_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(
            "AdministratorAccess"))
        ec2_admin_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(
            "CloudWatchAgentAdminPolicy"))
        ec2_admin_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(
            "CloudWatchAgentServerPolicy"))
        ec2_admin_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(
            "AmazonSSMManagedInstanceCore"))

        # What to install on instance on startup
        SSM_AGENT_RPM = 'https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm'
        ec2_user_data = ec2.UserData.for_linux()
        ec2_user_data.add_commands('sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm',
                                   'sudo yum -y install jq gettext bash-completion moreutils docker unzip nano git',
                                   f'sudo yum install -y {SSM_AGENT_RPM}',
                                   'restart amazon-ssm-agent')

        # Create own VPC for admin instance
        ec2_vpc = ec2.Vpc(self, "DaskHubEC2VPC")

        # TODO: add cloudwatch logs to SSM
        # Create admin instance and attach role
        instance = ec2.Instance(self, "DaskhubEC2AdminInstance",
                                vpc=ec2_vpc,
                                machine_image=ec2.AmazonLinuxImage(),
                                instance_type=ec2.InstanceType('t2.micro'),
                                user_data=ec2_user_data,
                                role=ec2_admin_role,
                                vpc_subnets=ec2.SubnetSelection(subnets=ec2_vpc.public_subnets))

        ###############################################
        # Create S3 Bucket for shared Daskhub storage #
        ###############################################
        # TODO potentially make this configurable along with component in s3 policy document
        daskhub_bucket = s3.Bucket(self, "DaskhubBucket")

        ####################################################
        # Managed Policies (S3 access and K8s autoscaling) #
        ####################################################

        # TODO programmatically add additional policy statements
        # based on known HelioCloud public buckets (maybe use user script to pull names?)
        # Need to iteratively adjust though, maybe lambda
        other_known_public_buckets = ['heliopublic']
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
                    resources=[daskhub_bucket.bucket_arn,
                               f"{daskhub_bucket.bucket_arn}/*"]
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

        helio_managed_policy = iam.ManagedPolicy(self, "S3ManagedPolicy",
                                                 document=s3_custom_policy_document)

        autoscaling_custom_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["autoscaling:DescribeAutoScalingGroups",
                             "autoscaling:DescribeAutoScalingInstances",
                             "autoscaling:DescribeLaunchConfigurations",
                             "autoscaling:DescribeTags",
                             "autoscaling:SetDesiredCapacity",
                             "autoscaling:TerminateInstanceInAutoScalingGroup",
                             "ec2:DescribeLaunchTemplateVersions"
                             ],
                    resources=["*"]
                )
            ]
        )

        autoscaling_managed_policy = iam.ManagedPolicy(self, "K8AutoScalingManagedPolicy",
                                                       document=autoscaling_custom_policy_document)

        ##########################
        # CloudFormation Outputs #
        ##########################

        # Return instance ID to make logging into admin instance easier
        cdk.CfnOutput(self, 'Instance ID',
                      value=instance.instance_id)
