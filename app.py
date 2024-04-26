"""
CDK script for deploying a HelioCloud instance to AWS
"""

# !/usr/bin/env python3
import os
import sys

import aws_cdk as cdk

from constructs import Construct

from app_config import load_configs
from base_auth.identity_stack import IdentityStack
from base_auth.auth_stack import AuthStack
from base_aws.base_aws_stack import BaseAwsStack
from registry.registry_stack import RegistryStack
from portal.portal_stack import PortalStack
from daskhub.daskhub_stack import DaskhubStack


class MyHelioCloud(Construct):
    """
    AWS CDK Construct for instantiating a HelioCloud.  This construct will resolve out the specific
    Stacks and their deployment configurations.
    """

    def __init__(self, scope: Construct, heliocloud_id: str):
        """
        Initialize a HelioCloud instance
        :param scope:
        :param heliocloud_id: identifier(name) to use for this instance of a HelioCloud
        """
        super().__init__(scope, heliocloud_id)

        # Identity of this HelioCloud instance
        self.__heliocloud_id = heliocloud_id

        # Get configuration details
        self.__config = None
        self.__get_config()

        # Get AWS env details
        self.__env = None
        self.__get_aws_env()

        # Build it
        self.__build_heliocloud()

    def __get_aws_env(self):
        """
        Get the AWS Account & Region to deploy into
        """
        # First, check the config
        account = str(self.__config.get("env").get("account", None))
        region = self.__config.get("env").get("region", None)
        if (region is not None) and (account is not None):
            print(f"Using instance configured AWS account {account}, region {region}.")
        else:
            # if nothing in the config, resolve from the environment
            account = os.environ["CDK_DEFAULT_ACCOUNT"]
            region = os.environ["CDK_DEFAULT_REGION"]
            print(f"Using AWS CLI provided AWS account {account}, region {region}.")

        self.__env = cdk.Environment(account=account, region=region)

    def __get_config(self):
        """
        Get the config for this HelioCloud instance.
        """
        self.__config = load_configs(hc_id=self.__heliocloud_id)

    def __build_heliocloud(self):
        """
        Builds the HelioCloud instance.
        """
        # First, need the foundation
        base_stack = BaseAwsStack(
            self,
            "Base",
            description="Foundational AWS resources for a HelioCloud instance.",
            config=self.__config,
            env=self.__env,
        )
        cdk.Tags.of(base_stack).add("Product", "heliocloud-base")

        # Next, determine if the Auth module is needed
        enabled_modules = self.__config.get("enabled")
        if enabled_modules.get("daskhub") or enabled_modules.get("portal"):
            identity_stack = None

            use_custom_email_domain = self.__config["email"]["use_custom_email_domain"]

            if use_custom_email_domain:
                identity_stack = IdentityStack(
                    self,
                    "Identity",
                    description="Optional custom email domain identity for a HelioCloud instance.",
                    config=self.__config,
                    env=self.__env,
                )

                cdk.Tags.of(identity_stack).add("Product", "heliocloud-identity")

            # We need the services of an AuthStack
            auth_stack = AuthStack(
                self,
                "Auth",
                description="End-user authentication and authorization for a HelioCloud instance.",
                config=self.__config,
                env=self.__env,
                base_identity=identity_stack,
            )
            auth_stack.add_dependency(base_stack)
            if use_custom_email_domain:
                auth_stack.add_dependency(identity_stack)
            cdk.Tags.of(auth_stack).add("Product", "heliocloud-auth")

            # Should the User Portal module be deployed
            if enabled_modules.get("portal", False):
                portal_stack = PortalStack(
                    self,
                    "Portal",
                    description="User Portal module for a HelioCloud instance.",
                    config=self.__config.get("portal"),
                    auth_stack=auth_stack,
                    aws_stack=base_stack,
                    env=self.__env,
                )
                portal_stack.add_dependency(auth_stack)
                cdk.Tags.of(portal_stack).add("Product", "heliocloud-portal")

            # Should Daskhub be deployed
            if enabled_modules.get("daskhub", False):
                daskhub_stack = DaskhubStack(
                    self,
                    "Daskhub",
                    description="Daskhub for a HelioCloud instance.",
                    config=self.__config,
                    base_aws=base_stack,
                    base_auth=auth_stack,
                    env=self.__env,
                )
                daskhub_stack.add_dependency(base_stack)
                daskhub_stack.add_dependency(auth_stack)
                cdk.Tags.of(daskhub_stack).add("Product", "heliocloud-daskhub-admin")

        # Deploy the registry module
        if enabled_modules.get("registry", False):
            registry_stack = RegistryStack(
                self,
                "Registry",
                description="HelioCloud data set management.",
                config=self.__config,
                env=self.__env,
                base_aws_stack=base_stack,
            )
            registry_stack.add_dependency(base_stack)
            cdk.Tags.of(registry_stack).add("Product", "heliocloud-registry")


def get_instance(cdk_app: cdk.App) -> str:
    """
    Get the name to use for this HelioCloud instance from the CDK app context
    :param cdk_app: CDK app context
    :return: name to use
    """
    instance = cdk_app.node.try_get_context("instance")
    if instance is None:
        sys.exit(
            "No instance specified. Re-run and provide an instance name value -c "
            "instance=<instance>"
        )
    return str(instance)


# Build the HelioCloud
app = cdk.App()
cdk.Tags.of(app).add("Project", "heliocloud")
MyHelioCloud(app, heliocloud_id=get_instance(app))

app.synth()
