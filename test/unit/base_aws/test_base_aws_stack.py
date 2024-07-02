"""
Tests for BaseAwsStack
"""
import json

import aws_cdk as cdk
from aws_cdk.assertions import Template
from utils import create_dumpfile

from base_aws.base_aws_stack import BaseAwsStack


def test_synthesis_new_vpc():
    """
    Test that the BaseAwsStack results in a CloudFormation template synthesized
    to contain a new VPC, nat gateway and four subnets
    """
    app = cdk.App()

    # Environment
    env = cdk.Environment(region="us-east1", account="unit-test")
    cfg = {
        "vpc": {"type": "new"},
        "userSharedBucket": {},
        "email": {"user": "no-reply", "from_name": "APL HelioCloud"},
        "registry": {"datasetBucketNames": ["bucket1"]},
    }

    # Stack dependencies
    aws_stack = BaseAwsStack(app, "Base-Portal-Test", description="", config=cfg, env=env)

    # Generate the template and run assertions against it
    template = Template.from_stack(aws_stack)
    create_dumpfile(
        test_class="test_base_aws_stack",
        test_name=test_synthesis_new_vpc.__name__,
        data=json.dumps(template.to_json(), indent=2),
    )

    # Should have 1 VPC with 4 subnets and a single NAT gateway
    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::EC2::NatGateway", 1)
    template.resource_count_is("AWS::EC2::Subnet", 4)


## TODO: Additional tests to consider
# - existing vpc/default vpc
# - creating the shared S3 bucket
# - creating the S3 management policy
