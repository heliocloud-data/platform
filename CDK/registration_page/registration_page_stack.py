"""
CDK Stack definition for deploying the Regsistration Page module of a HelioCloud instance.
"""

import os.path

import aws_cdk.custom_resources
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_cognito as cognito,
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


class RegistrationPageStack(Stack):
    """
    Stack to install the Heliocloud Regsistration Page module.
    There are two major components to this stack:
    - the creation of the user in AWS Cognito, for authentication purposes
    - the creation of an AWS Fargate cluster in which the Regsistration Page will run
    - the creation of a Regsistration Page Docker image and its deployment into the Fargate cluster
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
        Instantiates a Regsistration Page stack.
        """
        super().__init__(scope=scope, id=construct_id, **kwargs)

        # Extract the important bits from the Regsistration Page's config
        registration_url = f'https://{config.get("domain_record")}.' f'{config.get("domain_url")}'

        # Add the Regsistration Page as a client of the Cognito user pool for this HelioCloud
        # pylint: disable=duplicate-code
        user_pool_client = self.__create_user_pool_client(
            auth_stack=auth_stack, registration_url=registration_url
        )

        # Create the Fargate cluster that will host the Regsistration Page
        cluster = self.__create_fargate_cluster(vpc=aws_stack.heliocloud_vpc)

        # Create the Docker image for the Regsistration Page
        docker_build_args = {}
        if "docker" in config and "build_args" in config["docker"]:
            docker_build_args = config.get("docker").get("build_args")
        docker_image = self.__create_registration_docker_image(build_args=docker_build_args)

        # Create the Regsistration Page task for Fargate
        task = self.__create_fargate_task(
            vpc=aws_stack.heliocloud_vpc,
            docker_image=docker_image,
            user_pool=auth_stack.userpool,
            user_pool_client=user_pool_client,
        )

        # Create the load balancer to route traffic to the Regsistration Page service
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
        self, auth_stack: AuthStack, registration_url: str
    ) -> aws_cdk.aws_cognito.UserPoolClient:
        """
        Add the Regsistration Page as client of the AWS Cognito User Pool
        for this HelioCloud instance.
        """
        client = auth_stack.userpool.add_client(
            "heliocloud-registration-site",
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
                callback_urls=[f"{registration_url}/loggedin"],
                logout_urls=[f"{registration_url}/logout"],
            ),
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            prevent_user_existence_errors=True,
        )
        return client

    def __create_fargate_cluster(self, vpc: ec2.Vpc) -> ecs.Cluster:
        """
        Creates the Fargate cluster in which the Regsistration Page will be hosted
        """
        cluster = ecs.Cluster(self, "RegistrationCluster", vpc=vpc)
        cluster.add_default_cloud_map_namespace(name="registration.local")
        return cluster

    def __create_registration_docker_image(self, build_args: dict) -> ecr_assets.DockerImageAsset:
        """
        Create the Docker image of the Regsistration Page application, for deployment into AWS ECR.
        """
        # Construct the Docker image asset that ECR will need
        # Build args have to get turned into strings for DockerImageAsset to accept them
        args = {}
        if build_args is not None:
            args = {key: str(build_args[key]) for key in build_args.keys()}
        print(f"Registration Docker Image build is using args: {args}")
        directory = os.path.dirname(__file__)
        return ecr_assets.DockerImageAsset(
            self,
            "RegistrationDocker",
            directory=directory,
            file="Dockerfile",
            build_args=args,
        )

    # pylint: disable=too-many-arguments
    def __create_fargate_task(
        self,
        docker_image: ecr_assets.DockerImageAsset,
        vpc: ec2.Vpc,
        user_pool: cognito.UserPool,
        user_pool_client: cognito.UserPoolClient,
    ) -> ecs.FargateTaskDefinition:
        """
        Create the task in Fargate to run the Regsistration Page.
        """

        # Create default EC2 security group
        security_group = ec2.SecurityGroup(
            self,
            "RegistrationEc2SecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(22))
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(443))
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(80))
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))
        security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))

        task_role = iam.Role(
            self,
            "FargateTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Role for Fargate task to call Cognito admin APIs",
        )

        # Add Cognito Permissions to the Task Role
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminDisableUser",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:ListUsers",
                ],
                resources=["arn:aws:cognito-idp:*:*:userpool/*"],  # Scope to all user pools
            )
        )

        # Create the task & container
        task = ecs.FargateTaskDefinition(
            self, "RegsistrationFargateTask", cpu=256, memory_limit_mib=512, task_role=task_role
        )
        task.add_container(
            "RegistrationContainer",
            image=ecs.ContainerImage.from_docker_image_asset(docker_image),
            essential=True,
            environment={
                "REGION": self.region,
                "USER_POOL_ID": user_pool.user_pool_id,
            },
            secrets={
                # Need the user pool id
                "USER_POOL_CLIENT_SECRET": ecs.Secret.from_secrets_manager(
                    sm.Secret(
                        self,
                        "registration_user_pool_client_secret",
                        secret_string_value=user_pool_client.user_pool_client_secret,
                    )
                ),
                "USER_POOL_CLIENT_ID": ecs.Secret.from_secrets_manager(
                    sm.Secret(
                        self,
                        "registration_user_pool_client_id",
                        secret_string_value=aws_cdk.SecretValue(
                            user_pool_client.user_pool_client_id
                        ),
                    )
                ),
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="RegistrationContainer",
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
        Regsistration Page service.
        """

        # Hosted Zone for resolving in DNS
        zone = route53.PublicHostedZone.from_lookup(
            self, "RegistrationHostedZone", domain_name=domain
        )
        if zone.is_resource(self):
            zone = route53.PublicHostedZone(self, "RegistrationHostedZone", zone_name=domain)

        # Security group
        security_group = ec2.SecurityGroup(
            self,
            "RegistrationSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )

        # Set up the load balancer
        registration_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "RegistrationFargate",
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
        registration_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200-499",
        )

    # pylint: enable=too-many-arguments
