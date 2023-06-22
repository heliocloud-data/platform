# Utilities to help with integration tests
import boto3


def get_ingest_s3_bucket_name(hc_instance: str) -> str:
    """
    Returns the name of the S3 bucket used by the Ingester of the HelioCloud instance

    Parameters:
        hc_instance : name of the HelioCloud instance
    """
    # TODO: Implement
    return "cjeschke-dev-uploads"


def get_registry_s3_buckets(hc_instance: str) -> list[str]:
    """
    Returns the S3 buckets used in the Registry of the provided heliocloud instance

    Parameters:
        hc_instance: name of the HelioCloud instance
    """
    # TODO:  Implement
    return [
        "cjeschke-dev-datasets"
    ]


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

    client = session.client("lambda")
    response = client.list_functions()
    client.close()

    for function in response['Functions']:
        function_name = str(function['FunctionName'])
        if (lambda_name in function_name) and function_name.startswith(hc_instance):
            return function_name
