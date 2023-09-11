import unittest
from unittest.mock import patch, MagicMock

from base_auth.identity_stack import IdentityStack


class TestIdentityStack(unittest.TestCase):
    # EmailIdentityProps
    @patch("aws_cdk.aws_cognito.UserPoolEmail.with_ses")
    @patch("aws_cdk.aws_ses.Identity")
    @patch("aws_cdk.aws_ses.Identity.public_hosted_zone")
    @patch("aws_cdk.aws_ses.EmailIdentity")
    @patch("aws_cdk.aws_route53")
    @patch("aws_cdk.aws_route53.__init__")
    @patch("aws_cdk.aws_route53.PublicHostedZone.from_lookup")
    @patch("aws_cdk.aws_route53.IPublicHostedZone.__init__")
    @patch("aws_cdk.aws_route53.CnameRecord")
    def test_constructor_config__default(
        self,
        route53_cname_record,
        ipublic_hosted_zone,
        route53_public_hosted_zone,
        route53_package,
        route53,
        ses_email_identity,
        ses_identity_public_hosted_zone,
        ses_identity,
        cognito_user_pool_email,
    ) -> None:
        """
        This test checks verifies the resulting configuration with the default settings.
        """

        domain = "aplscicloud.org"
        user = "test_user"
        from_name = "Test User"

        cfg = {
            "portal": {
                "domain_url": domain,
            },
            "email": {"use_custom_email_domain": True, "user": user, "from_name": from_name},
        }

        scope = None
        construct_id = "constructid"
        i_s = IdentityStack(scope, construct_id, cfg)

        # Verify that resources were called correctly
        # route53
        self.assertEqual(route53_public_hosted_zone.call_count, 1)
        self.assertEqual(route53_public_hosted_zone.call_args[0][0], i_s)
        self.assertEqual(route53_public_hosted_zone.call_args[0][1], "HostedZone")
        self.assertEqual(route53_public_hosted_zone.call_args[1]["domain_name"], domain)

        # ses
        # self.assertEqual(ses_email_identity.call_count, 1)
        # self.assertEqual(ses_email_identity.call_args[0][0], i_s)
        # self.assertEqual(ses_email_identity.call_args[0][1], "Identity")

        # self.assertEqual(ses_identity_public_hosted_zone.call_count, 1)
        # need to check public hosted zone arg

        # cognito
        self.assertEqual(cognito_user_pool_email.call_count, 1)
        self.assertEqual(cognito_user_pool_email.call_args[1]["from_email"], f"{user}@{domain}")
        self.assertEqual(cognito_user_pool_email.call_args[1]["from_name"], from_name)
        self.assertEqual(cognito_user_pool_email.call_args[1]["ses_verified_domain"], domain)
