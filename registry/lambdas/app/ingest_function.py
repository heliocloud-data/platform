import os

import boto3

from .aws_utils.document_db import get_documentdb_client
from .aws_utils.s3 import get_dataset_entry_from_s3
from .aws_utils.s3 import get_manifest_from_s3
from .ingest.ingester import Ingester
from .repositories import DataSetRepository


def handler(event, context) -> dict:
    """
    AWS Lambda handler for the Ingest service of HelioCloud.

    :param event: must contain the parameter 'job_folder' with its value (the folder in the ingest bucket to check
                  for the ingest job
    :param context: n/a (required for method signature)
    :return: a dictionary containing two keys
             dataset_updated:  the name of the dataset in this HelioCloud's catalog that was updated by the job
             files_contributed:  the number of files contributed to that dataset
    """
    session = boto3.session.Session()

    # Get the Ingest bucket name & folder
    ingest_bucket = os.environ['ingest_bucket']
    ingest_folder = str(event['job_folder'])
    if not ingest_folder.endswith("/"):
        ingest_folder += "/"

    # Get the manifest
    manifest_key = ingest_folder + "manifest.csv"
    manifest_df = get_manifest_from_s3(session=session, bucket_name=ingest_bucket, manifest_key=manifest_key)

    # Get the entry dataset
    entry_key = ingest_folder + "entry.json"
    entry_ds = get_dataset_entry_from_s3(session=session, bucket_name=ingest_bucket, entry_key=entry_key)

    # Get a handle to the Catalog DB
    catalog_db_secret = os.environ['CATALOG_DB_SECRET']
    db_client = get_documentdb_client(session=session, secret_name=catalog_db_secret,
                                      tlsCAFile=os.path.dirname(__file__) + "/resources/global-bundle.pem")
    ds_repo = DataSetRepository(db_client=db_client)

    # Instantiate an Ingester instance and execute it
    ingester = Ingester(session=session, ingest_bucket=ingest_bucket, ingest_folder=ingest_folder,
                        entry_dataset=entry_ds,
                        manifest_df=manifest_df, ds_repo=ds_repo)
    results = ingester.execute()

    # Remove the entry & manifest files
    s3_client = session.client("s3")
    s3_client.delete_object(Bucket=ingest_bucket, Key=manifest_key)
    s3_client.delete_object(Bucket=ingest_bucket, Key=entry_key)
    s3_client.close()

    # Information to return back in the Lambda response payload stream
    return {
        "dataset_updated": results.dataset_updated,
        "files_contributed": results.files_contributed
    }
