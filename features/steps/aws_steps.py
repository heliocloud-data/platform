"""
Cucumber step definition file for AWS stuff.
"""
import ssl

import boto3

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

from utils.aws_utils import (
    str_to_stack_name,
    find_cloudformation_stack_name_starts_with,
    find_user_pool_id_from_stack_name,
    create_or_update_user,
    update_user_set_password,
    delete_user,
    find_keypair_by_name,
    find_ec2_instances_by_name,
)

# pylint: disable=undefined-variable
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
# pylint: disable=function-redefined
# pylint: disable=line-too-long


def get_user_pool_id_by_heliocloud_name(hc_instance):
    client = boto3.client("cloudformation")

    name_starts_with = str_to_stack_name(f"{hc_instance}/Auth")
    auth_cloudformation_stack = find_cloudformation_stack_name_starts_with(client, name_starts_with)

    if auth_cloudformation_stack is None:
        raise ValueError(
            f"Unable to find CloudFormation stack w/ name starting with: {auth_cloudformation_stack}"
        )

    user_pool_id = find_user_pool_id_from_stack_name(client, auth_cloudformation_stack["StackName"])
    if user_pool_id is None:
        raise ValueError(
            f"Unable to find user_pool_id in stack w/ name: {auth_cloudformation_stack['StackName']}"
        )

    return user_pool_id


@given('no existing keypair named "{key_name}" exists')
def given_delete_keypair_if_exists(context, key_name):
    client = boto3.client("ec2")

    keypair_obj = find_keypair_by_name(client, key_name)

    # There is no keypair w/ that name, nothing to do.
    if keypair_obj is None:
        return

    keypair_id = keypair_obj["KeyPairId"]

    resp = client.delete_key_pair(KeyName=key_name, KeyPairId=keypair_id, DryRun=False)

    if 200 != resp["ResponseMetadata"]["HTTPStatusCode"]:
        print(resp)
        raise ValueError("Falied to delete keypair; id: {keypair_id}, name: {key_name}")


@given('no existing ec2 instance named "{ec2_name}" exists')
def given_terminate_ec2_instance_if_exists(context, ec2_name):
    client = boto3.client("ec2")

    ec2_arr = find_ec2_instances_by_name(client, ec2_name)

    # There is no keypair w/ that name, nothing to do.
    if ec2_arr is None:
        return

    instance_ids = []
    for item in ec2_arr:
        instance_ids.append(item["InstanceId"])

    if len(instance_ids) == 0:
        return

    resp = client.terminate_instances(InstanceIds=instance_ids, DryRun=False)

    if 200 != resp["ResponseMetadata"]["HTTPStatusCode"]:
        print(resp)
        raise ValueError("Falied to termine ec2 instances; id: {instance_ids}")


@then('create a user with the name "{user_name}"')
def test_step_aws_create_user(context, user_name):
    disable_warnings(InsecureRequestWarning)
    ssl.SSLContext.verify_mode = property(lambda self: ssl.CERT_NONE, lambda self, newval: None)

    user_pool_id = get_user_pool_id_by_heliocloud_name(context.hc_instance)

    client = boto3.client("cognito-idp")

    password = context.user_password

    create_or_update_user(client, user_pool_id, user_name, password)

    # Mark the password as changed to prevent the tests from having
    # change the password upon logging in.
    update_user_set_password(client, user_pool_id, user_name, password, True)


@then('delete a user with the name "{user_name}"')
def test_step_aws_delete_user(context, user_name):
    user_pool_id = get_user_pool_id_by_heliocloud_name(context.hc_instance)

    client = boto3.client("cognito-idp")

    delete_user(client, user_pool_id, user_name)
