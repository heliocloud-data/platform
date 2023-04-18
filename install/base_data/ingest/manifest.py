import boto3
import pandas as pd

from base_data.ingest.exceptions import IngesterException


def get_manifest_from_s3(s3resource: boto3.resource, upload_bucket: str, manifest_key: str) -> pd.DataFrame:
    """
    Retrieves a manifest file from S3, returning it as a list of strings
    """
    if not manifest_key.endswith(".csv"):
        raise IngesterException(f"Expecting .csv extension for manifest file: {manifest_key}.")

    obj = s3resource.Object(bucket_name=upload_bucket, key=manifest_key)
    manifest_lines = []
    for line in obj.get()['Body'].readlines():
        line = str(line).lstrip('b\'')
        line = line.replace('\\n\'', '')
        line = line.strip()
        line = line.split(',')
        manifest_lines.append(line)

    # Build the data frame
    return __build_manifest_df(manifest_lines)


def get_manifest_from_fs(manifest_file: str) -> pd.DataFrame:
    """
    Constructs a manifest instance from a file on the local filesystem
    """
    if not manifest_file.endswith(".csv"):
        raise IngesterException(f"Expecting .csv extension for manifest file: {manifest_file}.")

    # Read the manifest in line by line
    manifest_lines = []
    with open(manifest_file) as manifest:
        for line in manifest:
            manifest_lines.append(line.strip().split(','))

    # Hand it off to build the manifest Dataframe
    return __build_manifest_df(manifest_lines)


def __build_manifest_df(manifest: list[list[str]]) -> pd.DataFrame:
    """
    Return the manifest as a Panda's DataFrame
    """
    # Split the lines and create a data frame
    columns = [column.replace('#', '').strip() for column in manifest[0]]
    manifest_df = pd.DataFrame(columns=columns, data=manifest[1:])

    # Validate the manifest structure
    required_headers = ['time', 's3key', 'filesize']
    # First, confirm all required headers are present
    if not all(header in manifest_df.columns for header in required_headers):
        raise IngesterException("Manifest file is missing one of the required headers: " + str(required_headers)
                                + ".")

    # Check data types of manifest and cast appropriately
    try:
        manifest_df = manifest_df.astype(dtype={
            'time': 'datetime64[ns, UTC]',
            's3key': 'string',
            'filesize': 'int64'
        })
    except ValueError as ex:
        raise IngesterException(str(ex))

    return manifest_df
