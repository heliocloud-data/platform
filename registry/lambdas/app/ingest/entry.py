import boto3
import json

from .exceptions import IngesterException
from ..model.dataset import DataSet


def get_entry_from_s3(s3client: boto3.client, bucket_name: str, entry_key: str) -> DataSet:
    """
    Load the entry.json file from an S3 location, returning a DataSet instance.
    """
    if not entry_key.endswith(".json"):
        raise IngesterException(f"Expecting .csv extension for manifest file: {entry_key}.")

    response = s3client.get_object(Bucket=bucket_name, Key=entry_key)
    data = json.load(response["Body"])
    return DataSet.from_serialized_dict(data)


def get_entry_from_fs(filename: str) -> DataSet:
    """
    Load the entry.json file from the local file system, returning a DataSet instance.
    """
    # Check file extension
    if not filename.endswith("json"):
        raise IngesterException(
            "Upload entry file " + filename + " does not have a JSON extension."
        )

    data = dict()
    with open(filename) as entry_f:
        data = json.load(entry_f)
    return DataSet.from_serialized_dict(data)
