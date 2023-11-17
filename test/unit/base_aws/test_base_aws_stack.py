import inspect
import json
from unittest import TestCase

import aws_cdk as cdk
from aws_cdk.assertions import Template

from base_aws.base_aws_stack import BaseAwsStack
from utils import create_dumpfile


class TestBaseAwsStack(TestCase):
    # Additional tests to consider:
    # existing vpc / default vpc
    # creating the shared s3 bucket
    # creating the S3 management policy

    def test_synthesis_new_vpc(self):
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
            test_class=self.__class__.__name__,
            test_name=inspect.currentframe().f_code.co_name,
            data=json.dumps(template.to_json(), indent=2),
        )

        # Should have 1 VPC with 4 subnets and a single NAT gateway
        template.resource_count_is("AWS::EC2::VPC", 1)
        template.resource_count_is("AWS::EC2::NatGateway", 1)
        template.resource_count_is("AWS::EC2::Subnet", 4)
