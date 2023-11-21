import boto3
import os.path
import random
import unittest
from registry.lambdas.app.aws_utils.s3 import get_dataset_entries_from_s3, get_manifest_from_s3

from utils import (
    new_boto_session,
    get_hc_instance,
    get_region,
)


class TestAWSUtils(unittest.TestCase):
    """
    Simple integration tests for AWS utils functionality.
    """

    pem_file = "registry/lambdas/app/resources/global-bundle.pem"
    bucket = "heliocloud-test-integration-" + str(random.randint(0, 1000))

    entry_dataset_file = os.path.dirname(__file__) + "/resources/s3/to_upload/entries.json"
    entry_dataset_key = "entries.json"

    manifest_file = os.path.dirname(__file__) + "/resources/s3/to_upload/MMS/manifest.csv"
    manifest_key = "manifest.csv"

    def setUp(self) -> None:
        self.__hc_instance = get_hc_instance()
        self.__location_constraint = get_region(self.__hc_instance, True)

        # put the test file up on S3
        s3client = boto3.client("s3")
        print(f"\n\n\n{self.__location_constraint}\n\n\n")
        s3client.create_bucket(
            Bucket=TestAWSUtils.bucket,
            CreateBucketConfiguration={
                "LocationConstraint": self.__location_constraint,
            },
        )
        s3client.upload_file(
            Filename=TestAWSUtils.entry_dataset_file,
            Bucket=TestAWSUtils.bucket,
            Key=TestAWSUtils.entry_dataset_key,
        )
        s3client.upload_file(
            Filename=TestAWSUtils.manifest_file,
            Bucket=TestAWSUtils.bucket,
            Key=TestAWSUtils.manifest_key,
        )
        s3client.close()

        # Session to use
        self.__hc_instance = get_hc_instance()
        self.__session = new_boto_session(self.__hc_instance)

    def tearDown(self) -> None:
        # Delete it from S3
        s3client = boto3.client("s3")
        s3client.delete_object(Bucket=TestAWSUtils.bucket, Key=TestAWSUtils.entry_dataset_key)
        s3client.delete_object(Bucket=TestAWSUtils.bucket, Key=TestAWSUtils.manifest_key)
        s3client.delete_bucket(Bucket=TestAWSUtils.bucket)
        s3client.close()

    def test_entriesx_json_s3(self):
        s3client = boto3.client("s3")
        dataset_list = get_dataset_entries_from_s3(
            session=self.__session,
            bucket_name=TestAWSUtils.bucket,
            entry_key=TestAWSUtils.entry_dataset_key,
        )
        self.assertEqual(dataset_list[0].dataset_id, "MMS")
        self.assertEqual(dataset_list[0].resource, "SPASE-1234567")
        s3client.close()

    def test_manifest_s3(self):
        s3client = boto3.client("s3")
        manifest_df = get_manifest_from_s3(
            session=self.__session,
            bucket_name=TestAWSUtils.bucket,
            manifest_key=TestAWSUtils.manifest_key,
        )
        self.assertEqual(manifest_df.shape[0], 6)
        s3client.close()
