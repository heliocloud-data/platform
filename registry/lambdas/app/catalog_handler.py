import boto3

from .registry.cataloger import Cataloger


def handler(event, context):
    """
    Handler that initiates construction of the Catalog.json files in the public data set buckets
    """
    s3client = boto3.client("s3")

    # Generate the Catalog JSON files
    cataloger = Cataloger(s3client=s3client, dbhandle=None)
    cataloger.execute()

    return {
        'statusCode': 200,
        'status': "Not much going on here yet."
    }
