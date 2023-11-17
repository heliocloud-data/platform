import io
import unittest
from unittest.mock import patch, Mock

import boto3
from botocore.client import BaseClient

from tools.catalog import CatalogRunner


class TestCatalogRunner(unittest.TestCase):
    """
    Unit test for the Catalog tool
    """

    @patch("boto3.Session")
    def test_failed_run(self, session: boto3.Session):
        """
        Test that the catalog tool fails on bad status code
        :return:
        """
        # Setup the boto3 session and client to support the runner failing due to status code
        client = Mock(BaseClient)
        client.list_functions = Mock(
            return_value={
                "Functions": [
                    {"FunctionName": "test_instanceCataloger"},
                    {"FunctionName": "another_instanceCataloger"},
                ]
            }
        )
        client.invoke = Mock(return_value={"StatusCode": 201})
        client.close = Mock(return_value=None)
        session.client = Mock(return_value=client)

        # Failed run
        runner = CatalogRunner(instance="test_instance", session=session)
        self.assertFalse(runner.execute())

    @patch("boto3.Session")
    def test_successful_run(self, session: boto3.Session):
        """
        Test the catalog tool recognizes a successful service invocation
        :return:
        """

        # Setup boto3 session and client to support the runner completing successfully
        client = Mock(BaseClient)
        client.list_functions = Mock(
            return_value={
                "Functions": [
                    {"FunctionName": "test_instanceCataloger"},
                ]
            }
        )
        client.invoke = Mock(
            return_value={
                "StatusCode": 200,
                "Payload": io.BytesIO(b"""{"test_instance_bucket":2}"""),
            }
        )
        client.close = Mock(return_value=None)
        session.client = Mock(return_value=client)

        # Successful run
        runner = CatalogRunner(instance="test_instance", session=session)
        self.assertTrue(runner.execute())
