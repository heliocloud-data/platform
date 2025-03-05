"""
Tests for access.py methods containing Portal logic.
"""
import datetime
from unittest.mock import Mock

import boto3
import pytest as pytest
from botocore.exceptions import ClientError
from botocore.stub import Stubber

import portal.lib.access as access


def test_get_aws_console_username():
    """
    Test getting the AWS console username for a user.
    """
    username = "user"
    assert username == access.get_aws_console_username(username)


def test_get_access_flag():
    """
    Confirm that an existing user is granted access.
    """
    iam_client = boto3.client("iam")
    stubber = Stubber(iam_client)
    response = {
        "User": {
            "UserName": "test",
            "Path": "A",
            "UserId": "ABCDEFGHIJKLMNOP",
            "Arn": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "CreateDate": datetime.datetime.now(),
        }
    }
    stubber.add_response("get_user", service_response=response)
    stubber.activate()

    # Use it
    session = Mock(boto3.Session)
    session.client = Mock(return_value=iam_client)
    result = access.get_access_flag(session, "test")
    assert result is True


def test_get_access_flag_no_user():
    """
    Confirm that a non-existent user is not granted access.
    """
    iam_client = boto3.client("iam")
    stubber = Stubber(iam_client)
    stubber.add_client_error("get_user", service_error_code="NoSuchEntity")
    stubber.activate()

    # Let our mock session use it
    session = Mock(boto3.Session)
    session.client = Mock(return_value=iam_client)
    result = access.get_access_flag(session, username="test")
    assert result is False


def test_get_access_flag_error():
    """
    Check that an error is propagated correctly from AWS.
    """

    # Stub an IAM client
    iam_client = boto3.client("iam")
    stubber = Stubber(iam_client)
    stubber.add_client_error("get_user", service_error_code="InvalidInput")
    stubber.activate()

    session = Mock(boto3.Session)
    session.client = Mock(return_value=iam_client)
    with pytest.raises(ClientError):
        access.get_access_flag(session, username="test")


def test_list_access_key():
    """
    Confirm a correct understanding of inactive vs. active keys as returned from the
    AWS IAM service for a user.
    """

    iam_client = boto3.client("iam")
    stub = Stubber(iam_client)
    response = {
        "AccessKeyMetadata": [
            {
                "AccessKeyId": "123-aaaaaaaaaaaa",
                "CreateDate": datetime.datetime.now(),
                "Status": "Active",
            },
            {
                "AccessKeyId": "123-zzzzzzzzzzzz",
                "CreateDate": datetime.datetime.now(),
                "Status": "Inactive",
            },
            {
                "AccessKeyId": "456-zzzzzzzzzzzz",
                "CreateDate": datetime.datetime.now(),
                "Status": "Inactive",
            },
        ]
    }
    stub.add_response("list_access_keys", service_response=response)
    stub.activate()
    session = Mock(boto3.Session)
    session.client = Mock(return_value=iam_client)

    # Check for the right counts of active & inactive keys for the user
    active_keys, inactive_keys = access.list_access_key(session, username="tester")
    assert len(active_keys) == 1
    assert len(inactive_keys) == 2


def test_create_access_key():
    """
    Test that we get the correct access key information back from the AWS IAM client
    on creation.
    """
    iam_client = boto3.client("iam")
    stubber = Stubber(iam_client)
    response = {
        "AccessKey": {
            "AccessKeyId": "abcdefghijklmnop",
            "SecretAccessKey": "some_secret_key",
            "UserName": "some_name",
            "Status": "active",
        }
    }
    stubber.add_response("create_access_key", service_response=response)
    stubber.activate()
    session = Mock(boto3.Session)
    session.client = Mock(return_value=iam_client)

    result = access.create_access_key(session, "tester")
    assert result == response["AccessKey"]


def test_delete_access_key():
    """
    Check deletion of an access key via the AWS IAM service.
    """
    iam_client = boto3.client("iam")
    stub = Stubber(iam_client)
    response = {"ResponseMetadata": {"RequestId": "10923019313"}}
    stub.add_response("delete_access_key", service_response=response)
    stub.activate()

    session = Mock(boto3.Session)
    session.client = Mock(return_value=iam_client)

    result = access.delete_access_key(
        aws_session=session, username="tester", access_key_id="123-aaaaaaaaaaaa"
    )
    assert "ResponseMetadata" in result.keys()


def test_update_key_status():
    """
    Flip a key to inactive.
    """
    iam_client = boto3.client("iam")
    stub = Stubber(iam_client)
    response = {"ResponseMetadata": {"RequestId": "7a62c49f-347e-4fc4-9331-6e8eEXAMPLE"}}
    stub.add_response("update_access_key", service_response=response)
    stub.activate()
    session = Mock(boto3.Session)
    session.client = Mock(return_value=iam_client)

    result = access.update_key_status(
        aws_session=session,
        username="tester",
        access_key_id="123-aaaaaaaaaaaa",
        new_status="Inactive",
    )
    assert "ResponseMetadata" in result.keys()


def test_list_mfa_devices():
    """
    Get a list of MFA devices for a user from AWS IAM.
    """
    iam_client = boto3.client("iam")
    stub = Stubber(iam_client)
    response = {
        "MFADevices": [
            {
                "UserName": "tester1",
                "SerialNumber": "kajsdlkjadlkajB",
                "EnableDate": datetime.datetime.now(),
            },
            {
                "UserName": "tester1",
                "SerialNumber": "kajsdlkjadlkajA",
                "EnableDate": datetime.datetime.now(),
            },
        ],
        "IsTruncated": False,
    }
    stub.add_response("list_mfa_devices", service_response=response)
    stub.activate()
    session = Mock(boto3.Session)
    session.client = Mock(return_value=iam_client)

    result = access.list_mfa_devices(aws_session=session, username="tester1")
    assert response["MFADevices"] == result


def test_get_session_token():
    """
    Get an AWS session token from AWS STS when presented with an MFA token.
    """
    sts_client = boto3.client("sts")
    stub = Stubber(sts_client)
    response = {
        "Credentials": {
            "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY",
            "SessionToken": "AQoEXAMPLEH4aoAH0gNCAPyJxz4BlCFFxWNE1OPTgk5T",
            "Expiration": "2020-05-19T18:06:10+00:00",
        }
    }
    stub.add_response("get_session_token", response)
    stub.activate()
    session = Mock(boto3.Session)
    session.client = Mock(return_value=sts_client)

    result = access.get_session_token(
        user_session=session, mfa_token="abcdef", mfa_arn="1234565789"
    )
    assert response["Credentials"] == result
