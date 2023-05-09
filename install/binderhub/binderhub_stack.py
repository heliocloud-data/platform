from aws_cdk import (
    Stack,
)
from constructs import Construct


class BinderhubStack(Stack):
    """
    CDK stack for installing Binderhub for a HelioCloud instance
    """

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        raise Exception("Not implemented yet.")