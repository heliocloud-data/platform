import unittest
from unittest.mock import patch

from base_auth.auth_stack import AuthStack


class TestAuthStack(unittest.TestCase):
    def setUp(self):
        self.cfg = {"auth": {"domain_prefix": "sample-domain-prefix"}}
        self.scope = None

        self.construct_id = "constructid"

    @patch("aws_cdk.custom_resources.AwsCustomResource.node.add_dependency")
    @patch("aws_cdk.custom_resources.AwsCustomResource")
    @patch("aws_cdk.aws_cognito.CfnUserPoolUICustomizationAttachment")
    @patch("base_auth.identity_stack.IdentityStack")
    @patch("aws_cdk.aws_cognito.UserPool.user_pool_id")
    @patch("aws_cdk.aws_cognito.UserPool.add_domain")
    @patch("aws_cdk.aws_cognito.UserPool")
    @patch("aws_cdk.aws_cognito.UserPool.__init__")
    def test_constructor_config__default(
        self,
        cognito_user_pool_package,
        cognito_user_pool,
        cognito_user_pool_add_domain,
        user_pool_id,
        base_identity,
        cfn_user_pool_ui_customization_attachment,
        custom_resources,
        custom_resources_node_add_dependency,
    ) -> None:
        """
        This test checks verifies the resulting configuration with the default settings.
        """

        email = "nota@real.email"

        base_identity.email = email

        a_s = AuthStack(self.scope, self.construct_id, self.cfg, base_identity)

        self.assertEqual(cognito_user_pool.call_count, 1)
        self.assertEqual(cognito_user_pool.call_args[0][0], a_s)
        self.assertEqual(cognito_user_pool.call_args[0][1], "Pool")
        self.assertEqual(cognito_user_pool.call_args[1]["email"], email)

    @patch("aws_cdk.custom_resources.AwsCustomResource.node.add_dependency")
    @patch("aws_cdk.custom_resources.AwsCustomResource")
    @patch("aws_cdk.aws_cognito.CfnUserPoolUICustomizationAttachment")
    @patch("aws_cdk.aws_cognito.UserPool.user_pool_id")
    @patch("aws_cdk.aws_cognito.UserPool")
    def test_constructor_config__no_identity(
        self,
        cognito_user_pool,
        user_pool_id,
        cfn_user_pool_ui_customization_attachment,
        custom_resources,
        custom_resources_node_add_dependency,
    ) -> None:
        """
        This test checks verifies the resulting configuration without an Identity Stack.
        """

        base_identity = None

        a_s_no_email = AuthStack(self.scope, self.construct_id, self.cfg, base_identity)
        self.assertEqual(cognito_user_pool.call_count, 1)
        self.assertEqual(cognito_user_pool.call_args[0][0], a_s_no_email)
        self.assertEqual(cognito_user_pool.call_args[0][1], "Pool")
        self.assertEqual(cognito_user_pool.call_args[1]["email"], None)
