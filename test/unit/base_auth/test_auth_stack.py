import unittest
from unittest.mock import patch

from base_auth.auth_stack import AuthStack


class TestAuthStack(unittest.TestCase):
    def setUp(self):
        self.cfg = {"auth": {"domain_prefix": "sample-domain-prefix"}}
        self.scope = None

        self.construct_id = "constructid"

    @patch("base_auth.identity_stack.IdentityStack")
    @patch("aws_cdk.aws_cognito.UserPool.add_domain")
    @patch("aws_cdk.aws_cognito.UserPool")
    @patch("aws_cdk.aws_cognito.UserPool.__init__")
    def test_constructor_config__default(
        self,
        cognito_user_pool_package,
        cognito_user_pool,
        cognito_user_pool_add_domain,
        base_identity,
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

    @patch("aws_cdk.aws_cognito.UserPool")
    def test_constructor_config__no_identity(
        self,
        cognito_user_pool,
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
