import json
import random
import unittest

import boto3
import pymongo

from registry.lambdas.app.model.dataset import DataSet
from registry.lambdas.app.catalog.cataloger import Cataloger
from registry.lambdas.app.repositories import DataSetRepository


@unittest.skip("Requires SSH tunnel to DocumentDB.")
class TestCatalogerAWS(unittest.TestCase):
    """
    Test Case for testing the Ingester codebase with AWS.  Uses live AWS resources to
    exercise all the Ingester logic.
    """
    # AWS S3
    # Generate bucket names to avoid collisions with existing buckets in AWS
    ds_bucket_1 = "heliocloud-test-integration-" + str(random.randint(0, 1000))
    ds_bucket_2 = "heliocloud-test-integration-" + str(random.randint(1001, 2000))

    # AWS DocumentDB Environment
    # Expecting to connect on localhost to a DocumentDB instance
    db_hostname = "localhost"
    db_port = 27017
    db_global_pem = "registry/lambdas/app/resources/global-bundle.pem"

    # TODO: Create an integration test account.  Temporarily using master credentials here (BAD)
    db_username = "hc_master"
    db_password = "password"

    # DB & collection names to use for testing.  These will be created & dropped for the test.
    db_name = "cataloger"

    def setUp(self) -> None:
        # Populate the upload path in S3
        s3client = boto3.client('s3')
        print("----------")
        print(f"Creating dataset buckets: {TestCatalogerAWS.ds_bucket_1}, {TestCatalogerAWS.ds_bucket_2}")
        s3client.create_bucket(Bucket=TestCatalogerAWS.ds_bucket_1)
        s3client.create_bucket(Bucket=TestCatalogerAWS.ds_bucket_2)
        s3client.close()

        # Clear out the catalog database
        self.__db_client = pymongo.MongoClient(
            TestCatalogerAWS.db_hostname,
            port=TestCatalogerAWS.db_port,
            username=TestCatalogerAWS.db_username,
            password=TestCatalogerAWS.db_password,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            tlsCAFile=TestCatalogerAWS.db_global_pem,
            directConnection=True,
            retryWrites=False
        )
        self.__db_client.drop_database(TestCatalogerAWS.db_name)

    def tearDown(self) -> None:
        # Delete S3 buckets
        s3client = boto3.client("s3")
        for bucket in (TestCatalogerAWS.ds_bucket_1, TestCatalogerAWS.ds_bucket_2):
            response = s3client.list_objects(Bucket=bucket)
            if 'Contents' in response:
                keys = [content['Key'] for content in response['Contents']]
                s3client.delete_objects(Bucket=bucket,
                                        Delete={
                                            "Objects": [{'Key': key} for key in keys]
                                        })
            s3client.delete_bucket(Bucket=bucket)
            print(f"Deleted bucket {bucket}.")
        s3client.close()

        # Clean up the repository
        self.__db_client.drop_database(TestCatalogerAWS.db_name)
        self.__db_client.close()

    def test_cataloger_aws(self):
        # Test the Ingester implementation with an AWS account

        # Start the s3 client
        s3client = boto3.client('s3')

        # Instantiate a repository instance
        repository = DataSetRepository(db_client=self.__db_client, db=TestCatalogerAWS.db_name)

        # Generate a couple of Datasets that will go into the repository, for generating Catalog files
        ds1 = DataSet(dataset_id="DS1", index="s3://" + TestCatalogerAWS.ds_bucket_1 + "/DS1", title="DataSet1")
        ds2 = DataSet(dataset_id="DS2", index="s3://" + TestCatalogerAWS.ds_bucket_1 + "/DS2", title="DataSet2")
        ds3 = DataSet(dataset_id="DS3", index="s3://" + TestCatalogerAWS.ds_bucket_1 + "/DS3", title="DataSet3")
        ds4 = DataSet(dataset_id="DS4", index="s3://" + TestCatalogerAWS.ds_bucket_2 + "/DS4", title="DataSet4")
        ds5 = DataSet(dataset_id="DS5", index="s3://" + TestCatalogerAWS.ds_bucket_2 + "/DS5", title="DataSet5")
        ds6 = DataSet(dataset_id="DS6", index="s3://" + TestCatalogerAWS.ds_bucket_2 + "/DS6", title="DataSet6")
        repository.save([ds1, ds2, ds3, ds4, ds5, ds6])

        # Create a cataloger instance and run it
        cataloger = Cataloger(dataset_repository=repository, s3client=s3client)
        cataloger.execute()

        # Pull the catalog.json for each bucket and check it
        response = s3client.get_object(Bucket=TestCatalogerAWS.ds_bucket_1, Key='catalog.json')
        catalog_1to3 = json.load((response['Body']))
        self.assertEqual(catalog_1to3['endpoint'], "s3://"+TestCatalogerAWS.ds_bucket_1)
        self.assertTrue(len(catalog_1to3['catalog']), 3)
        for catalog in catalog_1to3['catalog']:
            self.assertTrue(str(catalog['index']).startswith("s3://"+TestCatalogerAWS.ds_bucket_1))

        response = s3client.get_object(Bucket=TestCatalogerAWS.ds_bucket_2, Key='catalog.json')
        catalog_4to6 = json.load((response['Body']))
        self.assertEqual(catalog_4to6['endpoint'], "s3://"+TestCatalogerAWS.ds_bucket_2)
        self.assertTrue(len(catalog_4to6['catalog']), 3)
        for catalog in catalog_4to6['catalog']:
            self.assertTrue(str(catalog['index']).startswith("s3://"+TestCatalogerAWS.ds_bucket_2))

        # Clean up
        s3client.close()


