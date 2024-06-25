"""
CDK Stack responsible for defining the AWS authorization infrastructure required
for a HelioCloud instance.
"""

from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    custom_resources as resources,
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
        self.__domain_prefix = auth.get("domain_prefix", "")
        deletion_protection = bool(auth.get("deletion_protection", "False"))
        removal_policy = RemovalPolicy[auth.get("removal_policy", "RETAIN")]

        email = None if not base_identity else base_identity.email

        # Create an AWS Cognito User Pool using some sensible defaults
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

        # Provide a domain prefix for the public URLS that will be created
        # on instantiation of this Cognito user pool
        self.userpool.add_domain(
            "CognitoDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=self.__domain_prefix),
        )

        # Set the logo and css (only using css workaround - limitation with cdk prevents
        # uploading images) for all HelioCloud Cognito auth screens
        with open("base_auth/static/style.css", encoding="UTF-8") as f:
            css = f.read()

        # No ImageFile parameter is used as the AWS SDK SetUICustomization funciton for all versions
        # requires reading an array of base8 integers for the image instead of something that would
        # not go past the string size limit on the generated CDK template file.
        # See: https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/client/cognito-identity-provider/command/SetUICustomizationCommand/
        custom = resources.AwsCustomResource(
            self,
            id="UserPoolHostedUICustomResource",
            on_create=resources.AwsSdkCall(
                service="@aws-sdk/client-cognito-identity-provider",
                action="SetUICustomizationCommand",
                parameters={
                    "ClientId": "ALL",
                    "CSS": css,
                    "UserPoolId": self.userpool.user_pool_id,
                },
                physical_resource_id=resources.PhysicalResourceId.of("id"),
            ),
            install_latest_aws_sdk=True,
            policy=resources.AwsCustomResourcePolicy.from_sdk_calls(
                resources=resources.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )
        custom.node.add_dependency(self.userpool)

    @property
    def domain_prefix(self):
        """
        Prefix for the application domain
        """
        return self.__domain_prefix
