"""
This file contains the CDK stack for deploying Daskhub.
"""

from aws_cdk import (
    Stack,
    aws_route53 as route53,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    RemovalPolicy,
)
from constructs import Construct


class DaskhubMetricsStack(Stack):
    """
    CDK stack for installing DaskHub for a HelioCloud instance
    """

    # fmt: off
    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
            self,
            scope: Construct,
            construct_id: str,
            config: dict,
            **kwargs,
    ) -> None:
        # fmt: on
        super().__init__(scope, construct_id, **kwargs)

        self.__daskhub_metrics_config = config['daskhub_metrics']


        self.__hosted_zone = route53.PublicHostedZone.from_lookup(
            self, "HostedZone", domain_name=self.__daskhub_metrics_config['domain_url']
        )

        elb_grafana = elbv2.NetworkLoadBalancer.from_lookup(self, id="ELB-Grafana", load_balancer_tags={
            'kubernetes.io/service-name': 'monitoring/grafana',
        })

        self.build_route53_settings(self.__hosted_zone, 'GrafanaCNameRecord', 'grafana_domain_prefix', elb_grafana.load_balancer_dns_name)

        elb_prometheus = elbv2.NetworkLoadBalancer.from_lookup(self, id="ELB-Prometheus", load_balancer_tags={
            'kubernetes.io/service-name': 'monitoring/prometheus-server',
        })
        self.build_route53_settings(self.__hosted_zone, 'PrometheusCNameRecord', 'prometheus_domain_prefix', elb_prometheus.load_balancer_dns_name)


    def build_route53_settings(self, hosted_zone, record_id, record_name_key, load_balancer_dns_name):
        """
        This method will configure the Route53 settings for daskhub.  These settings
        will be subsequently updated during the EKSCTL portions of the deployment.  It's safe
        to run this deployment from a live system.
        """
        cname_record = route53.CnameRecord(
            self,
            record_id,
            record_name=self.__daskhub_metrics_config[record_name_key],
            zone=hosted_zone,
            ttl=Duration.seconds(300),
            delete_existing=True,
            domain_name=load_balancer_dns_name,
            comment="Automatically created by CDK deployment DaskhubMetricsStack"
        )
        cname_record.apply_removal_policy(RemovalPolicy.DESTROY)
