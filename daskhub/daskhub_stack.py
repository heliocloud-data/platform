import os

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_s3_assets as s3_assets,
    aws_cognito as cognito,
)
from constructs import Construct
from base_aws.base_aws_stack import BaseAwsStack

class DaskhubStack(Stack):
    """
    CDK stack for installing DaskHub for a HelioCloud instance
    """

    def __init__(self, scope: Construct, construct_id: str, config: dict, base_aws: BaseAwsStack, base_auth: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        with open('daskhub/deploy/00-tools.sh', encoding='UTF-8') as file:
            bash_lines = file.read()

        init_file_args = []
        deploy_dir = 'daskhub/deploy'
        config_deploy_file_list = [f for f in os.listdir(
            deploy_dir) if os.path.isfile(os.path.join(deploy_dir, f))]
        for i, f in enumerate(config_deploy_file_list):
            if f.split(".")[-1] == 'sh':
                mode = '000777'  # All levels read/write/execute
            else:
                mode = '000666'  # All levels read/write
            init_file_args.append(ec2.InitFile.from_existing_asset(f"/home/ssm-user/{f}",
                                                                   s3_assets.Asset(self, f'K8sAssets{i}', path=os.path.join(
                                                                       os.getcwd(), f'daskhub/deploy/{f}')),
                                                                   owner='ssm-user',
                                                                   mode=mode))

        init_data = ec2.CloudFormationInit.from_elements(*init_file_args)

        ec2_user_data.add_commands('sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm',
                                   'sudo yum -y install jq gettext bash-completion moreutils docker unzip nano git',
                                   f'sudo yum install -y {SSM_AGENT_RPM}',
                                   'restart amazon-ssm-agent',
                                   'adduser -m ssm-user',
                                   'echo "ssm-user ALL=(ALL) NOPASSWD:ALL" | tee  /etc/sudoers.d/ssm-agent-users',
                                   'chmod 440 /etc/sudoers.d/ssm-agent-users ',
                                   bash_lines,
                                   'sudo chown -R ssm-user:ssm-user /home/ssm-user'
                                   )

        # TODO: add cloudwatch logs to SSM
        # Create admin instance and attach role
        instance = ec2.Instance(self, "DaskhubInstance",
                                vpc=base_aws.heliocloud_vpc,
                                machine_image=ec2.MachineImage.latest_amazon_linux(),
                                instance_type=ec2.InstanceType('t2.micro'),
                                role=ec2_admin_role,
                                user_data=ec2_user_data,
                                vpc_subnets=ec2.SubnetSelection(
                                    subnets=base_aws.heliocloud_vpc.private_subnets),
                                init=init_data)

        ####################################################
        # Managed Policies (S3 access and K8s autoscaling) #
        ####################################################

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
                                     vpc=base_aws.heliocloud_vpc,
                                     encrypted=True,
                                     enable_automatic_backups=True
                                     )

        ##############################################
        # Authentication and Authorization (Cognito) #
        ##############################################
        # TODO make these configurable (with defaults), note changes to this 
        # need to be reflected in the "deploy/dh-auth.yaml.template" file
        # or things could break
        daskhub_client = base_auth.userpool.add_client("heliocloud-daskhub",
                                                       generate_secret=True,
                                                       o_auth=cognito.OAuthSettings(
                                                           flows=cognito.OAuthFlows(
                                                               authorization_code_grant=True),
                                                           scopes=[cognito.OAuthScope.PHONE,
                                                                   cognito.OAuthScope.EMAIL,
                                                                   cognito.OAuthScope.OPENID,
                                                                   cognito.OAuthScope.COGNITO_ADMIN,
                                                                   cognito.OAuthScope.PROFILE],
                                                           callback_urls=[
                                                               'https://example.com/hub/oauth_callback'],
                                                           logout_urls=['https://example.com/logout']),
                                                       supported_identity_providers=[
                                                           cognito.UserPoolClientIdentityProvider.COGNITO],
                                                       prevent_user_existence_errors=True)
        daskhub_client_id = daskhub_client.user_pool_client_id
        auth = config['auth']
        domain_prefix = auth.get('domain_prefix', '')

        ##########################
        # CloudFormation Outputs #
        ##########################

        # Return instance ID to make logging into admin instance easier
        cdk.CfnOutput(self, 'Instance ID',
                      value=instance.instance_id)
        cdk.CfnOutput(self, 'ASGArn',
                      value=autoscaling_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, 'KMSArn',
                      value=base_aws.kms.key_arn)
        cdk.CfnOutput(self, 'CustomS3Arn',
                      value=base_aws.s3_managed_policy.managed_policy_arn)
        cdk.CfnOutput(self, 'AdminRoleArn',
                      value=ec2_admin_role.role_arn)
        cdk.CfnOutput(self, 'EFSId',
                      value=file_system.file_system_id)
        cdk.CfnOutput(self, 'CognitoClientId',
                      value=daskhub_client_id)
        cdk.CfnOutput(self, 'CognitoDomainPrefix',
                      value=domain_prefix)
        cdk.CfnOutput(self, 'CognitoUserPoolId',
                      value=base_auth.userpool.user_pool_id)
