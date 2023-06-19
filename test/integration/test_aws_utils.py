import boto3
import os.path
import random
import unittest

from registry.lambdas.app.aws_utils.s3 import (
    get_dataset_entry_from_s3,
    get_manifest_from_s3
)
from registry.lambdas.app.aws_utils.document_db import get_documentdb_client


class TestAWSUtils(unittest.TestCase):
    pem_file = "registry/lambdas/app/resources/global-bundle.pem"
    bucket = "heliocloud-test-integration-" + str(random.randint(0, 1000))

    entry_dataset_file = os.path.dirname(__file__) + "/resources/s3/entry.json"
    entry_dataset_key = 'entry.json'

    manifest_file = os.path.dirname(__file__) + "/resources/s3/manifest.csv"
    manifest_key = 'manifest.csv'

    def setUp(self) -> None:
        # put the test file up on S3
        s3client = boto3.client('s3')
        s3client.create_bucket(Bucket=TestAWSUtils.bucket)
        s3client.upload_file(Filename=TestAWSUtils.entry_dataset_file,
                             Bucket=TestAWSUtils.bucket,
                             Key=TestAWSUtils.entry_dataset_key)
        s3client.upload_file(Filename=TestAWSUtils.manifest_file,
                             Bucket=TestAWSUtils.bucket,
                             Key=TestAWSUtils.manifest_key)
        s3client.close()

        # Session to use
        self.__session = boto3.session.Session()

    def tearDown(self) -> None:
        # Delete it from S3
        s3client = boto3.client('s3')
        s3client.delete_object(Bucket=TestAWSUtils.bucket, Key=TestAWSUtils.entry_dataset_key)
        s3client.delete_object(Bucket=TestAWSUtils.bucket, Key=TestAWSUtils.manifest_key)
        s3client.delete_bucket(Bucket=TestAWSUtils.bucket)
        s3client.close()

    @unittest.skip("Requires SSH tunnel.")
    def test_documentdb_connection(self):
        get_documentdb_client(session=self.__session, secret_name="cjeschkedev/registry/catalogdb/credentials",
                              tlsCAFile=TestAWSUtils.pem_file, local=True)

    def test_entry_json_s3(self):
        s3client = boto3.client('s3')
        dataset = get_dataset_entry_from_s3(session=self.__session, bucket_name=TestAWSUtils.bucket,
                                            entry_key=TestAWSUtils.entry_dataset_key)
        self.assertEqual(dataset.dataset_id, 'MMS')
        self.assertEqual(dataset.resource, 'SPASE-1234567')
        s3client.close()

    def test_manifest_s3(self):
        s3client = boto3.client('s3')
        manifest_df = get_manifest_from_s3(session=self.__session, bucket_name=TestAWSUtils.bucket,
                                           manifest_key=TestAWSUtils.manifest_key)
        self.assertEqual(manifest_df.shape[0], 6)
        s3client.close()
