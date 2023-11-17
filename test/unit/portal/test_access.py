"""
Tests for access.py methods containing Portal logic.
"""
import datetime
import unittest
from unittest.mock import patch, Mock

import boto3
from botocore.exceptions import ClientError
from botocore.stub import Stubber

import portal.lib.access as access


class TestAccess(unittest.TestCase):
    def test_get_aws_console_username(self):
        username = "user"
        self.assertEqual(username, access.get_aws_console_username(username))

    @patch("boto3.session.Session")
    def test_get_access_flag(self, session):
        # Stub an IAM client
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
        session.client = Mock(return_value=iam_client)
        result = access.get_access_flag(session, "test")
        self.assertTrue(result)

    @patch("boto3.session.Session")
    def test_get_access_flag_no_user(self, session):
        # Stub an IAM client
        iam_client = boto3.client("iam")
        stubber = Stubber(iam_client)
        stubber.add_client_error("get_user", service_error_code="NoSuchEntity")
        stubber.activate()

        # Let our mock session use it
        session.client = Mock(return_value=iam_client)
        result = access.get_access_flag(session, username="test")
        self.assertFalse(result)

    @patch("boto3.session.Session")
    def test_get_access_flag_error(self, session):
        # Stub an IAM client
        iam_client = boto3.client("iam")
        stubber = Stubber(iam_client)
        stubber.add_client_error("get_user", service_error_code="InvalidInput")
        stubber.activate()

        session.client = Mock(return_value=iam_client)
        with self.assertRaises(ClientError):
            access.get_access_flag(session, username="test")

    @patch("boto3.session.Session")
    def test_list_access_key(self, session):
        # Check for the right number of access keys

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
        session.client = Mock(return_value=iam_client)

        active_keys, inactive_keys = access.list_access_key(session, username="tester")
        self.assertEqual(len(active_keys), 1)
        self.assertEqual(len(inactive_keys), 2)

    @patch("boto3.session.Session")
    def test_create_access_key(self, session):
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
        session.client = Mock(return_value=iam_client)

        result = access.create_access_key(session, "tester")
        self.assertDictEqual(response["AccessKey"], result)

    @patch("boto3.session.Session")
    def test_delete_access_key(self, session):
        iam_client = boto3.client("iam")
        stub = Stubber(iam_client)
        response = {"ResponseMetadata": {"RequestId": "10923019313"}}
        stub.add_response("delete_access_key", service_response=response)
        stub.activate()
        session.client = Mock(return_value=iam_client)

        result = access.delete_access_key(
            aws_session=session, username="tester", access_key_id="123-aaaaaaaaaaaa"
        )
        self.assertTrue("ResponseMetadata" in result.keys())

    @patch("boto3.session.Session")
    def test_update_key_status(self, session):
        iam_client = boto3.client("iam")
        stub = Stubber(iam_client)
        response = {"ResponseMetadata": {"RequestId": "7a62c49f-347e-4fc4-9331-6e8eEXAMPLE"}}
        stub.add_response("update_access_key", service_response=response)
        stub.activate()
        session.client = Mock(return_value=iam_client)

        result = access.update_key_status(
            aws_session=session,
            username="tester",
            access_key_id="123-aaaaaaaaaaaa",
            new_status="Inactive",
        )
        self.assertTrue("ResponseMetadata" in result.keys())

    @patch("boto3.session.Session")
    def test_list_mfa_devices(self, session):
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
        session.client = Mock(return_value=iam_client)

        result = access.list_mfa_devices(aws_session=session, username="tester1")
        self.assertListEqual(response["MFADevices"], result)

    @patch("boto3.session.Session")
    def test_get_session_token(self, session):
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
        session.client = Mock(return_value=sts_client)

        result = access.get_session_token(
            user_session=session, mfa_token="abcdef", mfa_arn="1234565789"
        )
        self.assertEqual(response["Credentials"], result)
