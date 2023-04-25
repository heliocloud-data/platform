import unittest
import boto3

from base_data.ingest.exceptions import IngesterException
from base_data.ingest.manifest import get_manifest_from_fs, get_manifest_from_s3


class TestManifest(unittest.TestCase):

    def test_unrecognized_manifest(self):
        manifest_file = 'test/base_data/resources/ingest/manifest/manifest.txt'
        with self.assertRaises(IngesterException) as raised:
            manifest_df = get_manifest_from_fs(manifest_file=manifest_file)

    def test_manifest_missing_header(self):
        manifest_file = 'test/base_data/resources/ingest/manifest/missing_header.csv'
        with self.assertRaises(IngesterException) as raised:
            manifest_df = get_manifest_from_fs(manifest_file)

    def test_manifest_bad_data_type(self):
        manifest_file = 'test/base_data/resources/ingest/manifest/bad_data.csv'
        with self.assertRaises(IngesterException) as raised:
            manifest_df = get_manifest_from_fs(manifest_file=manifest_file)

    def test_get_valid_manifest(self):
        manifest_file = 'test/base_data/resources/ingest/manifest/valid.csv'
        manifest_df = get_manifest_from_fs(manifest_file=manifest_file)
        self.assertEqual(manifest_df.columns[0], 'time')

    def test_manifest_s3(self):
        bucket_name = 'heliocloud-dev-resources'
        manifest_key = 'test/manifest.csv'
        s3client = boto3.client('s3')
        manifest_df = get_manifest_from_s3(s3client=s3client, bucket_name=bucket_name, manifest_key=manifest_key)
        self.assertEqual(manifest_df.shape[0], 704)
        s3client.close()
