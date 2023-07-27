import pytest
import unittest
import sys

from config import Config

class TestConfig(unittest.TestCase):
    """
    Various tests for parsing configuration files.
    """

    def test_method_load_configs_OK(self):
        config_obj = Config()
        cfg = config_obj.load_configs('test/unit/resources/test_config/instance', 'test_config')

        print(cfg)

        # Confirm values in the instance document
        self.assertEqual(cfg['env']['account'], 123456789)
        self.assertEqual(cfg['env']['region'], 'us-east-100')
        self.assertEqual(cfg['enabled']['registry'], True)
        self.assertEqual(cfg['registry']['datasetBucketNames'][0], "suds-datasets-1")
        self.assertEqual(cfg['registry']['ingestBucketName'], "acid-reflux")

        # Confirm values in the default document
        self.assertEqual(cfg['auth']['domain_prefix'], "apl-helio")
        self.assertIsNone(cfg['portal']['domain_url'])
        self.assertIsNone(cfg['portal']['domain_record'])
        self.assertIsNone(cfg['portal']['domain_certificate_arn'])
        self.assertIsNone(cfg['daskhub'])

    def test_method_load_configs_OK_BasedirIsNull_Example(self):
        config_obj = Config()
        cfg = config_obj.load_configs(id='example')

        print(cfg)

        # Confirm values in the instance document
        self.assertEqual(cfg['env']['account'], 12345678)

    def test_method_load_configs_FileNotFound(self):
        config_obj = Config()
        try:
            cfg = config_obj.load_configs('test/unit/resources/test_config/instance', 'DoesNotExist')
            self.fail("FileNotFoundError should be thrown")
        except FileNotFoundError as e:
            print(e)

    def test_method_load_configs_InvalidFile(self):
        config_obj = Config()
        try:
            cfg = config_obj.load_configs('test/unit/resources/test_config/instance', 'invalid')
            self.fail("ValueError should be thrown")
        except ValueError as e:
            print(e)
