# Utilities to help with integration tests
import boto3
import os

from app_config import load_configs

# The default HC instance name.
DEFAULT_HC_INSTANCE="example"

def get_hc_instance() -> str:
    ret = os.environ['HC_INSTANCE']
    if ret is None or len(ret) == 0:
        ret = DEFAULT_HC_INSTANCE

    return ret

def get_ingest_s3_bucket_name(hc_instance: str) -> str:
    """
    Returns the name of the S3 bucket used by the Ingester of the HelioCloud instance

    Parameters:
        hc_instance : name of the HelioCloud instance
    """

    cfg = load_configs(hc_id=hc_instance)
    return cfg['registry']['ingestBucketName']


def get_registry_s3_buckets(hc_instance: str) -> list[str]:
    """
    Returns the S3 buckets used in the Registry of the provided heliocloud instance

    Parameters:
        hc_instance: name of the HelioCloud instance
    """

    cfg = load_configs(hc_id=hc_instance)
    return cfg['registry']['datasetBucketNames']

def remove_file_if_exists(filename: str) -> bool:
    ret = False

    if os.path.exists(filename):
        os.remove(filename)
        ret = True

    return ret

def get_lambda_function_name(session: boto3.Session, hc_instance: str, lambda_name: str) -> str:
    """
    Gets the name of a particular lambda function in AWS based on the HelioCloud instance name and the
    name of the lambda in the codebase.
    Note:  Fuzzy, imperfect search right now...

    Parameters:
        session: a configured Boto3 session instance to use
        hc_instance:  name of the HelioCloud instance
        lambda_name:  name of the Lambda to look up (as registered in the CDK)
    """

    # Derive the starting characters of the function name, which as far as I know,
    # simply drops any hyphen characters from the heliocloud instance name.
    function_name_starts_with = hc_instance.replace('-', '')

    client = session.client("lambda")
    response = client.list_functions()
    client.close()

    for function in response['Functions']:
        function_name = str(function['FunctionName'])

        if (lambda_name in function_name) and function_name.startswith(function_name_starts_with):
            return function_name
