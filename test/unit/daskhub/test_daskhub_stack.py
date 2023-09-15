from aws_cdk import Duration
import yaml

import pytest
import unittest
from unittest.mock import patch, MagicMock

from app_config import load_configs
from daskhub.daskhub_stack import DaskhubStack

from utils import which


class TestDaskhubStack(unittest.TestCase):
    DEFAULT_KEY_COUNT = 10
    """
    Various tests for parsing configuration files.
    """

    def test_method_load_configurations_OK_default(self):
        hc_cfg = load_configs("test/unit/resources/test_daskhub_stack/instance", "default")

        cfg = DaskhubStack.load_configurations(hc_cfg)
        print(cfg)

        # Verify that some elements are populated in the configuration
        # the
        self.assertEqual(TestDaskhubStack.DEFAULT_KEY_COUNT, len(cfg))

        # The contents should exactly match the 'defaults'
        default_cfg = None
        with open("daskhub/default-constants.yaml", "r") as stream:
            default_cfg = yaml.safe_load(stream)

        self.assertEqual(len(default_cfg), len(cfg))
        for key, value in default_cfg.items():
            self.assertEqual(default_cfg[key], cfg[key])

    def test_method_load_configurations_OK_override_one(self):
        hc_cfg = load_configs("test/unit/resources/test_daskhub_stack/instance", "override_one")

        cfg = DaskhubStack.load_configurations(hc_cfg)
        print(cfg)

        # Verify that some elements are populated in the configuration
        # the
        self.assertEqual(TestDaskhubStack.DEFAULT_KEY_COUNT, len(cfg))
        self.assertEqual("ludicolo.org", cfg["ROUTE53_HOSTED_ZONE"])

        # The contents should exactly match the 'defaults'
        default_cfg = None
        with open("daskhub/default-constants.yaml", "r") as stream:
            default_cfg = yaml.safe_load(stream)

        self.assertEqual(len(default_cfg), len(cfg))
        for key, value in default_cfg.items():
            # Skip over key that's set in the file.
            if key == "ROUTE53_HOSTED_ZONE":
                continue
            self.assertEqual(default_cfg[key], cfg[key])

    def test_method_load_configurations_OK_override_all_and_add_one(self):
        hc_cfg = load_configs(
            "test/unit/resources/test_daskhub_stack/instance", "override_all_and_add_one"
        )

        cfg = DaskhubStack.load_configurations(hc_cfg)
        print(cfg)

        # Verify that some elements are populated in the configuration
        # the
        self.assertEqual(TestDaskhubStack.DEFAULT_KEY_COUNT + 1, len(cfg))
        self.assertEqual("ludicolo.org", cfg["ROUTE53_HOSTED_ZONE"])
        self.assertEqual("daskhub-tapubulu", cfg["ROUTE53_DASKHUB_PREFIX"])
        self.assertEqual("tapufini", cfg["KUBERNETES_NAMESPACE"])
        self.assertEqual("eks-alola", cfg["EKS_NAME"])
        self.assertEqual("ketchap1", cfg["DASKHUB_ADMIN_USER"])
        self.assertEqual("ash.ketchum@jhuapl.edu", cfg["ADMIN_USER_EMAIL"])
        self.assertEqual("public.ecr.aws/a/tapukoko-notebook", cfg["GENERIC_DOCKER_LOCATION"])
        self.assertEqual("151", cfg["GENERIC_DOCKER_VERSION"])
        self.assertEqual("public.ecr.aws/b/tapulele-ml-notebook", cfg["ML_DOCKER_LOCATION"])
        self.assertEqual("252", cfg["ML_DOCKER_VERSION"])
        self.assertEqual("707", cfg["ANOTHER_KLEFKI"])

    def test_method_generate_app_config_from_template_OK_override_all_and_add_one(self):
        hc_cfg = load_configs(
            "test/unit/resources/test_daskhub_stack/instance", "override_all_and_add_one"
        )

        # Load the configurations
        cfg = DaskhubStack.load_configurations(hc_cfg)

        dest_file = "temp/test_daskhub_stack/override_all_and_add_one-actual.txt"
        DaskhubStack.generate_app_config_from_template(daskhub_config=cfg, dest_file=dest_file)

        with open(dest_file, encoding="UTF-8") as file:
            actual_lines = file.read()

        with open(
            "test/unit/resources/test_daskhub_stack/override_all_and_add_one-expected.txt",
            encoding="UTF-8",
        ) as file:
            expected_lines = file.read()

        # Verify they are exactly the same
        self.assertEqual(expected_lines, actual_lines)

    @pytest.mark.skipif(which("node") is None, reason="node not installed")
    @patch("base_aws.base_aws_stack.BaseAwsStack")
    @patch("base_auth.authorization_stack.AuthStack")
    @patch("aws_cdk.aws_ec2.Instance")
    @patch("aws_cdk.aws_ec2.Instance.__init__")
    @patch("aws_cdk.aws_ec2.InitFile.from_existing_asset")
    @patch("aws_cdk.aws_ec2.CloudFormationInit.from_elements")
    @patch("aws_cdk.aws_efs.FileSystem")
    @patch("aws_cdk.aws_efs.FileSystem.__init__")
    @patch("aws_cdk.aws_route53")
    @patch("aws_cdk.aws_route53.__init__")
    @patch("aws_cdk.aws_route53.PublicHostedZone")
    @patch("aws_cdk.aws_route53.CnameRecord")
    @patch("aws_cdk.CfnOutput")
    @patch("aws_cdk.CfnOutput.__init__")
    @patch("aws_cdk.aws_s3_assets.Asset")
    @patch("aws_cdk.aws_s3_assets.Asset.__init__")
    def test_constructor__default(
        self,
        s3_assets_constructor,
        s3_assets_output,
        cfn_output_constructor,
        cfn_output,
        route53_cname_record,
        route53_public_hosted_zone,
        route53_package_constructor,
        route53_package,
        efs_instance_constructor,
        efs_instance,
        ec2_cloud_formation_init_from_elements_method,
        ec2_init_file_from_existing_asset_method,
        ec2_instance_constructor,
        ec2_instance,
        base_auth,
        base_aws_stack,
    ):
        hc_cfg = load_configs("test/unit/resources/test_daskhub_stack/instance", "default")

        scope = None
        construct_id = "constructid"
        rs = DaskhubStack(scope, construct_id, hc_cfg, base_aws_stack, base_auth)

        self.assertEqual(ec2_instance.call_count, 1)

        # Verify the EFS instance was called correctly.
        self.assertEqual(efs_instance.call_count, 1)
        self.assertEqual(efs_instance.call_args[0][0], rs)
        self.assertEqual(efs_instance.call_args[0][1], "DaskhubEFS")
        self.assertEqual(efs_instance.call_args[1]["vpc"], base_aws_stack.heliocloud_vpc)
        self.assertEqual(efs_instance.call_args[1]["encrypted"], True)
        self.assertEqual(efs_instance.call_args[1]["enable_automatic_backups"], True)

        # Verify the CloudFormation Outputs were called correctly.
        self.assertEqual(cfn_output.call_count, 9)
        idx = 0
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "Instance ID")

        idx = idx + 1
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "ASGArn")

        idx = idx + 1
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "KMSArn")
        self.assertEqual(cfn_output.call_args_list[idx][1]["value"], base_aws_stack.kms.key_arn)

        idx = idx + 1
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "CustomS3Arn")
        self.assertEqual(
            cfn_output.call_args_list[idx][1]["value"],
            base_aws_stack.s3_managed_policy.managed_policy_arn,
        )

        idx = idx + 1
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "AdminRoleArn")

        idx = idx + 1
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "EFSId")

        idx = idx + 1
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "CognitoClientId")
        self.assertEqual(
            cfn_output.call_args_list[idx][1]["value"],
            base_auth.userpool.add_client().user_pool_client_id,
        )

        idx = idx + 1
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "CognitoDomainPrefix")
        self.assertEqual(cfn_output.call_args_list[idx][1]["value"], "apl-helio")

        idx = idx + 1
        self.assertEqual(cfn_output.call_args_list[idx][0][0], rs)
        self.assertEqual(cfn_output.call_args_list[idx][0][1], "CognitoUserPoolId")
        self.assertEqual(
            cfn_output.call_args_list[idx][1]["value"], base_auth.userpool.user_pool_id
        )

        self.assertEqual(route53_cname_record.call_count, 1)
        self.assertEqual(route53_cname_record.call_args_list[0][0][0], rs)
        self.assertEqual(route53_cname_record.call_args_list[0][0][1], "CnameRecord")
        self.assertEqual(route53_cname_record.call_args_list[0][1]["domain_name"], "0.0.0.0")
        self.assertEqual(
            route53_cname_record.call_args_list[0][1]["ttl"].to_string(),
            Duration.seconds(300).to_string(),
        )
        self.assertEqual(
            route53_cname_record.call_args_list[0][1]["comment"],
            "Initial provisioning from CDK, overridded by EKSCTL deployment.",
        )
