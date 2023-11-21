import boto3
import os
import random
import unittest
from unittest.mock import patch

from registry.lambdas.app.aws_utils.s3 import (
    get_bucket_name,
    get_dataset_entries_from_s3,
    get_manifest_from_s3,
)
from registry.lambdas.app.core.exceptions import IngesterException
from registry.lambdas.app.ingest.ingester import Ingester
from registry.lambdas.app.ingest.manifest import get_manifest_from_fs
from registry.lambdas.app.local_utils.entry import get_entries_from_fs

from utils import (
    new_boto_session,
    get_hc_instance,
    get_region,
)


class TestIngesterAWS(unittest.TestCase):
    """
    Test Case for testing the Ingester codebase with AWS.  This TestCase requires access to AWS S3.
    It uses a mock DataSet repository instance due to the challenges of connecting to a securely hosted
    DocumentDB instance in AWS
    """

    # AWS S3
    # Generate bucket names to avoid collisions with existing buckets in AWS
    ingest_bucket = "heliocloud-test-integration-ingest-" + str(random.randint(0, 1000))
    dataset_bucket = "heliocloud-test-integration-dataset-" + str(random.randint(1001, 2000))
    ingest_folder = "upload/"
    entry_key = ingest_folder + "entries.json"
    entries_local_file = "test/integration/resources/s3/to_upload/entries.json"

    def setUp(self) -> None:
        self.__hc_instance = get_hc_instance()
        self.__session = new_boto_session(self.__hc_instance)
        self.__location_constraint = get_region(self.__hc_instance, True)

        # Populate the upload path in S3
        s3client = self.__session.client(service_name="s3")
        print("\nSetting up for test.")
        print("\tCreating buckets.")

        print(f"\t\t{TestIngesterAWS.ingest_bucket}...")
        s3client.create_bucket(
            Bucket=TestIngesterAWS.ingest_bucket,
            CreateBucketConfiguration={
                "LocationConstraint": self.__location_constraint,
            },
        )
        print(f"\t\t{TestIngesterAWS.dataset_bucket}...")
        s3client.create_bucket(
            Bucket=TestIngesterAWS.dataset_bucket,
            CreateBucketConfiguration={
                "LocationConstraint": self.__location_constraint,
            },
        )

        # Upload entries file
        print("\tUploading entries file")
        s3client.upload_file(
            Filename=TestIngesterAWS.entries_local_file,
            Bucket=TestIngesterAWS.ingest_bucket,
            Key=TestIngesterAWS.entry_key,
        )

        # Upload files to ingest - see files in test/integration/resources/s3/to_upload
        print("\tUploading data files.")
        to_upload_path = "test/integration/resources/s3/to_upload/"
        for root, dirs, files in os.walk(to_upload_path):
            for filename in files:
                local_path = os.path.join(root, filename)
                key = TestIngesterAWS.ingest_folder + local_path.split(to_upload_path)[1]
                s3client.upload_file(
                    Filename=local_path, Bucket=TestIngesterAWS.ingest_bucket, Key=key
                )
                print(f"\tUploaded file s3://{TestIngesterAWS.ingest_bucket}/{key}.")
        s3client.close()

    def tearDown(self) -> None:
        # Delete S3 buckets
        s3client = self.__session.client("s3")

        # Delete the upload bucket
        response = s3client.list_objects(Bucket=TestIngesterAWS.ingest_bucket)
        keys = [content["Key"] for content in response["Contents"]]
        s3client.delete_objects(
            Bucket=TestIngesterAWS.ingest_bucket, Delete={"Objects": [{"Key": key} for key in keys]}
        )
        s3client.delete_bucket(Bucket=TestIngesterAWS.ingest_bucket)

        # Delete the dataset bucket
        response = s3client.list_objects(Bucket=TestIngesterAWS.dataset_bucket)
        if "Contents" in response:
            keys = [content["Key"] for content in response["Contents"]]
            s3client.delete_objects(
                Bucket=TestIngesterAWS.dataset_bucket,
                Delete={"Objects": [{"Key": key} for key in keys]},
            )
        s3client.delete_bucket(Bucket=TestIngesterAWS.dataset_bucket)
        s3client.close()

    @patch("registry.lambdas.app.catalog.dataset_repository.DataSetRepository")
    def test_invalid_dest_bucket(self, ds_repo) -> None:
        # Check that the Ingester throws an exception if provided an invalid destination location in the entry

        # Need a mock repository to inject into the Ingester
        ds_repo.save.return_value = 1

        # Set invalid destination location
        entry_ds_list = get_entries_from_fs(TestIngesterAWS.entries_local_file)

        # Ingester exception gets raised if the destination doesn't exist
        for entry_ds in entry_ds_list:
            index = entry_ds.index.rsplit("/", 1)[1]
            manifest_key = os.path.join(TestIngesterAWS.ingest_folder, index, "manifest.csv")

            manifest_df = get_manifest_from_s3(
                session=self.__session,
                bucket_name=TestIngesterAWS.ingest_bucket,
                manifest_key=manifest_key,
            )

            entry_ds.index = "s3://bucket.doesnt.exist/some_folder"
            with self.assertRaises(expected_exception=IngesterException) as raised:
                ingester = Ingester(
                    ingest_bucket=TestIngesterAWS.ingest_bucket,
                    ingest_folder=TestIngesterAWS.ingest_folder,
                    entry_dataset=entry_ds,
                    manifest_df=manifest_df,
                    ds_repo=ds_repo,
                )
                ingester.execute()

    @patch("registry.lambdas.app.catalog.dataset_repository.DataSetRepository")
    def test_missing_file(self, ds_repo):
        # Check that the Ingester throws an exception if the manifest references a file that doesn't exist

        # Need a mock repository to inject into the Ingester
        ds_repo.save.return_value = 1

        # Update the entry JSON with the real destination bucket
        entry_ds_list = get_dataset_entries_from_s3(
            session=self.__session,
            bucket_name=TestIngesterAWS.ingest_bucket,
            entry_key=TestIngesterAWS.entry_key,
        )

        # Get the manifest with a missing file
        manifest_df = get_manifest_from_fs(
            manifest_file="test/integration/resources/s3/manifest_missing_file.csv"
        )

        # Run Ingester and validate it fails
        for entry_ds in entry_ds_list:
            entry_ds.index = entry_ds.index.replace(
                get_bucket_name(entry_ds.index), TestIngesterAWS.dataset_bucket
            )
            with self.assertRaises(expected_exception=IngesterException) as raised:
                ingester = Ingester(
                    ingest_bucket=TestIngesterAWS.ingest_bucket,
                    ingest_folder=TestIngesterAWS.ingest_folder,
                    entry_dataset=entry_ds,
                    manifest_df=manifest_df,
                    ds_repo=ds_repo,
                )
                ingester.execute()

    @patch("registry.lambdas.app.catalog.dataset_repository.DataSetRepository")
    def test_bad_extension(self, ds_repo):
        # Check that the Ingester throws an exception if a file with a bad extension is found while
        # validating the manifest

        # Need a mock repository to inject into the Ingester
        ds_repo.save.return_value = 1

        # Update the entry JSON with the real destination bucket
        entry_ds_list = get_dataset_entries_from_s3(
            session=self.__session,
            bucket_name=TestIngesterAWS.ingest_bucket,
            entry_key=TestIngesterAWS.entry_key,
        )

        # Get the manifest with a missing file
        manifest_df = get_manifest_from_fs(
            manifest_file="test/integration/resources/s3/manifest_bad_extension.csv"
        )

        local_path = "test/integration/resources/s3/to_upload_bad_extension/MMS/"

        file_name = (
            "mms1/fgm/brst/l2/2015/09/01/mms1_fgm_brst_l2_20150901121114_v4.18.0.notanextension"
        )

        key = os.path.join(TestIngesterAWS.ingest_folder, "MMS", file_name)
        s3client = self.__session.client(service_name="s3")
        s3client.upload_file(
            Filename=os.path.join(local_path, file_name),
            Bucket=TestIngesterAWS.ingest_bucket,
            Key=key,
        )

        # Run Ingester and validate it fails
        for entry_ds in entry_ds_list:
            entry_ds.index = entry_ds.index.replace(
                get_bucket_name(entry_ds.index), TestIngesterAWS.dataset_bucket
            )
            with self.assertRaises(expected_exception=IngesterException) as raised:
                ingester = Ingester(
                    ingest_bucket=TestIngesterAWS.ingest_bucket,
                    ingest_folder=TestIngesterAWS.ingest_folder,
                    entry_dataset=entry_ds,
                    manifest_df=manifest_df,
                    ds_repo=ds_repo,
                )
                ingester.execute()

    @patch("registry.lambdas.app.catalog.dataset_repository.DataSetRepository")
    def test_ingester_aws(self, ds_repo) -> None:
        # Test the Ingester implementation with an AWS account

        # Need a mock repository to inject into the Ingester
        ds_repo.save.return_value = 1

        # Get the entry dataset and update the index to use the dataset bucket created
        entry_ds_list = get_dataset_entries_from_s3(
            session=self.__session,
            bucket_name=TestIngesterAWS.ingest_bucket,
            entry_key=TestIngesterAWS.entry_key,
        )

        # Create an Ingester instance and run it
        for entry_ds in entry_ds_list:
            # Get the manifest for this entry
            index = entry_ds.index.rsplit("/", 1)[1]
            manifest_key = os.path.join(TestIngesterAWS.ingest_folder, index, "manifest.csv")

            manifest_df = get_manifest_from_s3(
                session=self.__session,
                bucket_name=TestIngesterAWS.ingest_bucket,
                manifest_key=manifest_key,
            )

            entry_ds.index = entry_ds.index.replace(
                get_bucket_name(entry_ds.index), TestIngesterAWS.dataset_bucket
            )
            ingester = Ingester(
                ingest_bucket=TestIngesterAWS.ingest_bucket,
                ingest_folder=TestIngesterAWS.ingest_folder,
                entry_dataset=entry_ds,
                manifest_df=manifest_df,
                ds_repo=ds_repo,
            )
            result = ingester.execute()

            self.assertEqual(result.dataset_updated, index)
            self.assertEqual(result.files_contributed, 6)

            # Do some validation of the target S3 bucket
            # Check for the index file & confirm the count of records
            s3client = self.__session.client("s3")
            response = s3client.get_object(
                Bucket=TestIngesterAWS.dataset_bucket, Key=f"{index}/{index}_2015.csv"
            )
            self.assertEqual(len(response["Body"].readlines()) - 1, 4)
            response = s3client.get_object(
                Bucket=TestIngesterAWS.dataset_bucket, Key=f"{index}/{index}_2019.csv"
            )
            self.assertEqual(len(response["Body"].readlines()) - 1, 2)

            # Check for the dataset directory and confirm 6 objects
            response = s3client.list_objects(
                Bucket=TestIngesterAWS.dataset_bucket, Prefix=f"{index}/{index.lower()}1"
            )
            self.assertEqual(len(response["Contents"]), 6, msg="Contents wrong length")

            # Make sure the upload bucket was cleaned up
            response = s3client.list_objects(
                Bucket=TestIngesterAWS.ingest_bucket, Prefix=TestIngesterAWS.ingest_folder
            )
            # Only the entry & manifest files should remain
            remaining_keys = set(content["Key"] for content in response["Contents"])
            self.assertTrue(TestIngesterAWS.entry_key in remaining_keys, msg="Missing entry key")
            self.assertTrue(manifest_key in remaining_keys, msg="Missing manifest key")
            # Clean up
            s3client.close()

        self.assertEqual(ds_repo.save.call_count, len(entry_ds_list))
