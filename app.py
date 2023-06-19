#!/usr/bin/env python3
import os
import aws_cdk as cdk
import yaml

from constructs import Construct

from base_auth.authorization_stack import AuthStack
from base_aws.base_aws_stack import BaseAwsStack
from registry.registry_stack import RegistryStack
from portal.portal_stack import PortalStack
from daskhub.daskhub_stack import DaskhubStack


class MyHelioCloud(Construct):
    """
    AWS CDK Construct for instantiating a HelioCloud.  This construct will resolve out the specific
    Stacks and their deployment configurations.
    """

    def __init__(self, scope: Construct, id: str, *, prod=False):
        super().__init__(scope, id)

        # Identity of this HelioCloud instance
        self.__id = id

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
        # Get the instance for this instance
        # First load the default instance
        configuration = dict()
        with open("instance/default.yaml", "r") as default_config_file:
            configuration = yaml.safe_load(default_config_file)

        with open("instance/" + self.__id + ".yaml") as instance_config_file:
            configuration.update(yaml.safe_load(instance_config_file))

        self.__config = configuration

    def __build_heliocloud(self):
        """
        Builds the HelioCloud instance.
        """
        # First, need the foundation
        base_stack = BaseAwsStack(self,
                                  "Base",
                                  description="Foundational AWS resources for a HelioCloud instance.",
                                  config=self.__config,
                                  env=self.__env)
        cdk.Tags.of(base_stack).add("Product", "heliocloud-base")

        # Next, determine if the Auth module is needed
        enabled_modules = self.__config.get("enabled")
        if enabled_modules.get("daskhub") or enabled_modules.get("portal"):
            # We need the services of an AuthStack
            auth_stack = AuthStack(self,
                                   "Auth",
                                   description="End-user authentication and authorization for a HelioCloud instance.",
                                   config=self.__config,
                                   env=self.__env)
            auth_stack.add_dependency(base_stack)
            cdk.Tags.of(auth_stack).add("Product", "heliocloud-auth")

            # Should the User Portal module be deployed
            if enabled_modules.get("portal", False):
                portal_stack = PortalStack(self,
                                           "Portal",
                                           description="User Portal module for a HelioCloud instance.",
                                           config=self.__config,
                                           env=self.__env,
                                           base_auth=auth_stack)
                portal_stack.add_dependency(auth_stack)
                cdk.Tags.of(portal_stack).add("Product", "heliocloud-portal")

            # Should Daskhub be deployed
            if enabled_modules.get("daskhub", False):
                daskhub_stack = DaskhubStack(self,
                                             "Daskhub",
                                             description="Daskhub for a HelioCloud instance.",
                                             config=self.__config,
                                             base_aws=base_stack,
                                             base_auth=auth_stack,
                                             env=self.__env)
                daskhub_stack.add_dependency(base_stack)
                daskhub_stack.add_dependency(auth_stack)
                cdk.Tags.of(daskhub_stack).add("Product", "heliocloud-dashboard")

        # Deploy the registry module
        if enabled_modules.get("registry", False):
            registry_stack = RegistryStack(self, "Registry",
                                           description="HelioCloud data set management.",
                                           config=self.__config,
                                           env=self.__env,
                                           base_aws_stack=base_stack)
            registry_stack.add_dependency(base_stack)
            cdk.Tags.of(registry_stack).add("Product", "heliocloud-registry")


def get_instance(app: cdk.App) -> (str, dict):
    """
    Get the name for this HelioCloud instance.
    """
    instance = app.node.try_get_context("instance")
    if instance is None:
        raise Exception("No instance specified. Re-run and provide an instance name value -c instance=<instance>.")
    return str(instance)


# Build the HelioCloud
app = cdk.App()
cdk.Tags.of(app).add("Project", "heliocloud")
MyHelioCloud(app, id=get_instance(app))

app.synth()
