import os

import boto3

from .aws_utils.document_db import get_documentdb_client
from .aws_utils.s3 import get_manifest_from_s3
from .aws_utils.s3 import get_dataset_entry_from_s3
from .ingest.ingester import Ingester
from .repositories import DataSetRepository


def handler(event, context):
    """
    AWS Lambda to be invoked on an Ingest event, to load files into the data set registry

    Parameters:
        event: must be populated with the name of the AWS s3 bucket & folder containing the dataset to ingest
        context:
    """
    session = boto3.session.Session()

    # Get the Ingest bucket name & folder
    ingest_bucket = event['ingest_bucket']
    ingest_folder = str(event['ingest_folder'])
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
    ingester.execute()

    # Remove the entry & manifest files
    s3_client = session.client("s3")
    s3_client.delete_object(Bucket=ingest_bucket, Key=manifest_key)
    s3_client.delete_object(Bucket=ingest_bucket, Key=entry_key)
    s3_client.close()

    # On Success
    return {
        'statusCode': 200,
        'status': f"Ingest complete!"
    }
