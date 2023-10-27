"""
Contains helpful functions for interacting with the AWS.
"""
from botocore.exceptions import ClientError


def str_to_stack_name(txt) -> str:
    """
    Translate the name of a stack to it's CloudFormation stack name.
    """
    return txt.replace("-", "").replace("/", "")


def find_cloudformation_stack_name_starts_with(client, name_starts_with):
    """
    Find the cloudformation stack name that starts with the given text.
    """
    obj = None

    resp = client.list_stacks(
        StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE"],
    )

    for item in resp["StackSummaries"]:
        if item["StackName"].startswith(name_starts_with):
            obj = item
            break

    return obj


def find_user_pool_id_from_stack_name(client, stack_name):
    """
    Find the user pool identifier from the stack name.
    """

    resp = client.describe_stacks(StackName=stack_name)
    for item in resp["Stacks"]:
        for item2 in item["Outputs"]:
            # This I'm sure will be a little brittle, as there are many matches w/
            # `RefPool` in the name.  user_pool_id's will have an underscore between
            # the region and the logical ID, the other keys don't appear to have that.
            #
            #  us-north-7_AbCdefgHi
            if "ExportsOutputRefPool" in item2["OutputKey"] and "_" in item2["OutputValue"]:
                return item2["OutputValue"]
    return None


def create_or_update_user(client, user_pool_id, user_name, password):
    """
    Create or update the user.
    """

    user = find_user_by_name(client, user_pool_id, user_name)

    if user is None:
        return create_user(client, user_pool_id, user_name, password)

    return update_user_set_password(client, user_pool_id, user_name, password, False)


def find_user_by_name(client, user_pool_id, user_name):
    """
    Find the user by name.
    """

    try:
        return client.admin_get_user(UserPoolId=user_pool_id, Username=user_name)
    except ClientError as err:
        if err.response["Error"]["Code"] == "UserNotFoundException":
            return None
        raise


def update_user_set_password(client, user_pool_id, user_name, password, permanent):
    """
    Update the user's password.
    """

    resp = client.admin_set_user_password(
        UserPoolId=user_pool_id, Username=user_name, Password=password, Permanent=permanent
    )
    return resp


def create_user(client, user_pool_id, user_name, password):
    """
    Create a user.
    """

    resp = client.admin_create_user(
        UserPoolId=user_pool_id,
        Username=user_name,
        UserAttributes=[
            {"Name": "email", "Value": f"{user_name}@example.com"},
        ],
        ValidationData=[
            {"Name": "string", "Value": "string"},
        ],
        TemporaryPassword=password,
        ForceAliasCreation=True,
        MessageAction="SUPPRESS",
        DesiredDeliveryMediums=[
            "EMAIL",
        ],
        ClientMetadata={"string": "string"},
    )
    return resp


def delete_user(client, user_pool_id, user_name):
    """
    Delete a user.
    """
    resp = client.admin_delete_user(UserPoolId=user_pool_id, Username=user_name)
    return resp


def find_keypair_by_name(client, key_name):
    """
    Find a keypair by name.
    """
    try:
        resp = client.describe_key_pairs(
            KeyNames=[key_name],
            DryRun=False,
        )

        for item in resp["KeyPairs"]:
            return item
    except ClientError as err:
        if err.response["Error"]["Code"] == "InvalidKeyPair.NotFound":
            return None
        raise


def find_ec2_instances_by_name(client, name):
    """
    Find and EC2 instance by name.
    """
    try:
        resp = client.describe_instances(
            Filters=[{"Name": "tag:Name", "Values": [name]}],
            DryRun=False,
        )

        if len(resp["Reservations"]) == 0:
            return []

        return resp["Reservations"][0]["Instances"]
    except ClientError as err:
        if err.response["Error"]["Code"] == "InvalidKeyPair.NotFound":
            return None
        raise
