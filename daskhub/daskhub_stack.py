"""
This file contains the CDK stack for deploying Daskhub.
"""

import os
import re
import yaml

import aws_cdk as cdk
from aws_cdk import (
    Stack,
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


class DaskhubStack(Stack):
    """
    CDK stack for installing DaskHub for a HelioCloud instance
    """

    FILES_TO_OMIT = {"daskhub/deploy/app.config", "daskhub/deploy/app.config.template"}

    # URL to download the SSM_AGENT
    SSM_AGENT_RPM = "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm"  # pylint: disable=line-too-long

    # fmt: off
    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
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
        DaskhubStack.generate_app_config_from_template(self.__daskhub_config)

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

        with open("daskhub/deploy/00-tools.sh", encoding="UTF-8") as file:
            bash_lines = file.read()

        init_file_args = []
        deploy_dirs = ["daskhub/deploy", "temp/daskhub/deploy"]
        config_deploy_file_list = []

        for deploy_dir in deploy_dirs:
            for file in os.listdir(deploy_dir):
                file_rel = os.path.join(deploy_dir, file)
                if os.path.isfile(file_rel):
                    if file_rel in DaskhubStack.FILES_TO_OMIT:
                        continue

                    config_deploy_file_list.append(file_rel)

        for i, file_rel in enumerate(config_deploy_file_list):
            if file_rel.split(".")[-1] == "sh":
                mode = "000777"  # All levels read/write/execute
            else:
                mode = "000666"  # All levels read/write
            file = os.path.basename(file_rel)
            init_file_args.append(
                ec2.InitFile.from_existing_asset(
                    f"/home/ssm-user/{file}",
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
            "sudo chown -R ssm-user:ssm-user /home/ssm-user",
        )
        # pylint: enable=line-too-long

        # Create admin instance and attach role
        instance = ec2.Instance(
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

        file_system = efs.FileSystem(
            self,
            "DaskhubEFS",
            vpc=base_aws.heliocloud_vpc,
            encrypted=True,
            enable_automatic_backups=True,
        )

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
                callback_urls=["https://example.com/hub/oauth_callback"],
                logout_urls=["https://example.com/logout"],
            ),
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            prevent_user_existence_errors=True,
        )
        self.build_route53_settings()

        daskhub_client_id = daskhub_client.user_pool_client_id
        auth = config["auth"]
        domain_prefix = auth.get("domain_prefix", "")
        # pylint: enable=duplicate-code

        # Cloudformation outputs
        # Return instance ID to make logging into admin instance easier
        cdk.CfnOutput(self, "Instance ID", value=instance.instance_id)
        cdk.CfnOutput(self, "ASGArn", value=autoscaling_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, "KMSArn", value=base_aws.kms.key_arn)
        cdk.CfnOutput(self, "CustomS3Arn", value=base_aws.s3_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, "AdminRoleArn", value=ec2_admin_role.role_arn)
        cdk.CfnOutput(self, "EFSId", value=file_system.file_system_id)
        cdk.CfnOutput(self, "CognitoClientId", value=daskhub_client_id)
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

    @staticmethod
    def generate_app_config_from_template(
            daskhub_config: dict,
            src_file: str = "daskhub/deploy/app.config.template",
            dest_file: str = "temp/daskhub/deploy/app.config",
    ):
        """
        This method will generate the 'app.config' file to be deployed to the
        ec2 instance from the template.
        :param daskhub_config: the dictionary containing the 'daskhub' values from
                               the heliocloud instance configuration
        :param src_file:       the source file
        :param dest_file:      the destination file
        """
        with open(src_file, encoding="UTF-8") as file:
            app_config_lines = file.read()

        keys_to_add = []
        for key, value in daskhub_config.items():
            new_app_config_lines = re.sub(
                rf"^{key}=.*$", f"{key}='{value}'", app_config_lines, flags=re.MULTILINE
            )
            if new_app_config_lines == app_config_lines:
                keys_to_add.append(key)
            else:
                app_config_lines = new_app_config_lines

        if len(keys_to_add) > 0:
            app_config_lines = app_config_lines + "\n\n"
            app_config_lines = (
                    app_config_lines + "# Custom variables injected via heliocloud instance.yaml"
            )
            app_config_lines = app_config_lines + "\n"

        for key in keys_to_add:
            value = daskhub_config[key]
            app_config_lines = app_config_lines + f"{key}='{value}'\n"

        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        with open(dest_file, "w", encoding="UTF-8") as text_file:
            text_file.write(app_config_lines)

    def build_route53_settings(self):
        """
        This method will configure the Route53 settings for daskhub.  These settings
        will be subsequently updated during the EKSCTL portions of the deployment.  It's safe
        to run this deployment from a live system.
        """

        domain_url = self.__daskhub_config['ROUTE53_HOSTED_ZONE']
        hosted_zone = route53.PublicHostedZone.from_lookup(
            self, "HostedZone", domain_name=domain_url
        )
        if hosted_zone.is_resource(self):
            hosted_zone = route53.PublicHostedZone(
                self, "HostedZone", zone_name=domain_url
            )

        cname_record = route53.CnameRecord(
            self,
            "CnameRecord",
            record_name=self.__daskhub_config['ROUTE53_DASKHUB_PREFIX'],
            zone=hosted_zone,
            ttl=Duration.seconds(300),
            domain_name="0.0.0.0",
            comment="Initial provisioning from CDK, overridded by EKSCTL deployment."
        )
        cname_record.apply_removal_policy(RemovalPolicy.DESTROY)
