import pytest
import unittest
import sys

from app_config import load_configs


class TestConfig(unittest.TestCase):
    """
    Various tests for parsing configuration files.
    """

    def test_method_load_configs_OK(self):
        cfg = load_configs("test/unit/resources/test_app_config/instance", "test_config")

        print(cfg)

        # Confirm values in the instance document
        self.assertEqual(cfg["env"]["account"], 123456789)
        self.assertEqual(cfg["env"]["region"], "us-east-100")
        self.assertEqual(cfg["enabled"]["registry"], True)
        self.assertEqual(cfg["registry"]["datasetBucketNames"][0], "suds-datasets-1")
        self.assertEqual(cfg["registry"]["ingestBucketName"], "acid-reflux")

        # Confirm values in the default document
        self.assertEqual(cfg["auth"]["domain_prefix"], "apl-helio")
        self.assertIsNone(cfg["portal"]["domain_url"])
        self.assertIsNone(cfg["portal"]["domain_record"])
        self.assertIsNone(cfg["portal"]["domain_certificate_arn"])
        self.assertIsNone(cfg["daskhub"])

    def test_method_load_configs_OK_BasedirIsNull_Example(self):
        cfg = load_configs(hc_id="example")

        print(cfg)

        # Confirm values in the instance document
        self.assertEqual(cfg["env"]["account"], 12345678)

    def test_method_load_configs_FileNotFound(self):
        try:
            cfg = load_configs("test/unit/resources/test_app_config/instance", "DoesNotExist")
            self.fail("FileNotFoundError should be thrown")
        except FileNotFoundError as e:
            print(e)

    def test_method_load_configs_InvalidFile(self):
        try:
            cfg = load_configs("test/unit/resources/test_app_config/instance", "invalid")
            self.fail("ValueError should be thrown")
        except ValueError as e:
            print(e)
