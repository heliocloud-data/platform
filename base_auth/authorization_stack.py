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

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        auth = config['auth']
        domain_prefix = auth.get('domain_prefix', '')

        # TODO add ability to setup MFA
        self.userpool = cognito.UserPool(self,
                                         "Pool",
                                         account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
                                         sign_in_case_sensitive=False,
                                         standard_attributes=cognito.StandardAttributes(
                                             email=cognito.StandardAttribute(required=True, mutable=True)),
                                         removal_policy=RemovalPolicy.RETAIN,
                                         auto_verify=cognito.AutoVerifiedAttrs(email=True),
                                         self_sign_up_enabled=False)
        self.userpool.add_domain('CognitoDomain',
                                 cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix))