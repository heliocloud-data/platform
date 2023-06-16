import aws_cdk.custom_resources
import yaml
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    custom_resources as resources,
    aws_cognito as cognito,
)
from constructs import Construct


class PortalStack(Stack):
    """
    Stack to install HelioCloud user portal.
    """

    def __init__(self, scope: Construct, construct_id: str, config: dict, base_auth: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ##############################################
        # Authentication and Authorization (Cognito) #
        ##############################################
        # TODO make these configurable (with defaults), note changes to this 
        portal_client = base_auth.userpool.add_client("heliocloud-portal",
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
                                                              'https://example.com/login'],
                                                          logout_urls=['https://example.com/logout']),
                                                      supported_identity_providers=[
                                                          cognito.UserPoolClientIdentityProvider.COGNITO],
                                                      prevent_user_existence_errors=True)
