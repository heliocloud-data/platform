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
import secrets as pysecrets
from constructs import Construct
from base_aws.base_aws_stack import BaseAwsStack


class PortalStack(Stack):
    """
    Stack to install HelioCloud user portal.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        base_aws: BaseAwsStack,
        base_auth: Stack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        portal_config = config.get("portal")
        portal_url = (
            f'https://{portal_config.get("domain_record")}.{portal_config.get("domain_url")}'
        )
        auth_config = config.get("auth")
        env_config = config.get("env")

        ##############################################
        # Authentication and Authorization (Cognito) #
        ##############################################
        portal_client = base_auth.userpool.add_client(
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

        ## Create IAM auth/unauth Roles
        authenticated_policy_document = iam.PolicyDocument.from_json(
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
                        ],
                        "Resource": "*",
                    }
                ],
            }
        )
        authenticated_policy = iam.Policy(
            self, "PortalAuthPolicy", document=authenticated_policy_document
        )
        authenticated_role = iam.Role(
            self,
            "PortalAuthRole",
            assumed_by=iam.FederatedPrincipal("cognito-identity.amazonaws.com"),
        )
        authenticated_role.attach_inline_policy(authenticated_policy)
        unauthenticated_policy_document = iam.PolicyDocument.from_json(
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
        )
        unauthenticated_policy = iam.Policy(
            self, "PortalUnauthPolicy", document=unauthenticated_policy_document
        )
        unauthenticated_role = iam.Role(
            self,
            "PortalUnauthRole",
            assumed_by=iam.FederatedPrincipal("cognito-identity.amazonaws.com"),
        )
        unauthenticated_role.attach_inline_policy(unauthenticated_policy)

        ## Create identity pool
        portal_identity_pool = identity_pool.IdentityPool(
            self,
            "IdentityPool",
            identity_pool_name="portal_idpool",
            authentication_providers=identity_pool.IdentityPoolAuthenticationProviders(
                user_pools=[
                    identity_pool.UserPoolAuthenticationProvider(
                        user_pool=base_auth.userpool, user_pool_client=portal_client
                    )
                ]
            ),
            authenticated_role=authenticated_role,
            unauthenticated_role=unauthenticated_role,
        )

        ##############################################
        #    Create Portal Resources and Secrets     #
        ##############################################

        #### Create default EC2 security group
        portal_ec2_default_sg = ec2.SecurityGroup(
            self,
            "PortalEc2SecurityGroup",
            vpc=base_aws.heliocloud_vpc,
            allow_all_outbound=True,
        )
        portal_ec2_default_sg.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(22))
        portal_ec2_default_sg.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(443))
        portal_ec2_default_sg.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(80))
        portal_ec2_default_sg.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))
        portal_ec2_default_sg.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))
        portal_ec2_default_sg.add_egress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))

        ### Create default EC2 policy
        shared_policy = base_aws.s3_managed_policy
        portal_ec2_default_role = iam.Role(
            self,
            "PortalEc2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="Default Portal EC2 Role with S3 access",
        )
        portal_ec2_default_role.add_managed_policy(shared_policy)

        ec2_admin_role = iam.Role(
            self,
            "EC2AdminRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"), iam.AccountRootPrincipal()
            ),
        )
        ### Create Secrets
        identity_pool_id_secret = sm.Secret(
            self,
            "portal_identity_pool_id",
            secret_string_value=aws_cdk.SecretValue(portal_identity_pool.identity_pool_id),
        )
        user_pool_client_id_secret = sm.Secret(
            self,
            "portal_user_pool_client_id",
            secret_string_value=aws_cdk.SecretValue(portal_client.user_pool_client_id),
        )
        user_pool_client_secret_secret = sm.Secret(
            self,
            "portal_user_pool_client_secret",
            secret_string_value=portal_client.user_pool_client_secret,
        )
        flask_secret_key_secret = sm.Secret(
            self,
            "flask_secret_key",
            secret_string_value=aws_cdk.SecretValue(pysecrets.token_hex(16)),
        )

        ##############################################
        #          Cluster and Load Balancer         #
        ##############################################
        portal_cluster = ecs.Cluster(self, "PortalCluster", vpc=base_aws.heliocloud_vpc)
        portal_cluster.add_default_cloud_map_namespace(name="portal.local")
        portal_asset = ecr_assets.DockerImageAsset(
            self, "PortalDocker", directory="./portal", file="./portal/Dockerfile"
        )
        portal_task = ecs.FargateTaskDefinition(
            self, "PortalFargateTask", cpu=256, memory_limit_mib=512
        )
        portal_task.add_container(
            "PortalContainer",
            image=ecs.ContainerImage.from_docker_image_asset(portal_asset),
            essential=True,
            environment={
                "APP_NAME": auth_config.get("domain_prefix"),
                "REGION": env_config.get("region"),
                "PYTHONBUFFERED": "1",
                "USER_POOL_ID": base_auth.userpool.user_pool_id,
                "SITE_URL": portal_url,
                "DEFAULT_SECURITY_GROUP_ID": portal_ec2_default_sg.security_group_id,
                "DEFAULT_EC2_ROLE_ARN": portal_ec2_default_role.role_arn,
                "DEFAULT_EC2_ROLE_NAME": portal_ec2_default_role.role_name,
            },
            secrets={
                "IDENTITY_POOL_ID": ecs.Secret.from_secrets_manager(identity_pool_id_secret),
                "USER_POOL_CLIENT_SECRET": ecs.Secret.from_secrets_manager(
                    user_pool_client_secret_secret
                ),
                "USER_POOL_CLIENT_ID": ecs.Secret.from_secrets_manager(user_pool_client_id_secret),
                "FLASK_SECRET_KEY": ecs.Secret.from_secrets_manager(flask_secret_key_secret),
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="PortalContainer",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
        ).add_port_mappings(ecs.PortMapping(container_port=80, host_port=80))
        portal_hosted_zone = route53.PublicHostedZone.from_lookup(
            self, "PortalHostedZone", domain_name=portal_config.get("domain_url")
        )
        if portal_hosted_zone.is_resource(self):
            portal_hosted_zone = route53.PublicHostedZone(
                self, "PortalHostedZone", zone_name=f"{portal_config.get('domain_url')}"
            )
        portal_security_group = ec2.SecurityGroup(
            self,
            "PortalSecurityGroup",
            vpc=base_aws.heliocloud_vpc,
            allow_all_outbound=True,
        )
        portal_certificate = cm.Certificate.from_certificate_arn(
            self, "domainCert", portal_config.get("domain_certificate_arn")
        )
        portal_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "PortalFargate",
            cluster=portal_cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            public_load_balancer=True,
            security_groups=[portal_security_group],
            task_definition=portal_task,
            listener_port=443,
            domain_name=f"{portal_config.get('domain_record')}.{portal_config.get('domain_url')}",
            domain_zone=portal_hosted_zone,
            certificate=portal_certificate,
            record_type=aws_cdk.aws_ecs_patterns.ApplicationLoadBalancedServiceRecordType.ALIAS,
            redirect_http=True,
            assign_public_ip=True,
        )
        portal_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200-499",
        )
