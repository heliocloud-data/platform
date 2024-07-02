"""
Tests for the AuthStack.
"""
import json
from unittest.mock import Mock

import pytest
from aws_cdk import aws_cognito
from aws_cdk.assertions import Template, Match
from utils import create_dumpfile

from base_auth.auth_stack import AuthStack
from base_auth.identity_stack import IdentityStack

DOMAIN_PREFIX = "sample-domain-prefix"
LOGO_URL = "http://heliocloud.org/static/img/logo_bin.png"


@pytest.fixture(scope="module")
def config():
    return {"auth": {"domain_prefix": DOMAIN_PREFIX}}


def test_auth_stack(config) -> None:
    """
    Tests the creation of a default AuthStock. Various CloudFormation template contents are checked
    - Cognito User Pool configuration
    - Use of the HelioCloud logo for branding the authentication experience
    """
    a_s_no_email = AuthStack(None, "constructid", config, None)
    template = Template.from_stack(a_s_no_email)
    create_dumpfile(
        test_class="test_auth_stack",
        test_name=test_auth_stack.__name__,
        data=json.dumps(template.to_json(), indent=2),
    )

    # Check that a user pool is being created with a couple of the settings specified in the stack
    # - email as the account recovery mechanism
    # - case-insensitive usernames
    # - delete protection enable
    # - retain the user pool on delete
    template.resource_count_is("AWS::Cognito::UserPool", 1)
    template.has_resource(
        type="AWS::Cognito::UserPool",
        props={
            "Properties": {
                "AccountRecoverySetting": {"RecoveryMechanisms": [{"Name": "verified_email"}]},
                "UsernameConfiguration": {"CaseSensitive": False},
                "DeletionProtection": "ACTIVE",
            },
            "DeletionPolicy": "Retain",
        },
    )

    # Check that the correct domain was assigned to the user pool
    template.resource_count_is(type="AWS::Cognito::UserPoolDomain", count=1)
    template.has_resource(
        type="AWS::Cognito::UserPoolDomain", props={"Properties": {"Domain": DOMAIN_PREFIX}}
    )

    # A Custom resource should also exist that serves to attach
    # the location of the heliocloud log to the CloudFormation stack for the Cognito
    # user pool to use in rendering the signup/login page
    template.resource_count_is(type="Custom::AWS", count=1)
    template.has_resource(
        type="Custom::AWS",
        props={
            "Properties": {
                "Create": {
                    "Fn::Join": Match.array_with(
                        [Match.array_with([Match.string_like_regexp(LOGO_URL)])]
                    )
                }
            }
        },
    )


def test_auth_stack_with_identity(config) -> None:
    """
    Checks an AuthStack instantiated with reference to an Identity Stack,
    the later providing an email identity to use in email correspondence with end-users
    going through the signup process.
    """

    base_identity = Mock(spec=IdentityStack)
    base_identity.email = aws_cognito.UserPoolEmail.with_ses(
        from_email="test-user@heliocloud.org",
        from_name="from_name",
        ses_verified_domain="heliocloud.org",
        ses_region="us-east-1",
    )

    auth_stack = AuthStack(None, "constructid", config, base_identity)
    template = Template.from_stack(auth_stack)
    create_dumpfile(
        test_class="test_auth_stack",
        test_name=test_auth_stack.__name__,
        data=json.dumps(template.to_json(), indent=2),
    )

    # Check that the Cognito User Pool is setup with the correct
    # email configuration as derived from the IdentityStack
    template.has_resource(
        type="AWS::Cognito::UserPool",
        props={
            "Properties": {"EmailConfiguration": {"From": "from_name <test-user@heliocloud.org>"}}
        },
    )
