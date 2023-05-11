import unittest
import boto3

from base_data.lambdas.app.ingest.entry import get_entry_from_fs, get_entry_from_s3
from base_data.lambdas.app.ingest.exceptions import IngesterException


class TestEntry(unittest.TestCase):

    def test_upload_entry_not_json(self):
        filename = 'test/base_data/resources/ingest/entry/not_json.txt'
        with self.assertRaises(IngesterException) as raised:
            entry = get_entry_from_fs(filename=filename)

    def test_upload_entry_valid(self):
        filename = 'test/base_data/resources/ingest/entry/valid.json'
        dataset = get_entry_from_fs(filename=filename)
        self.assertEqual(dataset.entry_id, 'MMS')
        self.assertEqual(dataset.ownership.about_url, 'https://www.nasa.gov')

    def test_entry_json_s3(self):
        bucket_name = 'heliocloud-dev-resources'
        entry_key = 'test/entry.json'
        s3client = boto3.client('s3')
        dataset = get_entry_from_s3(s3client, bucket_name=bucket_name, entry_key=entry_key)
        self.assertEqual(dataset.entry_id, 'MMS')
        self.assertEqual(dataset.ownership.resource_id, 'SPASE-1234567')
        s3client.close()
