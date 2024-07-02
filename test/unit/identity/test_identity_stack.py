"""
Tests for the IdentityStack
"""
from aws_cdk.assertions import Template
import aws_cdk as cdk
from utils import create_dumpfile
import json

from base_auth.identity_stack import IdentityStack


def test_identity_stack() -> None:
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
    env = cdk.Environment(region="us-east1", account="unit-test")
    identity_stack = IdentityStack(None, "constructid", config=cfg, env=env)
    template = Template.from_stack(identity_stack)
    create_dumpfile(
        test_class="test_identity_stack",
        test_name=test_identity_stack.__name__,
        data=json.dumps(template.to_json(), indent=2),
    )

    # Zones should be referenced in the template
    # template.has_resource("AWS::Route53::HostedZone")
    template.has_resource("AWS::Route53::RecordSet", props={})

    # Confirm the correct email identity is in the template
    template.has_resource_properties("AWS::SES::EmailIdentity", props={"EmailIdentity": domain})
