"""
CDK Stack definition for deploying the Portal module of a HelioCloud instance.
"""
import os.path
import secrets as pysecrets

import aws_cdk.custom_resources
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_cognito_identitypool_alpha as identity_pool,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
    aws_logs as logs,
    aws_secretsmanager as sm,
    aws_route53 as route53,
    aws_certificatemanager as cm,
    aws_ec2 as ec2,
)
from constructs import Construct

from base_auth.auth_stack import AuthStack
from base_aws.base_aws_stack import BaseAwsStack


class PortalStack(Stack):
    """
    Stack to install the Heliocloud Portal module. There are two major components to this stack:
    - the creation of the user & id pools in AWS Cognito, for authentication purposes
    - the creation of an AWS Fargate cluster in which the Portal will run
    - the creation of a Portal Docker image and its deployment into the Fargate cluster
    """

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        aws_stack: BaseAwsStack,
        auth_stack: AuthStack,
        **kwargs,
    ) -> None:
        """
        Instantiates a Portal stack.
        """
        super().__init__(scope=scope, id=construct_id, **kwargs)

        # Extract the important bits from the Portal's config
        portal_url = f'https://{config.get("domain_record")}.' f'{config.get("domain_url")}'

        # Add the Portal as a client of the Cognito user pool for this HelioCloud
        # pylint: disable=duplicate-code
        user_pool_client = self.__create_user_pool_client(
            auth_stack=auth_stack, portal_url=portal_url
        )

        # Create an Identity Pool with the appropriate permissions for Portal Users
        id_pool = self.__create_identity_pool(
            user_pool=auth_stack.userpool, user_pool_client=user_pool_client
        )

        # Create the Fargate cluster that will host the Portal
        cluster = self.__create_fargate_cluster(vpc=aws_stack.heliocloud_vpc)

        # Create the Docker image for the Portal
        docker_build_args = {}
        if "docker" in config and "build_args" in config["docker"]:
            docker_build_args = config.get("docker").get("build_args")
        docker_image = self.__create_portal_docker_image(build_args=docker_build_args)

        # Create the Portal task for Fargate
        task = self.__create_fargate_task(
            app_name=auth_stack.domain_prefix,
            vpc=aws_stack.heliocloud_vpc,
            url=portal_url,
            docker_image=docker_image,
            s3_policy=aws_stack.s3_managed_policy,
            id_pool=id_pool,
            user_pool=auth_stack.userpool,
            user_pool_client=user_pool_client,
        )

        # Create the load balancer to route traffic to the Portal service
        cert_arn = config.get("domain_certificate_arn")
        domain_url = config.get("domain_url")
        sub_domain = config.get("domain_record")
        self.__create_load_balancer(
            cluster=cluster,
            vpc=aws_stack.heliocloud_vpc,
            cert_arn=cert_arn,
            domain=domain_url,
            sub_domain=sub_domain,
            task=task,
        )

    # pylint: enable=too-many-arguments
    # pylint: enable=too-many-locals

    def __create_user_pool_client(
        self, auth_stack: AuthStack, portal_url: str
    ) -> aws_cdk.aws_cognito.UserPoolClient:
        """
        Add the Portal as client of the AWS Cognito User Pool for this HelioCloud instance
        """
        client = auth_stack.userpool.add_client(
            "heliocloud-portal",
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
                callback_urls=[f"{portal_url}/loggedin"],
                logout_urls=[f"{portal_url}/logout"],
            ),
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            prevent_user_existence_errors=True,
        )
        return client

    def __create_identity_pool(
        self, user_pool: cognito.UserPool, user_pool_client: cognito.UserPoolClient
    ) -> identity_pool.IdentityPool:
        """
        Returns a configured Identity Pool for the Portal
        """

        # Build the Pool
        id_pool = identity_pool.IdentityPool(
            self,
            "IdentityPool",
            identity_pool_name="portal_idpool",
            authentication_providers=identity_pool.IdentityPoolAuthenticationProviders(
                user_pools=[
                    identity_pool.UserPoolAuthenticationProvider(
                        user_pool=user_pool, user_pool_client=user_pool_client
                    )
                ]
            ),
        )

        # Attach an IAM policy to use for Authenticated users
        authenticated_policy = iam.Policy(
            self,
            "PortalAuthPolicy",
            document=iam.PolicyDocument.from_json(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "VisualEditor0",
                            "Effect": "Allow",
                            "Action": [
                                "iam:DeleteAccessKey",
                                "ec2:AuthorizeSecurityGroupIngress",
                                "ec2:DescribeInstances",
                                "ec2:CreateKeyPair",
                                "ec2:CreateImage",
                                "ce:GetCostAndUsage",
                                "iam:ListMFADevices",
                                "cognito-sync:*",
                                "pricing:GetProducts",
                                "iam:CreateAccessKey",
                                "iam:PassRole",
                                "ec2:StartInstances",
                                "ec2:CreateSecurityGroup",
                                "ec2:DescribeKeyPairs",
                                "iam:ListAccessKeys",
                                "cognito-identity:*",
                                "ec2:TerminateInstances",
                                "ec2:DescribeLaunchTemplates",
                                "ec2:CreateTags",
                                "ec2:DescribeLaunchTemplateVersions",
                                "iam:UpdateAccessKey",
                                "ec2:RunInstances",
                                "ec2:StopInstances",
                                "ec2:DescribeSecurityGroups",
                                "ec2:DescribeImages",
                                "ec2:CreateLaunchTemplate",
                                "ec2:DescribeVpcs",
                                "mobileanalytics:PutEvents",
                                "ec2:DescribeInstanceTypes",
                                "iam:GetUser",
                                "ec2:DescribeSubnets",
                                "ec2:DeleteKeyPair",
                                "ec2:AssociateIamInstanceProfile",
                                "ec2:ReplaceIamInstanceProfileAssociation",
                            ],
                            "Resource": "*",
                        }
                    ],
                }
            ),
        )
        id_pool.authenticated_role.attach_inline_policy(authenticated_policy)

        # Attach an IAM policy for unauthenticated users
        unauthenticated_policy = iam.Policy(
            self,
            "PortalUnauthPolicy",
            document=iam.PolicyDocument.from_json(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["mobileanalytics:PutEvents", "cognito-sync:*"],
                            "Resource": ["*"],
                        }
                    ],
                }
            ),
        )
        id_pool.unauthenticated_role.attach_inline_policy(unauthenticated_policy)

        return id_pool

    def __create_fargate_cluster(self, vpc: ec2.Vpc) -> ecs.Cluster:
        """
        Creates the Fargate cluster in which the Portal will be hosted
        """
        cluster = ecs.Cluster(self, "PortalCluster", vpc=vpc)
        cluster.add_default_cloud_map_namespace(name="portal.local")
        return cluster

    def __create_portal_docker_image(self, build_args: dict) -> ecr_assets.DockerImageAsset:
        """
        Create the Docker image of the Portal application, for deployment into AWS ECR.
        """
        # Construct the Docker image asset that ECR will need
        # Build args have to get turned into strings for DockerImageAsset to accept them
        args = {}
        if build_args is not None:
            args = {key: str(build_args[key]) for key in build_args.keys()}
        print(f"Portal Docker Image build is using args: {args}")
        directory = os.path.dirname(__file__)
        return ecr_assets.DockerImageAsset(
            self,
            "PortalDocker",
            directory=directory,
            file="Dockerfile",
            build_args=args,
        )

    # pylint: disable=too-many-arguments
    def __create_fargate_task(
        self,
        app_name: str,
        url: str,
        docker_image: ecr_assets.DockerImageAsset,
        vpc: ec2.Vpc,
        s3_policy: iam.ManagedPolicy,
        id_pool: identity_pool.IdentityPool,
        user_pool: cognito.UserPool,
        user_pool_client: cognito.UserPoolClient,
    ) -> ecs.FargateTaskDefinition:
        """
        Create the task in Fargate to run the Portal.
        """

        # Create default EC2 security group
        security_group = ec2.SecurityGroup(
            self,
            "PortalEc2SecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(22))
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(443))
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(80))
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))

        # What is this for?
        ec2_default_role = iam.Role(
            self,
            "PortalEc2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="Default Portal EC2 Role with S3 access",
        )
        ec2_default_role.add_managed_policy(s3_policy)
        ec2_default_instance_profile = iam.CfnInstanceProfile(
            self,
            "PortalEc2InstanceProfile",
            roles=[ec2_default_role.role_name],
        )

        # Create the task & container
        task = ecs.FargateTaskDefinition(self, "PortalFargateTask", cpu=256, memory_limit_mib=512)
        task.add_container(
            "PortalContainer",
            image=ecs.ContainerImage.from_docker_image_asset(docker_image),
            essential=True,
            environment={
                "APP_NAME": app_name,
                "REGION": self.region,
                "PYTHONBUFFERED": "1",
                "USER_POOL_ID": user_pool.user_pool_id,
                "SITE_URL": url,
                "DEFAULT_SECURITY_GROUP_ID": security_group.security_group_id,
                "DEFAULT_EC2_INSTANCE_PROFILE_ARN": ec2_default_instance_profile.attr_arn,
                "DEFAULT_EC2_SUBNET_ID": vpc.public_subnets[0].subnet_id,
            },
            secrets={
                # Need the identity pool id
                "IDENTITY_POOL_ID": ecs.Secret.from_secrets_manager(
                    sm.Secret(
                        self,
                        "portal_identity_pool_id",
                        secret_string_value=aws_cdk.SecretValue(id_pool.identity_pool_id),
                    )
                ),
                # Need the user pool id
                "USER_POOL_CLIENT_SECRET": ecs.Secret.from_secrets_manager(
                    sm.Secret(
                        self,
                        "portal_user_pool_client_secret",
                        secret_string_value=user_pool_client.user_pool_client_secret,
                    )
                ),
                "USER_POOL_CLIENT_ID": ecs.Secret.from_secrets_manager(
                    sm.Secret(
                        self,
                        "portal_user_pool_client_id",
                        secret_string_value=aws_cdk.SecretValue(
                            user_pool_client.user_pool_client_id
                        ),
                    )
                ),
                "FLASK_SECRET_KEY": ecs.Secret.from_secrets_manager(
                    sm.Secret(
                        self,
                        "flask_secret_key",
                        secret_string_value=aws_cdk.SecretValue(pysecrets.token_hex(16)),
                    )
                ),
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="PortalContainer",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
        ).add_port_mappings(ecs.PortMapping(container_port=80, host_port=80))

        return task

    # pylint: enable=too-many-arguments

    # pylint: disable=too-many-arguments
    def __create_load_balancer(
        self,
        cluster: ecs.Cluster,
        vpc: ec2.Vpc,
        task: ecs.FargateTaskDefinition,
        sub_domain: str,
        domain: str,
        cert_arn: str,
    ) -> None:
        """
        Creates the Application Load Balancer for routing HTTPs traffic to the
        Portal service.
        """

        # Hosted Zone for resolving in DNS
        zone = route53.PublicHostedZone.from_lookup(self, "PortalHostedZone", domain_name=domain)
        if zone.is_resource(self):
            zone = route53.PublicHostedZone(self, "PortalHostedZone", zone_name=domain)

        # Security group
        security_group = ec2.SecurityGroup(
            self,
            "PortalSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )

        # Set up the load balancer
        portal_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "PortalFargate",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            public_load_balancer=True,
            security_groups=[security_group],
            task_definition=task,
            listener_port=443,
            domain_name=f"{sub_domain}.{domain}",
            domain_zone=zone,
            certificate=cm.Certificate.from_certificate_arn(self, "domainCert", cert_arn),
            record_type=aws_cdk.aws_ecs_patterns.ApplicationLoadBalancedServiceRecordType.ALIAS,
            redirect_http=True,
            assign_public_ip=True,
        )

        # Add a health check
        portal_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200-499",
        )

    # pylint: enable=too-many-arguments
