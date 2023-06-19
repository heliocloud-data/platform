import os
import random
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import boto3
import pymongo

from registry.lambdas.app.aws_utils.s3 import (
    get_bucket_name,
    get_dataset_entry_from_s3,
    get_manifest_from_s3
)
from registry.lambdas.app.exceptions import IngesterException
from registry.lambdas.app.ingest.ingester import Ingester
from registry.lambdas.app.ingest.manifest import get_manifest_from_fs
from registry.lambdas.app.local_utils.entry import get_entry_from_fs
from registry.lambdas.app.model.dataset import FileType, IndexType
from registry.lambdas.app.registry.repositories import DataSetRepository


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
    entry_key = ingest_folder + "entry.json"
    manifest_key = ingest_folder + "manifest.csv"

    # TODO: Update to use an SSH tunnel w/ AWS
    # AWS DocumentDB Environment
    # Expecting to connect on localhost to a DocumentDB instance
    db_hostname = "localhost"
    db_port = 27017
    db_global_pem = "test/integration/resources/document_db/global-bundle.pem"
    db_username = "hc_master"
    db_password = "password"
    # DB & collection names to use for testing.  These will be created & dropped for the test.
    db_name = "ingester"

    def setUp(self) -> None:
        self.__session = boto3.session.Session()

        # Populate the upload path in S3
        s3client = self.__session.client("s3")
        print("\nSetting up for test.")
        print("\tCreating buckets.")
        s3client.create_bucket(Bucket=TestIngesterAWS.ingest_bucket)
        s3client.create_bucket(Bucket=TestIngesterAWS.dataset_bucket)

        # Upload entry & Manifest files
        print("\tUploading entry & manifest files.")
        s3client.upload_file(Filename="test/integration/resources/s3/entry.json",
                             Bucket=TestIngesterAWS.ingest_bucket,
                             Key=TestIngesterAWS.entry_key)
        s3client.upload_file(Filename="test/integration/resources/s3/manifest.csv",
                             Bucket=TestIngesterAWS.ingest_bucket,
                             Key=TestIngesterAWS.manifest_key)

        # Upload files to ingest
        print("\tUploading data files.")
        for entry in os.scandir("test/integration/resources/s3"):
            if entry.is_file() and entry.name.startswith("mms1_fgm_brst_l2_20150901"):
                key = TestIngesterAWS.ingest_folder + "mms1/fgm/brst/l2/2015/09/01/" + entry.name
                s3client.upload_file(Filename=entry.path, Bucket=TestIngesterAWS.ingest_bucket,
                                     Key=key)
            elif entry.is_file() and entry.name.startswith("mms1_fgm_brst_l2_20150902"):
                key = TestIngesterAWS.ingest_folder + "mms1/fgm/brst/l2/2015/09/02/" + entry.name
                s3client.upload_file(Filename=entry.path, Bucket=TestIngesterAWS.ingest_bucket,
                                     Key=key)
        s3client.close()

    def tearDown(self) -> None:
        # Delete S3 buckets
        s3client = self.__session.client("s3")

        # Delete the upload bucket
        response = s3client.list_objects(Bucket=TestIngesterAWS.ingest_bucket)
        keys = [content['Key'] for content in response['Contents']]
        s3client.delete_objects(Bucket=TestIngesterAWS.ingest_bucket,
                                Delete={
                                    "Objects": [{'Key': key} for key in keys]
                                })
        s3client.delete_bucket(Bucket=TestIngesterAWS.ingest_bucket)

        # Delete the dataset bucket
        response = s3client.list_objects(Bucket=TestIngesterAWS.dataset_bucket)
        if 'Contents' in response:
            keys = [content['Key'] for content in response['Contents']]
            s3client.delete_objects(Bucket=TestIngesterAWS.dataset_bucket,
                                    Delete={
                                        "Objects": [{"Key": key} for key in keys]
                                    })
        s3client.delete_bucket(Bucket=TestIngesterAWS.dataset_bucket)
        s3client.close()

    @patch('registry.lambdas.app.registry.repositories.DataSetRepository')
    def test_invalid_dest_bucket(self, ds_repo) -> None:
        # Check that the Ingester throws an exception if provided an invalid destination location in the entry

        # Need a mock repository to inject into the Ingester
        ds_repo.save.return_value = 1

        # Set invalid destination location
        entry_ds = get_entry_from_fs('test/integration/resources/s3/entry.json')
        entry_ds.index = "s3://bucket.doesnt.exist/some_folder"
        manifest_df = get_manifest_from_fs("test/integration/resources/s3/manifest.csv")

        # Ingester exception gets raised if the destination doesn't exist
        with self.assertRaises(expected_exception=IngesterException) as raised:
            ingester = Ingester(ingest_bucket=TestIngesterAWS.ingest_bucket,
                                ingest_folder=TestIngesterAWS.ingest_folder, entry_dataset=entry_ds,
                                manifest_df=manifest_df, ds_repo=ds_repo)
            ingester.execute()

    @patch('registry.lambdas.app.registry.repositories.DataSetRepository')
    def test_missing_file(self, ds_repo):
        # Check that the Ingester throws an exception if the manifest references a file that doesn't exist

        # Need a mock repository to inject into the Ingester
        ds_repo.save.return_value = 1

        # Update the entry JSON with the real destination bucket
        entry_ds = get_dataset_entry_from_s3(session=self.__session, bucket_name=TestIngesterAWS.ingest_bucket,
                                             entry_key=TestIngesterAWS.entry_key)
        entry_ds.index = entry_ds.index.replace(
            get_bucket_name(entry_ds.index), TestIngesterAWS.dataset_bucket
        )

        # Get the manifest with a missing file
        manifest_df = get_manifest_from_fs(manifest_file="test/integration/resources/s3/manifest_missing_file.csv")

        # Run Ingester and validate it fails
        with self.assertRaises(expected_exception=IngesterException) as raised:
            ingester = Ingester(ingest_bucket=TestIngesterAWS.ingest_bucket,
                                ingest_folder=TestIngesterAWS.ingest_folder, entry_dataset=entry_ds,
                                manifest_df=manifest_df, ds_repo=ds_repo)
            ingester.execute()

    @patch('registry.lambdas.app.registry.repositories.DataSetRepository')
    def test_ingester_aws(self, ds_repo) -> None:
        # Test the Ingester implementation with an AWS account

        # Need a mock repository to inject into the Ingester
        ds_repo.save.return_value = 1

        # Get the entry dataset and update the index to use the dataset bucket created
        entry_dataset = get_dataset_entry_from_s3(session=self.__session,
                                                  bucket_name=TestIngesterAWS.ingest_bucket,
                                                  entry_key=TestIngesterAWS.entry_key)
        entry_dataset.index = entry_dataset.index.replace(
            get_bucket_name(entry_dataset.index), TestIngesterAWS.dataset_bucket
        )

        # Get the manifest
        manifest_df = get_manifest_from_s3(session=self.__session, bucket_name=TestIngesterAWS.ingest_bucket,
                                           manifest_key=TestIngesterAWS.manifest_key)

        # Create an Ingester instance and run it
        ingester = Ingester(ingest_bucket=TestIngesterAWS.ingest_bucket, ingest_folder=TestIngesterAWS.ingest_folder,
                            entry_dataset=entry_dataset, manifest_df=manifest_df, ds_repo=ds_repo)
        ingester.execute()

        # Do some validation of the target S3 bucket
        # Check for the index file & confirm the count of records
        s3client = self.__session.client("s3")
        response = s3client.get_object(Bucket=TestIngesterAWS.dataset_bucket, Key="MMS/MMS_2015.csv")
        self.assertEqual(len(response['Body'].readlines()) - 1, 32)

        # Check for the dataset directory and confirm 32 objects
        response = s3client.list_objects(Bucket=TestIngesterAWS.dataset_bucket, Prefix="MMS/mms1")
        self.assertEqual(len(response['Contents']), 32, msg="Contents wrong length")

        # Make sure the upload bucket was cleaned up
        response = s3client.list_objects(Bucket=TestIngesterAWS.ingest_bucket, Prefix=TestIngesterAWS.ingest_folder)
        # Only the entry & manifest files should remain
        remaining_keys = set(content['Key'] for content in response['Contents'])
        self.assertTrue(TestIngesterAWS.entry_key in remaining_keys, msg="Missing entry key")
        self.assertTrue(TestIngesterAWS.manifest_key in remaining_keys, msg="Missing manifest key")

        # save() should have been called once
        self.assertEqual(ds_repo.save.call_count, 1)

        # Clean up
        s3client.close()

    @unittest.skip("Requires SSH tunnel")
    def test_ingester_with_catalogdb_aws(self):
        # Test the Ingester implementation with a live catalog db, validating catalog db entries

        # Start the s3 client
        s3client = boto3.client('s3')

        # Get the entry dataset and update the index to use the dataset bucket created
        entry_dataset = get_dataset_entry_from_s3(session=self.__session, bucket_name=TestIngesterAWS.ingest_bucket,
                                                  entry_key=TestIngesterAWS.entry_key)
        entry_dataset.index = entry_dataset.index.replace(
            get_bucket_name(entry_dataset.index), TestIngesterAWS.dataset_bucket
        )

        # Get the manifest
        manifest_df = get_manifest_from_s3(session=self.__session, bucket_name=TestIngesterAWS.ingest_bucket,
                                           manifest_key=TestIngesterAWS.manifest_key)
        # Instantiate a clean repository instance
        db_client = pymongo.MongoClient(
            TestIngesterAWS.db_hostname,
            port=TestIngesterAWS.db_port,
            username=TestIngesterAWS.db_username,
            password=TestIngesterAWS.db_password,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            tlsCAFile=TestIngesterAWS.db_global_pem,
            directConnection=True,
            retryWrites=False
        )
        db_client.drop_database(TestIngesterAWS.db_name)
        ds_repo = DataSetRepository(db_client=db_client, db=TestIngesterAWS.db_name)

        # Create an Ingester instance and run it
        ingester = Ingester(ingest_bucket=TestIngesterAWS.ingest_bucket, ingest_folder=TestIngesterAWS.ingest_folder,
                            entry_dataset=entry_dataset, manifest_df=manifest_df, ds_repo=ds_repo)
        ingester.execute()

        # Do some validation of the catalog db.  Check various fields on the dataset
        dataset = ds_repo.get_all()[0]
        self.assertEqual(dataset.dataset_id, entry_dataset.dataset_id)
        self.assertEqual(dataset.index, entry_dataset.index)
        self.assertEqual(dataset.title, entry_dataset.title)
        self.assertEqual(dataset.start, datetime(year=2015, month=9, day=1, hour=12, minute=11, second=14,
                                                 tzinfo=ZoneInfo("UTC")))
        self.assertEqual(dataset.stop, datetime(year=2015, month=9, day=2, hour=18, minute=10, second=0,
                                                tzinfo=ZoneInfo("UTC")))
        self.assertEqual(dataset.filetype, [FileType.CDF])
        self.assertEqual(dataset.indextype, IndexType.CSV)
        self.assertEqual(dataset.creation, entry_dataset.creation)

        # Clean up
        s3client.close()
