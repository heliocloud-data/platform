"""AWS commands via boto3."""

import boto3
import datetime
from config import region, user_pool_id, identity_pool_id
import json


def create_user_tag(username):
    return {'Name':'tag:Owner', 'Values': [username]}


def get_ec2_pricing(aws_session, instance_types):
    pricing_client = aws_session.client('pricing', region_name='us-east-1') # must be on us-east-1
    filters = [
                {"Field": "regionCode", "Value": 'us-east-1', "Type": "TERM_MATCH"},
                {"Field": "operatingSystem", "Value": "Linux", "Type": "TERM_MATCH"},
                {"Field": "tenancy", "Value": "Shared", "Type": "TERM_MATCH"},
                {"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"},
                {"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"},
            ]
    resp = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=filters
    )
    price_list = resp['PriceList']
    while "NextToken" in resp:
        resp = pricing_client.get_products(
            ServiceCode='AmazonEC2',
            Filters=filters,
            NextToken=resp['NextToken']
        )
        price_list.extend(resp['PriceList'])
    instance_out_dict = {it: {'cpu': 'None', 'memory': 'None', 'price': 'None'} for it in instance_types}
    price_list = [p for p in price_list if json.loads(p)['product']['attributes']['instanceType'] in instance_types]
    for r in price_list:
        resp_json = json.loads(r)
        rit = resp_json['product']['attributes']['instanceType']
        if rit in instance_out_dict.keys() and instance_out_dict[rit]['price'] is not None:
            od = resp_json['terms']['OnDemand']
            key1 = list(od.keys())[0]
            key2 = list(od[key1]['priceDimensions'].keys())[0]
            price_resp = od[key1]['priceDimensions'][key2]
            instance_out_dict[rit] = {'cpu': resp_json['product']['attributes']['vcpu'], 'memory': resp_json['product']['attributes']['memory'], 'price': "{:.2f}".format(float(price_resp['pricePerUnit']['USD']))}
    return instance_out_dict

def start_aws_session(id_token):
    identity_client = boto3.client('cognito-identity', region_name=region)
    identity_id = identity_client.get_id(IdentityPoolId=identity_pool_id,
                                         Logins={f'cognito-idp.{region}.amazonaws.com/{user_pool_id}': id_token})
    aws_cred = identity_client.get_credentials_for_identity(
        IdentityId=identity_id['IdentityId'],
        Logins={f'cognito-idp.{region}.amazonaws.com/{user_pool_id}': id_token},
    )['Credentials']
    aws_session = boto3.Session(aws_access_key_id=aws_cred['AccessKeyId'], aws_secret_access_key=aws_cred['SecretKey'], aws_session_token=aws_cred['SessionToken'])
    return aws_session

def get_weekly_overall_cost(aws_session, username):
    time_end = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    week_start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    overall_start = '2022-01-01'
    ce_client = aws_session.client('ce')
    week_resp = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': week_start,
            'End': time_end
        },
        Granularity="MONTHLY",
        Metrics=['UnblendedCost'],
        Filter= {'Tags':{'Key':'Owner', 'Values':[username]}}
    )
    week_cost = 0
    for r in week_resp['ResultsByTime']:
        week_cost += float(r['Total']['UnblendedCost']['Amount'])
    week_cost = round(week_cost,2)
    overall_resp = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': overall_start,
            'End': time_end
        },
        Granularity="MONTHLY",
        Metrics=['UnblendedCost'],
        Filter= {'Tags':{'Key':'Owner', 'Values':[username]}}
    )
    overall_cost = 0
    for r in overall_resp['ResultsByTime']:
        overall_cost += float(r['Total']['UnblendedCost']['Amount'])
    overall_cost = round(overall_cost,2)
    cost = {'week':week_cost, 'overall':overall_cost}
    return cost

