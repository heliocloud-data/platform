"""
CDK Stack responsible for defining the AWS authorization infrastructure required
for a HelioCloud instance.
"""

from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    RemovalPolicy,
)
from constructs import Construct


class AuthStack(Stack):
    """
    Stack for instantiating Authorization and Authentication services in AWS
    that are required by other HelioCloud components:  User dashboard, Daskhub,
    File Registration, etc"
    """

    def __init__(
        self, scope: Construct, construct_id: str, config: dict, base_identity: Stack, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        auth = config["auth"]
        domain_prefix = auth.get("domain_prefix", "")

        deletion_protection = bool(auth.get("deletion_protection", "False"))
        removal_policy = RemovalPolicy[auth.get("removal_policy", "RETAIN")]

        email = None if not base_identity else base_identity.email

        self.userpool = cognito.UserPool(
            self,
            "Pool",
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            sign_in_case_sensitive=False,
            deletion_protection=deletion_protection,
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True)
            ),
            removal_policy=removal_policy,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            self_sign_up_enabled=False,
            email=email,
        )
        self.userpool.add_domain(
            "CognitoDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix),
        )
