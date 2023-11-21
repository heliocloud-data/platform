"""
AWS Lambda implementation for running the Ingester service.
"""
import os

import boto3

from .aws_utils.lambdas import get_dataset_repository
from .aws_utils.s3 import get_dataset_entries_from_s3
from .aws_utils.s3 import get_manifest_from_s3
from .ingest.ingester import Ingester


def handler(event, context) -> dict:
    # pylint: disable=unused-argument
    # context argument is required by AWS lambda service
    """
    AWS Lambda handler for the Ingest service of HelioCloud.

    :param event: must contain the parameter 'job_folder' with its value (the folder in the ingest
        bucket to check for the ingest job
    :param context: n/a (required for method signature)
    :return: a dictionary containing two keys
             dataset_updated:  the name of the dataset in this HelioCloud's catalog that was
             updated by the job
             files_contributed:  the number of files contributed to that dataset
    """

    session = boto3.session.Session()

    # Get the Ingest bucket name & folder
    ingest_bucket = os.environ["ingest_bucket"]
    ingest_folder = str(event["job_folder"])

    # Get the entries dataset
    entry_key = os.path.join(ingest_folder, "entries.json")
    entry_ds_list = get_dataset_entries_from_s3(
        session=session, bucket_name=ingest_bucket, entry_key=entry_key
    )

    # Get the manifest for each entry
    results = []
    s3_client = session.client("s3")
    for entry_ds in entry_ds_list:
        # join ingest folder (ex. my_job/), index split (ex. MMS/), and manifest.csv
        manifest_key = os.path.join(ingest_folder, entry_ds.index.rsplit("/", 1)[1], "manifest.csv")

        manifest_df = get_manifest_from_s3(
            session=session, bucket_name=ingest_bucket, manifest_key=manifest_key
        )

        ingester = Ingester(
            session=session,
            ingest_bucket=ingest_bucket,
            ingest_folder=ingest_folder,
            entry_dataset=entry_ds,
            manifest_df=manifest_df,
            ds_repo=get_dataset_repository(),
        )
        results.append(ingester.execute())

        s3_client.delete_object(Bucket=ingest_bucket, Key=manifest_key)

    # Remove the entries file
    s3_client.delete_object(Bucket=ingest_bucket, Key=entry_key)
    s3_client.close()

    # Information to return back in the Lambda response payload stream

    updates = {
        "datasets_updated": [],
        "files_contributed": [],
    }

    for result in results:
        updates["datasets_updated"].append(result.dataset_updated)
        updates["files_contributed"].append(result.files_contributed)

    return updates


# pylink: enable=unused-argument
