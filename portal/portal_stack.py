"""
CDK Stack definition for deploying the Portal module of a HelioCloud instance.
"""

import os.path
import secrets as pysecrets

import aws_cdk as cdk
import aws_cdk.custom_resources
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_cognito_identitypool_alpha as identity_pool,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_route53 as route53,
    aws_ec2 as ec2,
    aws_route53 as route53,
    Duration,
    RemovalPolicy,
)
from constructs import Construct

from base_auth.auth_stack import AuthStack
from base_aws.base_aws_stack import BaseAwsStack

from daskhub.aws_utils import get_instance_types_by_region, find_route53_record_by_type_and_name


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

        # Create the Portal task for Fargate
        task = self.__create_ec2_resources(
            vpc=aws_stack.heliocloud_vpc, s3_policy=aws_stack.s3_managed_policy
        )

        self.__build_hosted_zone(config["domain_url"])
        self.__build_route53_settings(
            f"{config['domain_record']}.{config['domain_url']}", config["domain_record"]
        )

        # # Cloudformation outputs
        # # Return instance ID to make logging into admin instance easier
        cdk.CfnOutput(self, "Portal_Ec2SecurityGroup", value=self.security_group.security_group_id)
        cdk.CfnOutput(
            self, "Portal_Ec2InstanceProfile", value=self.ec2_default_instance_profile.attr_arn
        )
        cdk.CfnOutput(
            self, "Portal_Ec2SubnetId", value=aws_stack.heliocloud_vpc.public_subnets[0].subnet_id
        )
        cdk.CfnOutput(self, "Portal_Ec2RoleArn", value=self.ec2_default_role.role_arn)

        cdk.CfnOutput(self, "Portal_IdentityPool", value=id_pool.identity_pool_id)
        cdk.CfnOutput(self, "Portal_CognitoClientId", value=user_pool_client.user_pool_client_id)
        cdk.CfnOutput(self, "Portal_UserPoolId", value=auth_stack.userpool.user_pool_id)

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
                                "s3:ListAllMyBuckets",
                                "s3:CreateBucket",
                                "s3:DeleteBucket",
                                "s3:GetBucketLocation",
                                "s3:ListBucket",
                                "s3:GetBucketPolicy",
                                "s3:PutBucketPolicy",
                                "s3:DeleteBucketPolicy",
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListMultipartUploadParts",
                                "s3:AbortMultipartUpload",
                                "s3:PutBucketAcl",
                                "s3:GetBucketAcl",
                                "s3:PutBucketTagging",
                                "s3:GetBucketTagging",
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

    # pylint: disable=too-many-arguments
    def __create_ec2_resources(self, vpc: ec2.Vpc, s3_policy: iam.ManagedPolicy):
        """
        Create the task in Fargate to run the Portal.
        """

        # Create default EC2 security group
        self.security_group = ec2.SecurityGroup(
            self,
            "PortalEc2SecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )
        self.security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(22))
        self.security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(443))
        self.security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(80))
        self.security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))
        self.security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), ec2.Port.tcp(8000))

        # What is this for?
        self.ec2_default_role = iam.Role(
            self,
            "PortalEc2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="Default Portal EC2 Role with S3 access",
        )
        self.ec2_default_role.add_managed_policy(s3_policy)
        self.ec2_default_instance_profile = iam.CfnInstanceProfile(
            self,
            "PortalEc2InstanceProfile",
            roles=[self.ec2_default_role.role_name],
        )

    # pylint: enable=too-many-arguments

    def __build_hosted_zone(self, domain_name):
        """
        This method creates a CDK route53 construct from a domain lookup under the
        assumption it already exists.
        """
        self.hosted_zone = route53.PublicHostedZone.from_lookup(
            self, "PortalHostedZone", domain_name=domain_name
        )
        if self.hosted_zone.is_resource(self):
            self.hosted_zone = route53.PublicHostedZone(
                self, "PortalHostedZone", zone_name=domain_name
            )

    def __build_route53_settings(self, full_record_name, record_name):
        """
        This method will configure the Route53 settings for daskhub.  These settings
        will be subsequently updated during the EKSCTL portions of the deployment.  It's safe
        to run this deployment from a live system.
        """

        ttl = Duration.seconds(300)
        domain_name = "0.0.0.0"

        record = find_route53_record_by_type_and_name(
            self.hosted_zone.hosted_zone_id, "CNAME", full_record_name
        )
        if record is not None:
            print(f"Route53 record set already exists for {full_record_name}")
            ttl = Duration.seconds(record["TTL"])
            domain_name = record["ResourceRecords"][0]["Value"]
            print(f" Using ttl={ttl.to_seconds()}, domain_name={domain_name}")

        cname_record = route53.CnameRecord(
            self,
            "CnameRecord",
            record_name=record_name,
            zone=self.hosted_zone,
            ttl=ttl,
            delete_existing=True,
            domain_name=domain_name,
            comment="Initial provisioning from CDK, updated via external-dns.",
        )
        cname_record.apply_removal_policy(RemovalPolicy.DESTROY)
