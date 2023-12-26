import datetime
import json
import os
import unittest

from registry.lambdas.app.model.dataset import DataSet
from registry.lambdas.client.invoke import (
    get_ingester_function,
    get_cataloger_function,
    CatalogerResponse,
)
from utils import (
    new_boto_session,
    get_hc_instance,
    get_registry_s3_buckets,
    get_ingest_s3_bucket_name,
    list_lambda_function_names,
)


class TestRegistryAWS(unittest.TestCase):
    """
    Full integration test for evaluating a Registry module deployed to an AWS account. Assumes the following:

    - A fully deployed HelioCloud instance with a registry module enabled
    - Access to the instance configuration file for the deployed instance
    - Running this test using AWS admin keys/privileges

    """

    hc_instance = get_hc_instance()

    # Boto3 session to use for AWS calls
    session = new_boto_session(hc_instance)

    registry_bucket = get_registry_s3_buckets(hc_instance=hc_instance)[0]

    ingest_bucket = get_ingest_s3_bucket_name(hc_instance=hc_instance)

    ingest_folder = "upload/"

    # Ingest job path
    ingest_job_subfolder = "upload"

    mms_local_manifest_path = "test/integration/resources/s3/to_upload/MMS/manifest.csv"

    # Get the function names
    ingest_function_name = get_ingester_function(
        hc_instance=hc_instance, region=session.region_name
    )
    cataloger_function_name = get_cataloger_function(
        hc_instance=hc_instance, region=session.region_name
    )

    def setUp(self) -> None:
        # get the name of the ingest bucket and upload our test dataset
        s3client = TestRegistryAWS.session.client("s3")

        # Upload the manifest file to the ingest bucket
        key = TestRegistryAWS.ingest_job_subfolder + "/MMS/manifest.csv"
        print(
            f"Uploading manifest file: {TestRegistryAWS.mms_local_manifest_path} to key: {key} in bucket: {TestRegistryAWS.ingest_bucket}"
        )
        s3client.upload_file(
            Filename=TestRegistryAWS.mms_local_manifest_path,
            Bucket=TestRegistryAWS.ingest_bucket,
            Key=key,
        )

        # Upload test files to the ingest bucket
        to_upload_path = "test/integration/resources/s3/to_upload/"
        for root, dirs, files in os.walk(to_upload_path):
            for filename in files:
                local_path = os.path.join(root, filename)
                key = TestRegistryAWS.ingest_folder + local_path.split(to_upload_path)[1]
                s3client.upload_file(
                    Filename=local_path, Bucket=TestRegistryAWS.ingest_bucket, Key=key
                )
                print(f"\tUploaded file s3://{TestRegistryAWS.ingest_bucket}/{key}.")

        # Create the entries.json to upload (w/ the bucket name)
        # Overwrite the existing entries with existing index
        entry_dataset = DataSet(
            dataset_id="MMS",
            index="s3://" + TestRegistryAWS.registry_bucket + "/MMS",
            title="MMS data",
        )
        entry_dataset.creation = datetime.datetime(
            year=2015, month=9, day=1, hour=1, minute=0, second=0
        )
        entry_dataset.resource = "SPASE-12345678"
        entry_dataset.contact = "Dr. Soandso, ephemerus.soandso@nasa.gov"
        entry_dataset.description = "Data from the Magnetospheric Multiscale Mission run by NASA"
        key = TestRegistryAWS.ingest_job_subfolder + "/entries.json"

        print(f"Creating entries.json at key: {key}")
        s3client.put_object(
            Bucket=TestRegistryAWS.ingest_bucket,
            Key=key,
            Body=json.dumps([entry_dataset.to_serializable_dict()]),
        )
        s3client.close()

    def tearDown(self) -> None:
        """
        Tear down
        """
        s3_client = TestRegistryAWS.session.client("s3")

        # Clear out the ingest bucket upload folder
        response = s3_client.list_objects_v2(
            Bucket=TestRegistryAWS.ingest_bucket, Prefix=TestRegistryAWS.ingest_job_subfolder
        )
        if "Contents" in response:
            keys = [content["Key"] for content in response["Contents"]]
            s3_client.delete_objects(
                Bucket=TestRegistryAWS.ingest_bucket,
                Delete={"Objects": [{"Key": key} for key in keys]},
            )
        print(
            f"Cleared out s3://{TestRegistryAWS.ingest_bucket}/{TestRegistryAWS.ingest_job_subfolder}"
        )

        # Clear out the registry bucket's MMS folder
        response = s3_client.list_objects_v2(Bucket=TestRegistryAWS.registry_bucket, Prefix="MMS/")
        if "Contents" in response:
            keys = [content["Key"] for content in response["Contents"]]
            s3_client.delete_objects(
                Bucket=TestRegistryAWS.registry_bucket,
                Delete={"Objects": [{"Key": key} for key in keys]},
            )
        print(f"Cleared out s3://{TestRegistryAWS.registry_bucket}/MMS")

        # Delete the catalog file
        s3_client.delete_object(Bucket=TestRegistryAWS.registry_bucket, Key="catalog.json")
        print(f"Deleted s3://{TestRegistryAWS.registry_bucket}/catalog.json")
        s3_client.close()

    def test_registry(self):
        """
        End to end test of the Registry module. An example Data Set for ingestion is uploaded, the Ingester
        and Cataloger lambdas invoked, and the Registry S3 buckets checked for the installed DataSet.
        """

        # First, run the Ingester Lambda
        lambda_client = TestRegistryAWS.session.client("lambda")
        payload = {
            "job_folder": TestRegistryAWS.ingest_job_subfolder,
        }

        if TestRegistryAWS.ingest_function_name is None:
            print(f"Unable to locate lambda ingest function for {TestRegistryAWS.hc_instance}")
            list_lambda_function_names(TestRegistryAWS.session)
        else:
            print(f"Running lambda ingest function {TestRegistryAWS.ingest_function_name}")

        print(f"{json.dumps(payload)}")
        response = lambda_client.invoke(
            FunctionName=TestRegistryAWS.ingest_function_name, Payload=json.dumps(payload)
        )
        self.assertEqual(response["StatusCode"], 200)
        print("Ingester lambda ran successfully.")

        # Next, run the Cataloger
        cataloger_response = CatalogerResponse(
            lambda_client.invoke(
                FunctionName=TestRegistryAWS.cataloger_function_name, Payload=json.dumps({})
            )
        )
        print(cataloger_response)
        self.assertTrue(cataloger_response.success)
        print("Cataloger ran successfully.")

        # Now inspect the results
        # (1) Check that the ingest folder is completely empty
        s3_client = TestRegistryAWS.session.client("s3")
        response = s3_client.list_objects_v2(Bucket=TestRegistryAWS.ingest_bucket, Prefix="MMS/")
        self.assertTrue("Contents" not in response)
        print(
            f"Confirmed ingest folder s3://{TestRegistryAWS.ingest_bucket}/"
            f"{TestRegistryAWS.ingest_job_subfolder} is empty."
        )

        response = s3_client.list_objects_v2(Bucket=TestRegistryAWS.registry_bucket)

        # (2) Check registry bucket for the dataset
        # (2a) Open the index file & check the line count
        s3_client.download_file(
            Bucket=TestRegistryAWS.registry_bucket,
            Key="MMS/MMS_2015.csv",
            Filename="/tmp/MMS_2015.csv",
        )
        with open("/tmp/MMS_2015.csv") as registry_index:
            lines = [line for line in registry_index]
            self.assertEqual(len(lines), 5)
        os.remove("/tmp/MMS_2015.csv")
        print(
            f"Confirmed registry index s3://{TestRegistryAWS.registry_bucket}/MMS/MMS_2015.csv "
            f"is correct."
        )

        s3_client.download_file(
            Bucket=TestRegistryAWS.registry_bucket,
            Key="MMS/MMS_2019.csv",
            Filename="/tmp/MMS_2019.csv",
        )
        with open("/tmp/MMS_2019.csv") as registry_index:
            lines = [line for line in registry_index]
            self.assertEqual(len(lines), 3)
        os.remove("/tmp/MMS_2019.csv")
        print(
            f"Confirmed registry index s3://{TestRegistryAWS.registry_bucket}/MMS/MMS_2019.csv "
            f"is correct"
        )

        # (2b) Does every file exist that should?
        manifest_file = open(TestRegistryAWS.mms_local_manifest_path)
        files = [line.split(",")[1] for line in manifest_file if line.startswith("2015")]
        for file in files:
            key = "MMS/" + file
            try:
                response = s3_client.head_object(Bucket=TestRegistryAWS.registry_bucket, Key=key)
            except Exception as e:
                # Couldn't find one of the files
                self.assertTrue(False, msg=str(e))
        print(
            f"Confirmed all files in the manifest are present at "
            f"s3://{TestRegistryAWS.registry_bucket}/MMS"
        )

        # (2c) Does the catalog file exist and is it correct?
        s3_client.download_file(
            Bucket=TestRegistryAWS.registry_bucket, Key="catalog.json", Filename="/tmp/catalog.json"
        )
        with open("/tmp/catalog.json") as catalog_json:
            catalog = json.load(catalog_json)
            self.assertEqual(catalog["endpoint"], f"s3://{TestRegistryAWS.registry_bucket}")
            self.assertIsNotNone(catalog["name"])
            self.assertIsNotNone(catalog["contact"])
            if "catalog" in catalog:
                mms_found = False
                for ds_entry in catalog["catalog"]:
                    if ds_entry["dataset_id"] == "MMS":
                        self.assertTrue(
                            ds_entry["index"], f"s3://{TestRegistryAWS.registry_bucket}/MMS"
                        )
                        self.assertTrue(ds_entry["title"], "MMS data")
                        self.assertTrue(ds_entry["indextype"], "csv")
                        self.assertTrue(ds_entry["resource"], "SPASE-12345678")
                        mms_found = True
                self.assertTrue(mms_found)
            else:
                self.assertTrue(False, msg="Catalog didn't contain catalog element.")
        os.remove("/tmp/catalog.json")
        print(f"Catalog at s3://{TestRegistryAWS.registry_bucket}/catalog.json confirmed correct.")
