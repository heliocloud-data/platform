"""
Methods for manipulating AWS Access Keys & Session Tokens for a
HelioCloud user.
"""

from botocore.errorfactory import ClientError

# Local imports
from .config import region


def get_aws_console_username(username):
    """
    Previously: Supposed to turn the AWS Cognito username into the matching AWS Console user
    name.
    Current implementation is empty.
    TODO: Figure out what we are supposed to do here.
    """
    return username


def get_access_flag(aws_session, username) -> bool:
    """
    Returns True if username exists in AWS IAM, else False.
    """
    iam_client = aws_session.client("iam", region_name=region)
    try:
        iam_client.get_user(UserName=username)

    except ClientError as error:
        # Couldn't find the user
        if isinstance(error, iam_client.exceptions.NoSuchEntityException):
            return False

        # Different problem
        raise

    return True


def create_access_key(aws_session, username):
    """
    Creates an Access Key in AWS IAM for the specified user in the AWS region
    the Portal is deployed in.
    """
    iam_client = aws_session.client("iam", region_name=region)
    response = iam_client.create_access_key(UserName=username)
    return response["AccessKey"]


def list_access_key(aws_session, username):
    """
    Lists the Access Key(s) in AWS IAM for the specified user, in the AWS
    region the Portal is deployed in.
    """
    iam_client = aws_session.client("iam", region_name=region)
    keys = iam_client.list_access_keys(UserName=username)["AccessKeyMetadata"]
    active_access_keys = [key for key in keys if key["Status"] == "Active"]
    inactive_access_keys = [key for key in keys if key["Status"] == "Inactive"]
    return active_access_keys, inactive_access_keys


def delete_access_key(aws_session, username, access_key_id):
    """
    Deletes the Access Key in AWS IAM for a particular user in the AWS region
    in which the Portal is deployed.
    """
    iam_client = aws_session.client("iam", region_name=region)
    response = iam_client.delete_access_key(UserName=username, AccessKeyId=access_key_id)
    return response


def update_key_status(aws_session, username, access_key_id, new_status):
    """
    Updates the status of a user's access key in AWS IAM in the AWS region
    in which the Portal is deployed.
    """
    iam_client = aws_session.client("iam", region_name=region)
    response = iam_client.update_access_key(
        UserName=username,
        AccessKeyId=access_key_id,
        Status=new_status,
    )
    return response


def list_mfa_devices(aws_session, username):
    """
    Returns the MFA Devices configured for a particular user in
    AWS IAM for the region in which the Portal is deployed.
    """
    iam_client = aws_session.client("iam", region_name=region)
    response = iam_client.list_mfa_devices(UserName=username)
    return response["MFADevices"]


def get_session_token(user_session, mfa_arn, mfa_token):
    """
    Returns a session token created for a particular user, based on the provided
    user_session: a boto3.session instantiated using the user's access key in the region
        in which the portal is running
    """
    sts_client = user_session.client("sts", region_name=region)
    response = sts_client.get_session_token(SerialNumber=mfa_arn, TokenCode=mfa_token)
    return response["Credentials"]
