"""
AWS Lambda implementation for running the Cataloger service.
"""
import os
import json
from dataclasses import dataclass, field
import boto3
from .aws_utils.lambdas import get_dataset_repository
from .catalog.cataloger import Cataloger, Result


def handler(event, context) -> dict:  # pylint: disable=unused-argument
    """
    Lambda handler function for invoking the Catalog generator
    :param event: n/a, but required by AWS Lambda
    :param context: n/a, but required by AWS Lambda
    :return: dictionary of S3 buckets updated and the number of datasets updated in each
    """

    # Steps:
    # 1 - Create a DataSetRepository instance pointing to the DocumentDB running in this HelioCloud
    # 2 - Instantiate a Cataloger instance
    # 3 - Execute the Cataloger

    # Boto3 session for AWS
    session = boto3.session.Session()

    # DataSetRepository creation
    ds_repo = get_dataset_repository(session=session)

    # Values to use for certain catalog fields
    name = os.environ["CATALOG_NAME"]
    contact = os.environ["CATALOG_CONTACT"]

    # Create and execute a Cataloger
    cataloger = Cataloger(dataset_repository=ds_repo, session=session, name=name, contact=contact)
    results = cataloger.execute()

    # Return the results
    return_dict = {}
    for result in results:
        return_dict[result.endpoint] = result.num_datasets
    return return_dict


@dataclass
class CatalogerResponse:
    """
    Response object for understanding the results of invoking the Cataloger lambda
    """

    is_success = False
    results: list[Result] = field(default_factory=list)  # List of cataloger results
    function_error: str = ""
    error_message: str = ""


def lambda_execute(function_name: str, session: boto3.Session) -> CatalogerResponse:
    """
    Simple wrapper function for invoking the Cataloger lambda remotely and making sense of the
    response received from AWS without having to know the particulars of the boto SDK and AWS
    services API.
    :param session: boto3 session to use for the lambda invocation
    :param function_name: name the Cataloger lambda function is registered under in AWS
    :return: a response object for understanding the results of the lambda invocation
    """

    # Invoke the lambda
    client = session.client("lambda")
    response = client.invoke(FunctionName=function_name)

    # Process the response
    lambda_response = CatalogerResponse()
    if response["StatusCode"] == 200:
        # There was an error
        if "FunctionError" in response:
            lambda_response.is_success = False
            lambda_response.function_error = response["FunctionError"]
            lambda_response.error_message = response["Payload"].read().decode()
        # Invocation worked
        else:
            lambda_response.is_success = True
            # Parse the payload out
            results = json.loads(response["Payload"].read().decode())
            for bucket in results:
                lambda_response.results.append(
                    Result(endpoint=bucket, num_datasets=results[bucket])
                )

    # Failure to invoke the function
    else:
        lambda_response.is_success = False
        lambda_response.function_error = "Failure invoking Cataloger lambda."
        lambda_response.error_message = "Cataloger lambda could not be found/executed."

    return lambda_response
