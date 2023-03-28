import aws_cdk.custom_resources
import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    RemovalPolicy,
)
from constructs import Construct


class AuthStack(Stack):
    """
    Stack for instantiating Authorization and Authentication services in AWS
    that are required by other HelioCloud components:  User dashboard, Daskhub, File Registration, etc"
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get the configuration file from the context
        config = self.node.try_get_context("config")
        with open(config, 'r') as file:
            configuration = yaml.safe_load(file)

        auth = configuration['auth']
        domain_prefix = auth.get('domain_prefix', '')


        # TODO: rethink removal policy Caution: removal policy set to destroy
        self.userpool = cognito.UserPool(self, "Pool",
                                    account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
                                    sign_in_case_sensitive=False,
                                    standard_attributes=cognito.StandardAttributes(
                                        email=cognito.StandardAttribute(required=True, mutable=True)),
                                    removal_policy=RemovalPolicy.DESTROY,
                                    auto_verify=cognito.AutoVerifiedAttrs(email=True))
        self.userpool.add_domain('CognitoDomain',
                            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix))

        # TODO move this into daskhub stack and make a copy and put in dashboard
        daskhub_client = self.userpool.add_client("heliocloud-daskhub",
                                             generate_secret=True,
                                             o_auth=cognito.OAuthSettings(
                                                 flows=cognito.OAuthFlows(
                                                     authorization_code_grant=True),
                                                 scopes=[cognito.OAuthScope.PHONE,
                                                         cognito.OAuthScope.EMAIL,
                                                         cognito.OAuthScope.OPENID,
                                                         cognito.OAuthScope.COGNITO_ADMIN,
                                                         cognito.OAuthScope.PROFILE],
                                                 callback_urls=[
                                                     'https://example.com/hub/oauth_callback'],
                                                 logout_urls=['https://example.com/logout']),
                                             supported_identity_providers=[
                                                 cognito.UserPoolClientIdentityProvider.COGNITO],
                                             prevent_user_existence_errors=True)
        self.daskhub_client_id = daskhub_client.user_pool_client_id
        self.daskhub_client_secret = daskhub_client.user_pool_client_secret

