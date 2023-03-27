import yaml
import os
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_s3_assets as s3_assets,
)
from constructs import Construct


class DaskhubStack(Stack):
    """
    CDK stack for installing DaskHub for a HelioCloud instance
    """

    def __init__(self, scope: Construct, construct_id: str, base_stack, **kwargs) -> None:
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
                                  assumed_by=iam.CompositePrincipal(
                                      iam.ServicePrincipal(
                                          "ec2.amazonaws.com"),
                                      iam.AccountRootPrincipal()))
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

        
        with open('daskhub/deploy/01-tools.sh', encoding='UTF-8') as file:
            bash_lines = file.read()

        # TODO remove all of these when scripts are available on open git repo
        # that requires no auth, instead add git commands to 01-tools.sh
        deploy_dir = 'daskhub/deploy'
        config_deploy_file_list = [f for f in os.listdir(deploy_dir) if os.path.isfile(os.path.join(deploy_dir, f)) and f.split(".")[-1] != 'sh']
        assets_tuple_list = [(f, s3_assets.Asset(self, f'K8sAssets{i}', path=os.path.join(os.getcwd(), f'daskhub/deploy/{f}'))) for i, f in enumerate(config_deploy_file_list)]

        shell_script_deploy_file_list = [f for f in os.listdir(deploy_dir) if os.path.isfile(os.path.join(deploy_dir, f)) and f.split(".")[-1] == 'sh']
        assets_sh_tuple_list = [(f, s3_assets.Asset(self, f'K8sAssetsSh{i}', path=os.path.join(os.getcwd(), f'daskhub/deploy/{f}'))) for i, f in enumerate(shell_script_deploy_file_list)]

        # TODO find a way to bundle and unbundle these files with correct permissions to avoid
        # having to move them like this
        init_data = ec2.CloudFormationInit.from_elements(
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_tuple_list[0][0]}", assets_tuple_list[0][1], mode='000666'),
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_tuple_list[1][0]}", assets_tuple_list[1][1], mode='000666'),
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_tuple_list[2][0]}", assets_tuple_list[2][1], mode='000666'),
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_tuple_list[3][0]}", assets_tuple_list[3][1], mode='000666'),
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_tuple_list[4][0]}", assets_tuple_list[4][1], mode='000666'),
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_tuple_list[5][0]}", assets_tuple_list[5][1], mode='000666'),
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_tuple_list[6][0]}", assets_tuple_list[6][1], mode='000666'),
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_sh_tuple_list[0][0]}", assets_sh_tuple_list[0][1], mode='000777'),
                                                         ec2.InitFile.from_existing_asset(f"/home/ssm-user/{assets_sh_tuple_list[1][0]}", assets_sh_tuple_list[1][1], mode='000777')
                                                         )

        # TODO figure out why chown statement won't work in either the cloudformationinit or user data
        ec2_user_data.add_commands('sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm',
                                   'sudo yum -y install jq gettext bash-completion moreutils docker unzip nano git',
                                   f'sudo yum install -y {SSM_AGENT_RPM}',
                                   'restart amazon-ssm-agent',
                                    bash_lines,
                                    'sudo chown -R ssm-user:ssm-user /home/ssm-user'  #TODO figure out why this doesn't work
                                    )

        # TODO: add cloudwatch logs to SSM
        # Create admin instance and attach role
        instance = ec2.Instance(self, "DaskhubInstance",
                                vpc=base_stack.heliocloud_vpc,
                                machine_image=ec2.AmazonLinuxImage(),
                                instance_type=ec2.InstanceType('t2.micro'),
                                role=ec2_admin_role,
                                user_data=ec2_user_data,
                                vpc_subnets=ec2.SubnetSelection(
                                    subnets=base_stack.heliocloud_vpc.private_subnets),
                                init=init_data)

        ###############################################
        # Create S3 Bucket for shared Daskhub storage #
        ###############################################
        # TODO potentially make this configurable along with component in s3 policy document
        # TODO figure out retention plan, persists after stack deleted
        # TODO make this an option (ALSO MUST MAKE OPTIONAL IN K8s SCRIPTS)
        daskhub_bucket = s3.Bucket(self, "DaskhubBucket")

        ####################################################
        # Managed Policies (S3 access and K8s autoscaling) #
        ####################################################

        # TODO programmatically add additional policy statements
        # based on known HelioCloud public buckets (maybe use user script to pull names?)
        # Need to iteratively adjust though, maybe lambda
        other_known_public_buckets = ['helio-public']
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

        s3_managed_policy = iam.ManagedPolicy(self, "S3ManagedPolicy",
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

        # TODO figure out retention plan, persists after stack deleted
        # TODO make this an option (ALSO MUST MAKE OPTIONAL IN K8s SCRIPTS)
        file_system = efs.FileSystem(self, "DaskhubEFS",
                                     vpc=base_stack.heliocloud_vpc,
                                     encrypted=True,
                                     enable_automatic_backups=True
                                     )

        ##########################
        # CloudFormation Outputs #
        ##########################

        # Return instance ID to make logging into admin instance easier
        cdk.CfnOutput(self, 'Instance ID',
                      value=instance.instance_id)
        cdk.CfnOutput(self, 'ASGArn',
                      value=autoscaling_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, 'KMSArn',
                      value=base_stack.kms.key_arn)
        cdk.CfnOutput(self, 'CustomS3Arn',
                      value=s3_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, 'AdminRoleArn',
                      value=ec2_admin_role.role_arn)  
        cdk.CfnOutput(self, 'EFSId',
                      value=file_system.file_system_id)
        cdk.CfnOutput(self, 'AssetBucket',
                      value=assets_tuple_list[0][1].s3_bucket_name)
        