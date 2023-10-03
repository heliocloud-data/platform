"""
CDK Stack responsible for creating and verifying an SES domain identity.
"""

from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    aws_ses as ses,
    aws_route53 as route53,
)
from constructs import Construct


class IdentityStack(Stack):
    """
    Stack for creating and verifying an SES identity for the current HelioCloud domain.
    Optional stack if the deployment does not require a custom domain for egress email traffic."
    """

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        domain_url = config["portal"]["domain_url"]
        user = config["email"]["user"]
        from_name = config["email"]["from_name"]

        hosted_zone = route53.PublicHostedZone.from_lookup(
            self, "HostedZone", domain_name=domain_url
        )
        ses.EmailIdentity(
            self,
            "Identity",
            identity=ses.Identity.public_hosted_zone(hosted_zone),
        )
        self.email = cognito.UserPoolEmail.with_ses(
            from_email=f"{user}@{domain_url}",
            from_name=from_name,
            ses_verified_domain=domain_url,
        )
