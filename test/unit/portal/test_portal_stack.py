"""
Tests for the PortalStack
"""

import inspect
import json

import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from utils import create_dumpfile

from base_auth.auth_stack import AuthStack
from base_auth.identity_stack import IdentityStack
from base_aws.base_aws_stack import BaseAwsStack
from portal.portal_stack import PortalStack


def test_portal_stack():
    app = cdk.App()

    # Environment
    env = cdk.Environment(region="us-east1", account="unit-test")
    cfg = {
        "vpc": {"type": "new"},
        "userSharedBucket": {},
        "email": {"user": "no-reply", "from_name": "APL HelioCloud"},
        "auth": {"domain_prefix": "helio"},
        "portal": {
            "domain_record": "portal",
            "domain_url": "hctest.org",
            "domain_certificate_arn": "arn:aws:acm:us-east-1:123456789012:certificate"
            "/abcdefg01-a0b0-c0f0-1mb09mf01fp1",
            "pip_timeout": 100,
        },
        "daskhub": {
            "global": {
                "domain_url": "hctest.org",
                "domain_certificate_arn": "arn:aws:acm:us-east-1:123456789012:certificate"
                "/abcdefg01-a0b0-c0f0-1mb09mf01fp1",
            },
            "eksctl": {"metadata": {"name": "eks-helio", "region": "us-east-1"}},
            "daskhub": {"domain_record": "daskhub"},
        },
    }

    # Stack dependencies
    aws_stack = BaseAwsStack(app, "Base-Portal-Test", description="", config=cfg, env=env)
    id_stack = IdentityStack(app, "Id-Portal-Test", description="", config=cfg, env=env)
    auth_stack = AuthStack(
        app, "Auth-Portal-Test", description="", config=cfg, base_identity=id_stack, env=env
    )

    # Create a portal_stack and assert on its contents
    portal_stack = PortalStack(
        app,
        "Portal-Test",
        description="",
        config=cfg["portal"],
        aws_stack=aws_stack,
        auth_stack=auth_stack,
        env=env,
    )

    # Generate the template and dump a copy of it for inspection if needed
    template = Template.from_stack(portal_stack)
    create_dumpfile(
        test_class="test_portal_stack",
        test_name=inspect.currentframe().f_code.co_name,
        data=json.dumps(template.to_json(), indent=2),
    )
