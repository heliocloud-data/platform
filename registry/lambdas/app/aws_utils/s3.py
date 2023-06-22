import boto3
import json
import pandas as pd

from boto3.session import Session
from ..ingest.manifest import build_manifest_df
from ..model.dataset import DataSet
from ..exceptions import RegistryException


def get_dataset_entry_from_s3(session: Session, bucket_name: str, entry_key: str) -> DataSet:
    """
    Load the entry.json file from an S3 location, returning a DataSet instance.

    Parameters:
        session: boto3 session to use for connecting to S3
        bucket_name: name of the AWS s3 bucket
        entry_key: AWS s3 key of the entry dataset file (should end in .json)
    """
    if not entry_key.endswith(".json"):
        raise RegistryException(f"Expecting .json extension for dataset file: {entry_key}.")

    response = session.client("s3").get_object(Bucket=bucket_name, Key=entry_key)
    data = json.load(response['Body'])

    # Correction for id field used in the JSON form
    data['dataset_id'] = data['id']
    return DataSet.from_serialized_dict(data)


def get_manifest_from_s3(session: Session, bucket_name: str, manifest_key: str) -> pd.DataFrame:
    """
    Retrieves a manifest file from AWS S3, returning as a Pandas DataFrame

    Parameters:
        session: boto3 session to use for connecting to AWS s3
        bucket_name:  name of the AWS S3 bucket
        manifest_key:  name of the manifest file (ex: manifest.csv)
    """
    if not manifest_key.endswith(".csv"):
        raise RegistryException(f"Expecting .csv extension for manifest file: {manifest_key}.")

    response = session.client("s3").get_object(Bucket=bucket_name, Key=manifest_key)
    manifest_lines = []
    for line in response['Body'].readlines():
        # Strip leading 'b in the stream
        line = str(line).lstrip('b\'')

        # Strip trailing ' and \n
        line = line.rstrip("'")
        line = line.rstrip("\\n")

        line = line.split(',')
        if len(line) == 3:
            manifest_lines.append(line)

    # Build the data frame
    return build_manifest_df(manifest_lines)


def get_s3_bucket_name(uri: str) -> str:
    """
    Return the name of the bucket given a full S3 uri such as s3://my.bucket.name/content

    Parameters:
        uri : an s3:// uri
    """
    return uri.split("/")[2]


def get_s3_bucket_subfolder(uri: str) -> str:
    """
    Gets the sub folder within an S3 URI (everything after the bucket name)

    Parameters:
        uri : an s3:// uri
    """
    return "/".join(uri.split("/", )[3:], )


def get_bucket_name(path: str) -> str:
    """
    Gets the name of the S3 bucket. Assumes names start with one of:
    - file://
    - s3://

    Parameters:
        path : path to get the bucket name from
    """
    return path.split("/")[2]


def get_bucket_subfolder(path: str) -> str:
    """
    Gets the sub folder within the bucket (everything after the bucket name). Assumes paths starting with:
    - file://
    - s3://
    """
    return "/".join(path.split("/", )[3:], )
