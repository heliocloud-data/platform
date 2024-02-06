import inspect
import json
import yaml

import aws_cdk as cdk
from aws_cdk import Duration
from aws_cdk.assertions import Match, Template

import pytest
import unittest
from unittest.mock import patch, MagicMock
from base_aws.base_aws_stack import BaseAwsStack
from base_auth.auth_stack import AuthStack
from base_auth.identity_stack import IdentityStack

from app_config import load_configs
from daskhub.daskhub_stack import DaskhubStack
from utils import which, create_dumpfile


class TestDaskhubStack(unittest.TestCase):
    DEFAULT_KEY_COUNT = 11
    """
    Various tests for parsing configuration files.
    """

    def test_method_load_configurations_OK_default(self):
        hc_cfg = load_configs("test/unit/resources/test_daskhub_stack/instance", "default")

        cfg = DaskhubStack.load_configurations(hc_cfg)
        print(cfg)

        # Verify that some elements are populated in the configuration
        # the
        self.assertEqual(TestDaskhubStack.DEFAULT_KEY_COUNT, len(cfg))

        # The contents should exactly match the 'defaults'
        default_cfg = None
        with open("daskhub/default-constants.yaml", "r") as stream:
            default_cfg = yaml.safe_load(stream)

        self.assertEqual(len(default_cfg), len(cfg))
        for key, value in default_cfg.items():
            self.assertEqual(default_cfg[key], cfg[key])

    def test_method_load_configurations_OK_override_one(self):
        hc_cfg = load_configs("test/unit/resources/test_daskhub_stack/instance", "override_one")

        cfg = DaskhubStack.load_configurations(hc_cfg)
        print(cfg)

        # Verify that some elements are populated in the configuration
        # the
        self.assertEqual(TestDaskhubStack.DEFAULT_KEY_COUNT, len(cfg))
        self.assertEqual("ludicolo.org", cfg["ROUTE53_HOSTED_ZONE"])

        # The contents should exactly match the 'defaults'
        default_cfg = None
        with open("daskhub/default-constants.yaml", "r") as stream:
            default_cfg = yaml.safe_load(stream)

        self.assertEqual(len(default_cfg), len(cfg))
        for key, value in default_cfg.items():
            # Skip over key that's set in the file.
            if key == "ROUTE53_HOSTED_ZONE":
                continue
            self.assertEqual(default_cfg[key], cfg[key])

    def test_method_load_configurations_OK_override_all_and_add_one(self):
        hc_cfg = load_configs(
            "test/unit/resources/test_daskhub_stack/instance", "override_all_and_add_one"
        )

        cfg = DaskhubStack.load_configurations(hc_cfg)
        print(cfg)

        # Verify that some elements are populated in the configuration
        # the
        self.assertEqual(TestDaskhubStack.DEFAULT_KEY_COUNT + 1, len(cfg))
        self.assertEqual("ludicolo.org", cfg["ROUTE53_HOSTED_ZONE"])
        self.assertEqual("daskhub-tapubulu", cfg["ROUTE53_DASKHUB_PREFIX"])
        self.assertEqual("tapufini", cfg["KUBERNETES_NAMESPACE"])
        self.assertEqual("eks-alola", cfg["EKS_NAME"])
        self.assertEqual("ketchap1", cfg["DASKHUB_ADMIN_USER"])
        self.assertEqual("ash.ketchum@jhuapl.edu", cfg["ADMIN_USER_EMAIL"])
        self.assertEqual("public.ecr.aws/a/tapukoko-notebook", cfg["GENERIC_DOCKER_LOCATION"])
        self.assertEqual("151", cfg["GENERIC_DOCKER_VERSION"])
        self.assertEqual("public.ecr.aws/b/tapulele-ml-notebook", cfg["ML_DOCKER_LOCATION"])
        self.assertEqual("252", cfg["ML_DOCKER_VERSION"])
        self.assertEqual("707", cfg["ANOTHER_KLEFKI"])

    def test_method_generate_app_config_from_template_OK_override_all_and_add_one(self):
        hc_cfg = load_configs(
            "test/unit/resources/test_daskhub_stack/instance", "override_all_and_add_one"
        )

        # Load the configurations
        cfg = DaskhubStack.load_configurations(hc_cfg)

        dest_file = "temp/test_daskhub_stack/override_all_and_add_one-actual.txt"
        DaskhubStack.generate_app_config_from_template(daskhub_config=cfg, dest_file=dest_file)

        with open(dest_file, encoding="UTF-8") as file:
            actual_lines = file.read()

        with open(
            "test/unit/resources/test_daskhub_stack/override_all_and_add_one-expected.txt",
            encoding="UTF-8",
        ) as file:
            expected_lines = file.read()

        # Verify they are exactly the same
        self.assertEqual(expected_lines, actual_lines)

    @pytest.mark.skipif(which("node") is None, reason="node not installed")
    def test_constructor__default(self):
        # Environment
        app = cdk.App()
        env = cdk.Environment(region="us-east1", account="unit-test")
        hc_cfg = load_configs("test/unit/resources/test_daskhub_stack/instance", "default")

        # Create stacks
        base_aws_stack = BaseAwsStack(scope=app, construct_id="test-base", config=hc_cfg, env=env)
        identity_stack = IdentityStack(
            scope=app, construct_id="test-identity", config=hc_cfg, env=env
        )
        auth_stack = AuthStack(
            scope=app,
            construct_id="test-auth",
            config=hc_cfg,
            base_identity=identity_stack,
            env=env,
        )
        daskhub_stack = DaskhubStack(
            app, "test-daskhub", hc_cfg, base_aws_stack, auth_stack, env=env
        )

        # Generate & dump CloudFormation templates for daskhub & auth
        daskhub_template = Template.from_stack(daskhub_stack)
        create_dumpfile(
            test_class=self.__class__.__name__,
            test_name=inspect.currentframe().f_code.co_name + "-daskhub",
            data=json.dumps(daskhub_template.to_json(), indent=2),
        )
        # We need auth since the Daskhub stack attaches a Cognito user pool client
        auth_template = Template.from_stack(auth_stack)
        create_dumpfile(
            test_class=self.__class__.__name__,
            test_name=inspect.currentframe().f_code.co_name + "-auth",
            data=json.dumps(auth_template.to_json(), indent=2),
        )

        # Evaluate the CDK generated CloudFormation templates for Daskhub and Auth
        # to make sure the right resources have been declared by the Daskhub stack implementation

        # AWS EFS:  Check that the FS file system is created correctly
        daskhub_template.has_resource(
            "AWS::EFS::FileSystem",
            {
                "Properties": {
                    "Encrypted": True,
                    "BackupPolicy": {"Status": "ENABLED"},
                    "FileSystemTags": [{"Key": "Name", "Value": "test-daskhub/DaskhubEFS"}],
                },
                "DeletionPolicy": "Retain",
            },
        )
        daskhub_template.has_output("EFSId", props=Match.any_value())

        # AWS EC2:  Check that the bastion host for Daskhub was created, along with an
        # IAM policy for deployment
        daskhub_template.has_resource(
            "AWS::EC2::Instance",
            {
                "Properties": {
                    "InstanceType": "t2.micro",
                    "Tags": [{"Key": "Name", "Value": "test-daskhub/DaskhubInstance"}],
                    "UserData": Match.any_value(),
                }
            },
        )
        daskhub_template.has_resource(
            "AWS::IAM::Role",
            {
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Statement": Match.array_with(
                            [
                                {
                                    "Action": "sts:AssumeRole",
                                    "Effect": "Allow",
                                    "Principal": {"Service": "ec2.amazonaws.com"},
                                }
                            ]
                        )
                    }
                }
            },
        )
        daskhub_template.has_output("InstanceID", props=Match.any_value())
        daskhub_template.has_output("AdminRoleArn", props=Match.any_value())

        # AWS KMS:  Check for the KMS key being created and ARN available in the output
        daskhub_template.has_output("KMSArn", props=Match.any_value())
        daskhub_template.has_resource("AWS::KMS::Key", {"DeletionPolicy": "Delete"})

        # AWS IAM:  Checking for the autoscaler policy that will be used by Daskhub
        daskhub_template.has_resource(
            "AWS::IAM::ManagedPolicy",
            {
                "Properties": {
                    "PolicyDocument": {
                        "Statement": Match.array_with(
                            [
                                {
                                    "Action": Match.array_with(["autoscaling:SetDesiredCapacity"]),
                                    "Effect": "Allow",
                                    "Resource": "*",
                                }
                            ]
                        )
                    }
                }
            },
        )
        daskhub_template.has_output("ASGArn", props=Match.any_value())

        # AWS Route53:  Check for the Daskhub entries we expect
        daskhub_template.has_resource(
            "AWS::Route53::RecordSet",
            {
                "Properties": {
                    "Comment": "Initial provisioning from CDK, overridden by EKSCTL deployment.",
                    "Name": "daskhub.<REPLACE>.",
                    "ResourceRecords": Match.array_with(["0.0.0.0"]),
                },
                "UpdateReplacePolicy": "Delete",
            },
        )

        # AWS Cognito:  Checking that Daskhub has been registered as a user pool client
        # to the user pool created by the auth stack
        auth_template.has_resource(
            "AWS::Cognito::UserPoolClient",
            {
                "Properties": {
                    "CallbackURLs": Match.array_with(["https://example.com/hub/oauth_callback"]),
                    "LogoutURLs": Match.array_with(["https://example.com/logout"]),
                }
            },
        )
        daskhub_template.has_output("CognitoClientId", props=Match.any_value())
