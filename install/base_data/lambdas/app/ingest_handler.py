import boto3

from .ingest import utils as utils
from .ingest.entry import get_entry_from_s3
from .ingest.manifest import get_manifest_from_s3
from .ingest.ingester import Ingester
from .registry.repositories import DataSetRepository


def handler(event, context):
    """
    AWS Lambda to be invoked on an Ingest event, to load files into the data set registry
    """

    # From the event, we must get
    # - the upload bucket name
    # - the folder the upload is under
    # - the name of the manifest file
    # - the name the entry.json file

    # Get the upload path,  manifest & entry files
    upload_path = event['upload_path']
    manifest_file_name = event['manifest']
    entry_file_name = event['entry']

    # S3 client for this Lambda invocation
    s3client = boto3.client("s3")

    # Get the Manifest file
    bucket_name = utils.get_bucket_name(upload_path)
    subfolder = utils.get_bucket_subfolder(upload_path)
    manifest_key = subfolder + manifest_file_name
    manifest_df = get_manifest_from_s3(s3client=s3client, bucket_name=bucket_name, manifest_key=manifest_key)

    # Get the bucket name, path & entry file
    entry_key = subfolder + entry_file_name
    entry_dataset = get_entry_from_s3(s3client=s3client, bucket_name=bucket_name, entry_key=entry_key)

    # Instantiate an Ingester instance and execute it
    ingester = Ingester(upload_path=upload_path, manifest_df=manifest_df, entry_dataset=entry_dataset,
                        dataset_repository=DataSetRepository(), s3client=s3client)
    ingester.execute()

    # Clean up
    s3client.close()

    # On Success
    return {
        'statusCode': 200,
        'status': f"Ingest complete!"
    }
