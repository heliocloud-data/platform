import boto3
import datetime
import json
import os
import unittest

from registry.lambdas.app.model.dataset import DataSet
from utils import (
    get_lambda_function_name,
    get_registry_s3_buckets,
    get_ingest_s3_bucket_name
)


class TestRegistryAWS(unittest.TestCase):
    """
    Full integration test for evaluating a Registry module deployed to an AWS account. Assumes the following:

    - A fully deployed HelioCloud instance with a registry module enabled
    - Access to the instance configuration file for the deployed instance
    - Running this test using AWS admin keys/privileges

    """

    # Boto3 session to use for AWS calls
    session = boto3.session.Session()

    # TODO:  Get these from the instance config
    registry_bucket = get_registry_s3_buckets(hc_instance="cjeschke-dev")[0]

    # TODO: Get these from the instance config
    ingest_bucket = get_ingest_s3_bucket_name(hc_instance="cjeschke-dev")

    # Ingest job path
    ingest_job_subfolder = "upload/"

    # Get the function names
    ingest_function_name = get_lambda_function_name(session=session, hc_instance="cjeschkedev",
                                                    lambda_name="Ingester")
    cataloger_function_name = get_lambda_function_name(session=session, hc_instance="cjeschkedev",
                                                       lambda_name="Cataloger")

    def setUp(self) -> None:
        # get the name of the ingest bucket and upload our test dataset
        s3client = TestRegistryAWS.session.client('s3')

        # Upload the manifest file to the ingest bucket
        manifest_file = "test/integration/resources/s3/manifest.csv"
        key = TestRegistryAWS.ingest_job_subfolder + "/manifest.csv"
        print(f"Uploading manifest file: {manifest_file} to key: {key}")
        s3client.upload_file(Filename=manifest_file, Bucket=TestRegistryAWS.ingest_bucket, Key=key)

        # Upload test files to the ingest bucket
        for entry in os.scandir("test/integration/resources/s3"):
            key = TestRegistryAWS.ingest_job_subfolder

            # Only process mms1 files & the valid manifest
            if entry.name.startswith("mms1_fgm") and entry.is_file():
                if entry.name.startswith("mms1_fgm_brst_l2_20150901"):
                    key += "mms1/fgm/brst/l2/2015/09/01/"
                if entry.name.startswith("mms1_fgm_brst_l2_20150902"):
                    key += "mms1/fgm/brst/l2/2015/09/02/"
                if entry.name.startswith("mms1_fgm_brst_l2_20191130"):
                    key += "mms1/fgm/brst/l2/2019/11/30/"
                key += entry.name

                # Upload the file
                print(f"Uploading file: {entry.name} to key: {key}")
                s3client.upload_file(Filename=entry.path, Bucket=TestRegistryAWS.ingest_bucket,
                                     Key=key)

        # Upload entry and manifest files to the ingest bucket
        key = TestRegistryAWS.ingest_job_subfolder + "manifest.csv"
        print(f"Uploading file: manifest.csv to key: {key}")
        s3client.upload_file(Filename="test/integration/resources/s3/manifest.csv",
                             Bucket=TestRegistryAWS.ingest_bucket,
                             Key=key)

        # Create the entry.json to upload (w/ the bucket name)
        entry_dataset = DataSet(dataset_id="MMS", index="s3://" + TestRegistryAWS.registry_bucket + "/MMS",
                                title="MMS data")
        entry_dataset.creation = datetime.datetime(year=2015, month=9, day=1, hour=1, minute=0, second=0)
        entry_dataset.resource = "SPASE-12345678"
        entry_dataset.contact = "Dr. Soandso, ephemerus.soandso@nasa.gov"
        entry_dataset.description = "Data from the Magnetospheric Multiscale Mission run by NASA"
        key = TestRegistryAWS.ingest_job_subfolder + "entry.json"
        print(f"Creating entry.json at key: {key}")
        s3client.put_object(Bucket=TestRegistryAWS.ingest_bucket, Key=key,
                            Body=entry_dataset.to_json())
        s3client.close()

    def tearDown(self) -> None:
        """
        Tear down
        """
        s3_client = TestRegistryAWS.session.client("s3")

        # Clear out the ingest bucket upload folder
        response = s3_client.list_objects_v2(Bucket=TestRegistryAWS.ingest_bucket,
                                             Prefix=TestRegistryAWS.ingest_job_subfolder)
        if 'Contents' in response:
            keys = [content['Key'] for content in response['Contents']]
            s3_client.delete_objects(Bucket=TestRegistryAWS.ingest_bucket,
                                     Delete={
                                         "Objects": [{"Key": key} for key in keys]
                                     })
        print(f"Cleared out s3://{TestRegistryAWS.ingest_bucket}/{TestRegistryAWS.ingest_job_subfolder}")

        # Clear out the registry bucket's MMS folder
        response = s3_client.list_objects_v2(Bucket=TestRegistryAWS.registry_bucket, Prefix="MMS/")
        if 'Contents' in response:
            keys = [content['Key'] for content in response['Contents']]
            s3_client.delete_objects(Bucket=TestRegistryAWS.registry_bucket,
                                     Delete={
                                         "Objects": [{"Key": key} for key in keys]
                                     })
        print(f"Cleared out s3://{TestRegistryAWS.registry_bucket}/MMS")

        # Delete the catalog file
        s3_client.delete_object(Bucket=TestRegistryAWS.registry_bucket, Key="catalog.json")
        print(f"Deleted s3://{TestRegistryAWS.registry_bucket}/catalog.json")
        s3_client.close()

    def test_registry(self):
        """
        End to end test of the Registry module. An example Data Set for ingestion is uploaded, the Ingester
        and Cataloger lambdas invokved, and the Registry S3 buckets checked for the installed DataSet.
        """

        # First, run the Ingester Lambda
        lambda_client = TestRegistryAWS.session.client("lambda")
        payload = {
            "ingest_bucket": TestRegistryAWS.ingest_bucket,
            "ingest_folder": TestRegistryAWS.ingest_job_subfolder,
        }
        response = lambda_client.invoke(FunctionName=TestRegistryAWS.ingest_function_name, Payload=json.dumps(payload))
        self.assertEqual(response['StatusCode'], 200)
        print("Ingester lambda ran successfully.")

        # Next, run the Cataloger
        response = lambda_client.invoke(FunctionName=TestRegistryAWS.cataloger_function_name)
        self.assertEqual(response['StatusCode'], 200)
        lambda_client.close()
        print("Cataloger lambda ran successfully.")

        # Now inspect the results

        # (1) Check that the ingest folder is completely empty
        s3_client = TestRegistryAWS.session.client("s3")
        response = s3_client.list_objects_v2(Bucket=TestRegistryAWS.ingest_bucket, Prefix="MMS/")
        self.assertTrue("Contents" not in response)
        print(f"Confirmed ingest folder s3://{TestRegistryAWS.ingest_bucket}/{TestRegistryAWS.ingest_job_subfolder} "
              f"is empty.")

        # (2) Check registry bucket for the dataset
        # (2a) Open the index file & check the line count
        s3_client.download_file(Bucket=TestRegistryAWS.registry_bucket, Key="MMS/MMS_2015.csv",
                                Filename="/tmp/MMS_2015.CSV")
        with open("/tmp/MMS_2015.csv") as registry_index:
            lines = [line for line in registry_index]
            self.assertEqual(len(lines), 5)
        os.remove("/tmp/MMS_2015.csv")
        print(f"Confirmed registry index s3://{TestRegistryAWS.registry_bucket}/MMS/MMS_2015.csv is correct.")

        s3_client.download_file(Bucket=TestRegistryAWS.registry_bucket, Key="MMS/MMS_2019.csv",
                                Filename="/tmp/MMS_2019.csv")
        with open("/tmp/MMS_2019.csv") as registry_index:
            lines = [line for line in registry_index]
            self.assertEqual(len(lines), 3)
        os.remove("/tmp/MMS_2019.csv")
        print(f"Confirmed registry index s3://{TestRegistryAWS.registry_bucket}/MMS/MMS_2019.csv is correct")

        # (2b) Does every file exist that should?
        manifest_file = open("test/integration/resources/s3/manifest.csv")
        files = [line.split(',')[1] for line in manifest_file if line.startswith("2015")]
        for file in files:
            key = "MMS/" + file
            try:
                response = s3_client.head_object(Bucket=TestRegistryAWS.registry_bucket, Key=key)
            except Exception as e:
                # Couldn't find one of the files
                self.assertTrue(False, msg=str(e))
        print(f"Confirmed all files in the manifest are present at s3://{TestRegistryAWS.registry_bucket}/MMS")

        # (2c) Does the catalog file exist and is it correct?
        s3_client.download_file(Bucket=TestRegistryAWS.registry_bucket, Key="catalog.json",
                                Filename="/tmp/catalog.json")
        with open("/tmp/catalog.json") as catalog_json:
            catalog = json.load(catalog_json)
            self.assertEqual(catalog['endpoint'], f"s3://{TestRegistryAWS.registry_bucket}")
            if 'catalog' in catalog:
                mms_found = False
                for ds_entry in catalog['catalog']:
                    if ds_entry['dataset_id'] == 'MMS':
                        self.assertTrue(ds_entry['index'], f"s3://{TestRegistryAWS.registry_bucket}/MMS")
                        self.assertTrue(ds_entry['title'], "MMS data")
                        self.assertTrue(ds_entry['indextype'], "csv")
                        self.assertTrue(ds_entry['resource'], "SPASE-12345678")
                        mms_found = True
                self.assertTrue(mms_found)
            else:
                self.assertTrue(False, msg="Catalog didn't contain catalog element.")
        os.remove("/tmp/catalog.json")
        print(f"Catalog at s3://{TestRegistryAWS.registry_bucket}/catalog.json confirmed correct.")
