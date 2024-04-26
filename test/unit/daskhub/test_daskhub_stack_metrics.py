import inspect
import json

import unittest
import pytest
from aws_cdk.assertions import Match, Template
import aws_cdk as cdk
from base_aws.base_aws_stack import BaseAwsStack
from base_auth.auth_stack import AuthStack
from base_auth.identity_stack import IdentityStack

from app_config import load_configs
from daskhub.daskhub_stack import DaskhubStack
from utils import which, create_dumpfile


class TestDaskhubStackMetrics(unittest.TestCase):
    """
    This test specifically checks that kubecost dependencies are met at the cdk level.
    """

    @pytest.mark.skipif(which("node") is None, reason="node not installed")
    def test_constructor_metrics__default(self):
        """
        Check cdk outputs with metrics enabled.
        """
        # Environment
        app = cdk.App()
        env = cdk.Environment(region="us-east1", account="unit-test")
        hc_cfg = load_configs("test/unit/resources/test_daskhub_stack/instance", "metrics_enabled")

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

        # AWS Cognito:  Checking that Daskhub has been registered as a user pool client
        # to the user pool created by the auth stack
        auth_template.resource_count_is("AWS::Cognito::UserPoolClient", 2)

        daskhub_template.has_output("CognitoClientIdKubeCost", props=Match.any_value())
