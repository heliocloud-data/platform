"""
This file contains the CDK stack for deploying Daskhub.
"""

import glob
import os
import secrets
import shutil
import yaml

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_kms as kms,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_s3_assets as s3_assets,
    aws_cognito as cognito,
    aws_route53 as route53,
    Duration,
    RemovalPolicy,
)
from constructs import Construct
from base_aws.base_aws_stack import BaseAwsStack

from daskhub.aws_utils import get_instance_types_by_region, find_route53_record_by_type_and_name
from daskhub.jinja_utils import apply_jinja_templates_by_dir

SECRET_HEX_IN_BYTES = 32
WARN_ON_UNSUPPORTED_INSTANCE_TYPE = True
WARN_ON_DUPLICATE_FILES = True


class DaskhubStack(Stack):
    """
    CDK stack for installing DaskHub for a HelioCloud instance
    """

    FILES_TO_OMIT = {}

    # URL to download the SSM_AGENT
    SSM_AGENT_RPM = "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm"  # pylint: disable=line-too-long

    # fmt: off
    def __init__(  # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
            self,
            scope: Construct,
            construct_id: str,
            config: dict,
            base_aws: BaseAwsStack,
            base_auth: Stack,
            **kwargs,
    ) -> None:
        # fmt: on
        super().__init__(scope, construct_id, **kwargs)

        self.__daskhub_config = DaskhubStack.load_configurations(config)
        self.build_hosted_zone()

        if self.__daskhub_config['daskhub']['api_key1'] == 'auto':
            self.__daskhub_config['daskhub']['api_key1'] = secrets.token_hex(SECRET_HEX_IN_BYTES)
        if self.__daskhub_config['daskhub']['api_key2'] == 'auto':
            self.__daskhub_config['daskhub']['api_key2'] = secrets.token_hex(SECRET_HEX_IN_BYTES)

        # Scan the instance types and down-select
        region = None
        account = None
        if 'env' in config:
            if 'region' in config['env']:
                region = config['env']['region']
            if 'account' in config['env']:
                account = config['env']['account']
        if region is None:
            region = 'us-east-1'
            print("WARN: Unable to detect AWS region for HelioCloud instance, "
                  + f"defaulting to {region}")
        if account is None:
            account = '0123456789'
            print("WARN: Unable to detect AWS account for HelioCloud instance, "
                  + f"defaulting to {account}")

        instance_types = get_instance_types_by_region(region)

        # Scan the instance types and remove any instance type not supported by
        # the region.
        if 'nodeGroups' in self.__daskhub_config['eksctl']:
            for nodeGroup in self.__daskhub_config['eksctl']['nodeGroups']: # pylint: disable=invalid-name
                if ('instancesDistribution' in nodeGroup and
                    'instanceTypes' in nodeGroup['instancesDistribution']):
                    to_remove = []
                    for instanceType in nodeGroup['instancesDistribution']['instanceTypes']: # pylint: disable=invalid-name
                        if instanceType not in instance_types:
                            if WARN_ON_UNSUPPORTED_INSTANCE_TYPE:
                                print(f"WARN: Unsupported instance type {instanceType},"
                                    + "removing from node group")
                            to_remove.append(instanceType)
                    for rem in to_remove:
                        nodeGroup['instancesDistribution']['instanceTypes'].remove(rem)
                    # TODO: If list is empty at this point... Fail.

        # EC2 admin instance can create AWS resources needed to control
        # EKS (Kubernetes) backing Daskhub, can access through SSM opposed to SSH
        # for tighter control

        # Create admin role for EC2 so we can create an EC2 instance to control
        # what is deployed on EKS
        ec2_admin_role = iam.Role(
            self,
            "EC2AdminRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"), iam.AccountRootPrincipal()
            ),
        )
        ec2_admin_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
        )
        ec2_admin_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchAgentAdminPolicy")
        )
        ec2_admin_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchAgentServerPolicy")
        )
        ec2_admin_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )

        # What to install on instance on startup
        ec2_user_data = ec2.UserData.for_linux()

        # Scan this directory for shell scripts starting w/ `00`; have them auto-run on init
        # Based on the user data.
        with open("daskhub/deploy/00-tools.sh", encoding="UTF-8") as file:
            bash_lines = file.read()

        template_src_folder = "daskhub/deploy"
        template_dest_folder = "temp/daskhub/deploy"
        ec2_dest_folder = "/home/ssm-user"

        shutil.rmtree(template_dest_folder, ignore_errors=True)

        apply_jinja_templates_by_dir(template_src_folder, template_dest_folder, {
            'stack': self,
            'base_aws': base_aws,
            'config': self.__daskhub_config,
            'account': account,
        })

        deploy_dirs = [template_dest_folder, template_src_folder]
        init_file_args = []
        config_deploy_files_to_ec2_dest_abspath = {}
        config_deploy_file_list = []

        for deploy_dir in deploy_dirs:
            for file_rel in glob.glob(f"{deploy_dir}/**", recursive=True):
                if os.path.isfile(file_rel):
                    if file_rel in DaskhubStack.FILES_TO_OMIT:
                        continue
                    if file_rel.endswith(".j2"):
                        continue

                    file_relative_to_src_folder = file_rel[len(deploy_dir)+1:]
                    ec2_dest_abs_path = f"{ec2_dest_folder}/{file_relative_to_src_folder}"
                    if ec2_dest_abs_path in config_deploy_files_to_ec2_dest_abspath:
                        if WARN_ON_DUPLICATE_FILES:
                            print(f"WARN: Skipping file {file_rel} in {deploy_dir}, "
                                  + f"already exists {ec2_dest_abs_path}")
                        continue

                    print(f"  + {file_rel} -> {ec2_dest_abs_path}")
                    config_deploy_file_list.append(ec2_dest_abs_path)
                    config_deploy_files_to_ec2_dest_abspath[ec2_dest_abs_path] = file_rel

        # potentially, tar the file and extract if this doesn't work.
        for i, ec2_dest_abs_path in enumerate(config_deploy_file_list):
            # if i <= 24:
            file_rel = config_deploy_files_to_ec2_dest_abspath[ec2_dest_abs_path]


            print(f"  + {os.path.join(os.getcwd(), file_rel)} -> {ec2_dest_abs_path}")
            if file_rel.split(".")[-1] == "sh":
                mode = "000777"  # All levels read/write/execute
            else:
                mode = "000666"  # All levels read/write
            init_file_args.append(
                ec2.InitFile.from_existing_asset(
                    ec2_dest_abs_path,
                    s3_assets.Asset(
                        self,
                        f"K8sAssets{i}",
                        path=os.path.join(os.getcwd(), file_rel),
                    ),
                    owner="ssm-user",
                    mode=mode,
                )
            )

        init_data = ec2.CloudFormationInit.from_elements(*init_file_args)

        # pylint: disable=line-too-long
        ec2_user_data.add_commands(
            "sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm",
            "sudo yum -y install jq gettext bash-completion moreutils docker unzip nano git",
            f"sudo yum install -y {DaskhubStack.SSM_AGENT_RPM}",
            "restart amazon-ssm-agent",
            "adduser -m ssm-user",
            'echo "ssm-user ALL=(ALL) NOPASSWD:ALL" | tee  /etc/sudoers.d/ssm-agent-users',
            "chmod 440 /etc/sudoers.d/ssm-agent-users ",
            bash_lines,
            "sudo chown -R ssm-user:ssm-user /home/ssm-user",  # This doesn't seem to address folder permissions...
        )
        # pylint: enable=line-too-long

        # Create admin instance and attach role
        ec2_instance = ec2.Instance(
            self,
            "DaskhubInstance",
            vpc=base_aws.heliocloud_vpc,
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            instance_type=ec2.InstanceType("t2.micro"),
            role=ec2_admin_role,
            user_data=ec2_user_data,
            vpc_subnets=ec2.SubnetSelection(subnets=base_aws.heliocloud_vpc.private_subnets),
            init=init_data,
        )

        ####################################################
        # Managed Policies (S3 access and K8s autoscaling) #
        ####################################################

        route53_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect = iam.Effect.ALLOW,
                    actions=[
                        "route53:ChangeResourceRecordSets",
                    ],
                    resources=[
                        f"{self.hosted_zone.hosted_zone_arn}"
                    ]
                ),
                iam.PolicyStatement(
                    effect = iam.Effect.ALLOW,
                    actions=[
                        "route53:ListHostedZones",
                        "route53:ListResourceRecordSets",
        				"route53:ListTagsForResource"
                    ],
                    resources=[
                        "*",
                    ]
                ),
            ]
        )

        route53_managed_policy = iam.ManagedPolicy(
            self, "AllowExternalDNSUpdates", document=route53_policy_document
        )

        autoscaling_custom_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "autoscaling:DescribeAutoScalingGroups",
                        "autoscaling:DescribeAutoScalingInstances",
                        "autoscaling:DescribeLaunchConfigurations",
                        "autoscaling:DescribeScalingActivities",
                        "autoscaling:DescribeTags",
                        "ec2:DescribeInstanceTypes",
                        "ec2:DescribeLaunchTemplateVersions",
                        "autoscaling:SetDesiredCapacity",
                        "autoscaling:TerminateInstanceInAutoScalingGroup",
                        "ec2:DescribeImages",
                        "ec2:GetInstanceTypesFromInstanceRequirements",
                        "eks:DescribeNodegroup"
                    ],
                    resources=["*"],
                )
            ]
        )

        autoscaling_managed_policy = iam.ManagedPolicy(
            self, "K8AutoScalingManagedPolicy", document=autoscaling_custom_policy_document
        )

        efs_mount_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
				"elasticfilesystem:DescribeMountTargets",
				"elasticfilesystem:CreateMountTarget",
				"ec2:DescribeAvailabilityZones",
				"eks:DescribeCluster",
				"ec2:DescribeSubnets",
				"elasticfilesystem:DeleteMountTarget"
                    ],
                    resources=["*"],
                )
            ]
        )

        efs_mount_managed_policy = iam.ManagedPolicy(
            self, "EfsMountManagedPolicy", document=efs_mount_policy_document
        )

        file_system = efs.FileSystem(
            self,
            "DaskhubEFS",
            vpc=base_aws.heliocloud_vpc,
            encrypted=True,
            enable_automatic_backups=True,

        )

        oauth_base_url=(f"https://{self.__daskhub_config['daskhub']['domain_record']}."
            f"{self.__daskhub_config['daskhub']['domain_url']}")
        callback_url=f"{oauth_base_url}/hub/oauth_callback"
        logout_url=f"{oauth_base_url}/logout"

        # Add Daskhub as a client to the Cognito user pool
        # pylint: disable=duplicate-code
        daskhub_client = base_auth.userpool.add_client(
            "heliocloud-daskhub",
            generate_secret=True,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.PHONE,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.COGNITO_ADMIN,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=[callback_url],
                logout_urls=[logout_url],
            ),
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            prevent_user_existence_errors=True,
        )

        # Add Daskhub Metrics as a client to the Cognito user pool
        # pylint: disable=duplicate-code
        if "daskhub_metrics" in config["enabled"] and config["enabled"]["daskhub_metrics"]:
            oauth_base_url = ("https://"
                            f"{self.__daskhub_config['monitoring']['cost_analyzer_domain_prefix']}."
                            f"{self.__daskhub_config['daskhub']['domain_url']}")
            callback_url = f"{oauth_base_url}/model/oidc/authorize"
            logout_url = f"{oauth_base_url}/logout"

            kubecost_client = base_auth.userpool.add_client(
                "heliocloud-kubecost",
                generate_secret=True,
                o_auth=cognito.OAuthSettings(
                    flows=cognito.OAuthFlows(authorization_code_grant=True),
                    scopes=[
                        cognito.OAuthScope.PHONE,
                        cognito.OAuthScope.EMAIL,
                        cognito.OAuthScope.OPENID,
                        cognito.OAuthScope.COGNITO_ADMIN,
                        cognito.OAuthScope.PROFILE,
                    ],
                    callback_urls=[callback_url],
                    logout_urls=[logout_url],
                ),
                supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
                prevent_user_existence_errors=True,
            )

            # Set conditional output for the kubecost client
            cdk.CfnOutput(self, "CognitoClientIdKubeCost",
                          value=kubecost_client.user_pool_client_id)

        self.build_route53_settings()

        # AWS KMS key required for K8 to encrypt/decrypt secrets during its deployment
        kms_key = kms.Key(self, id=construct_id + "-key", removal_policy=RemovalPolicy.DESTROY)

        auth = config["auth"]
        domain_prefix = auth.get("domain_prefix", "")
        # pylint: enable=duplicate-code

        # Cloudformation outputs
        # Return instance ID to make logging into admin instance easier
        cdk.CfnOutput(self, "Instance ID", value=ec2_instance.instance_id)
        cdk.CfnOutput(self, "KMSArn", value=kms_key.key_arn)
        cdk.CfnOutput(self, "ASGArn", value=autoscaling_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, "CustomS3Arn", value=base_aws.s3_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, "AdminRoleArn", value=ec2_admin_role.role_arn)
        cdk.CfnOutput(self, "Route53Arn", value=route53_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, "EFSId", value=file_system.file_system_id)
        cdk.CfnOutput(self, "EFSMountArn", value=efs_mount_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, "CognitoClientId", value=daskhub_client.user_pool_client_id)
        cdk.CfnOutput(self, "CognitoDomainPrefix", value=domain_prefix)
        cdk.CfnOutput(self, "CognitoUserPoolId", value=base_auth.userpool.user_pool_id)


    @staticmethod
    def load_configurations(config: dict) -> dict:
        """
        This method will load the daskhub configurations from the heliocloud instance
        configurations and the defaults.
        :param config: the heliocloud instance configurations
        :return: the daskhub configurations
        """

        default_cfg = None
        with open(
                f"{os.path.dirname(os.path.abspath(__file__))}/default-constants.yaml",
                "r",
                encoding="UTF-8",
        ) as stream:
            try:
                default_cfg = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        daskhub_config = config["daskhub"]
        if daskhub_config is None:
            daskhub_config = {}

        if default_cfg is not None:
            for key, value in default_cfg.items():
                if key not in daskhub_config:
                    daskhub_config[key] = value

        print("Preparing daskhub environment with the following settings:")
        for key, value in daskhub_config.items():
            print(f"{key}: {value}")

        return daskhub_config

    def build_hosted_zone(self):
        """
        This method creates a CDK route53 construct from a domain lookup under the 
        assumption it already exists.
        """
        domain_url = self.__daskhub_config['daskhub']['domain_url']
        self.hosted_zone = route53.PublicHostedZone.from_lookup(
            self, "HostedZone", domain_name=domain_url
        )

        if self.hosted_zone.is_resource(self):
            self.hosted_zone = route53.PublicHostedZone(
                self, "HostedZone", zone_name=domain_url
            )

    def build_route53_settings(self):
        """
        This method will configure the Route53 settings for daskhub.  These settings
        will be subsequently updated during the EKSCTL portions of the deployment.  It's safe
        to run this deployment from a live system.
        """

        ttl = Duration.seconds(300)
        domain_name = "0.0.0.0"
        full_name = f"{self.__daskhub_config['daskhub']['domain_record']}." \
                    f"{self.__daskhub_config['daskhub']['domain_url']}."

        record = find_route53_record_by_type_and_name(
            self.hosted_zone.hosted_zone_id, 'CNAME',
            full_name
        )
        if record is not None:
            print(f"Route53 record set already exists for {full_name}")
            ttl = Duration.seconds(record['TTL'])
            domain_name = record['ResourceRecords'][0]['Value']
            print(f" Using ttl={ttl.to_seconds()}, domain_name={domain_name}")

        cname_record = route53.CnameRecord(
            self,
            "CnameRecord",
            record_name=self.__daskhub_config['daskhub']['domain_record'],
            zone=self.hosted_zone,
            ttl=ttl,
            delete_existing=True,
            domain_name=domain_name,
            comment="Initial provisioning from CDK, updated via external-dns."
        )
        cname_record.apply_removal_policy(RemovalPolicy.DESTROY)
