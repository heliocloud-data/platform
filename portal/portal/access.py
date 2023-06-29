import boto3
from config import region


def get_aws_console_username(username):
    """turn the cognito username into the aws console user name. Edit if different."""
    #'CT-PowerUser-HelioCloud-Wenli.Mo@jhuapl.edu-208'
    return username


def get_access_flag(aws_session, username):
    iam_client = aws_session.client("iam", region_name=region)
    try:
        response = iam_client.get_user(UserName=username)
        access_flag = True
    except Exception as e:
        access_flag = False
    return access_flag


def create_access_key(aws_session, username):
    iam_client = aws_session.client("iam", region_name=region)
    response = iam_client.create_access_key(UserName=username)
    return response["AccessKey"]


def list_access_key(aws_session, username):
    iam_client = aws_session.client("iam", region_name=region)
    keys = iam_client.list_access_keys(UserName=username)["AccessKeyMetadata"]
    active_access_keys = [key for key in keys if key["Status"] == "Active"]
    inactive_access_keys = [key for key in keys if key["Status"] == "Inactive"]
    return active_access_keys, inactive_access_keys


def delete_access_key(aws_session, username, access_key_id):
    iam_client = aws_session.client("iam", region_name=region)
    response = iam_client.delete_access_key(
        UserName=username, AccessKeyId=access_key_id
    )
    return response


def update_key_status(aws_session, username, access_key_id, new_status):
    iam_client = aws_session.client("iam", region_name=region)
    response = iam_client.update_access_key(
        UserName=username, AccessKeyId=access_key_id, Status=new_status,
    )
    return response


def list_mfa_devices(aws_session, username):
    iam_client = aws_session.client("iam", region_name=region)
    response = iam_client.list_mfa_devices(UserName=username)
    return response["MFADevices"]


def get_session_token(access_key_id, secret_access_key, mfa_arn, mfa_token):
    user_session = boto3.Session(
        region_name=region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
    )
    sts_client = user_session.client("sts", region_name=region)
    response = sts_client.get_session_token(SerialNumber=mfa_arn, TokenCode=mfa_token,)
    return response["Credentials"]
