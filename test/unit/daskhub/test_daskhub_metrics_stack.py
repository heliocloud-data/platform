from aws_cdk import Duration
from pprint import pprint

import pytest
import unittest
from unittest.mock import ANY, patch

from app_config import load_configs
from daskhub.daskhub_metrics_stack import DaskhubMetricsStack

from utils import which


class TestDaskhubMetricsStack(unittest.TestCase):
    @pytest.mark.skipif(which("node") is None, reason="node not installed")
    @patch("aws_cdk.aws_route53")
    @patch("aws_cdk.aws_route53.__init__")
    @patch("aws_cdk.aws_route53.PublicHostedZone")
    @patch("aws_cdk.aws_route53.CnameRecord")
    @patch("aws_cdk.aws_elasticloadbalancingv2")
    @patch("aws_cdk.aws_elasticloadbalancingv2.__init__")
    @patch("aws_cdk.aws_elasticloadbalancingv2.NetworkLoadBalancer")
    @patch("aws_cdk.aws_elasticloadbalancingv2.NetworkLoadBalancer.from_lookup")
    def test_constructor__default(
        self,
        elbv2_network_load_balancer_from_lookup_method,
        elbv2_network_load_balancer,
        elbv2_package_constructor,
        elbv2_package,
        route53_cname_record,
        route53_public_hosted_zone,
        route53_package_constructor,
        route53_package,
    ):
        hc_cfg = load_configs("test/unit/resources/test_daskhub_metrics_stack/instance", "default")

        scope = None
        construct_id = "constructid"
        rs = DaskhubMetricsStack(scope, construct_id, hc_cfg)

        elbv2_network_load_balancer.from_lookup.assert_called_with(
            rs,
            id="ELB-Prometheus",
            load_balancer_tags={
                "kubernetes.io/service-name": "monitoring/prometheus-server",
            },
        )

        self.assertEqual(route53_cname_record.call_count, 2)
        self.assertEqual(route53_cname_record.call_args_list[0][0][0], rs)
        self.assertEqual(route53_cname_record.call_args_list[0][0][1], "GrafanaCNameRecord")

        self.assertEqual(
            route53_cname_record.call_args_list[0][1]["ttl"].to_string(),
            Duration.seconds(300).to_string(),
        )
        self.assertEqual(
            route53_cname_record.call_args_list[0][1]["comment"],
            "Automatically created by CDK deployment DaskhubMetricsStack",
        )

        self.assertEqual(route53_cname_record.call_args_list[1][0][0], rs)
        self.assertEqual(route53_cname_record.call_args_list[1][0][1], "PrometheusCNameRecord")

        self.assertEqual(
            route53_cname_record.call_args_list[1][1]["ttl"].to_string(),
            Duration.seconds(300).to_string(),
        )
        self.assertEqual(
            route53_cname_record.call_args_list[1][1]["comment"],
            "Automatically created by CDK deployment DaskhubMetricsStack",
        )
