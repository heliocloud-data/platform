"""
This module contains a tool for running a HelioCloud instance's Cataloger service from the command
line.
"""
import argparse
import sys
from pathlib import Path

import boto3

# pylint: disable=import-error, wrong-import-position
# The catalog_lambda module is in a separate, top level project directory unaffiliated with tools,
# thus importing it requires updating the sys.path with the project directory.
PROJECT_DIR = str((Path(__file__)).parent.parent)
sys.path.append(PROJECT_DIR)
from registry.lambdas.app.catalog_lambda import lambda_execute

# pylint: enable=import-error, wrong-import-position


class CatalogRunner:  # pylint: disable=too-few-public-methods
    """
    Runner class to encapsulate invoking the Cataloger AWS Lambda installed in a HelioCloud.
    Parameters needed are:
    - instance
    """

    def __init__(self, instance: str, session: boto3.Session):
        """
        Initialize a new CatalogRunner.
        :param instance: name of the HelioCloud instance to invoke the Cataloger service on
        :param session: boto3 session to use for calling the AWS API
        """

        self.__instance = instance
        self.__boto_session = session

    def __get_function_name(self) -> str:
        """
        Get the handle of the lambda function to invoke based on the HelioCloud instance name
        :return: the AWS function name of the Cataloger lambda
        """

        client = self.__boto_session.client("lambda")
        response = client.list_functions()

        # find the name
        name = ""
        for function in response["Functions"]:
            function_name = str(function["FunctionName"])
            # AWS CDK/Cloudformation removes hyphens from instance names
            instance_aws_name = self.__instance.replace("-", "")
            if ("Cataloger" in function_name) and function_name.startswith(instance_aws_name):
                name = function_name

        client.close()
        # need to remove any hyphens because of how AWS id generation works
        return name

    def execute(self) -> bool:
        """
        Executtes the Cataloger lambda on a specified HelioCloud instance
        :return: True if successful, else False
        """
        print(f"Invoking the Cataloger service on HelioCloud {self.__instance}.")

        # Execute the lambda for the Cataloger service
        response = lambda_execute(
            function_name=self.__get_function_name(), session=self.__boto_session
        )

        # Successful lambda invocation
        if response.is_success:
            if len(response.results) == 0:
                print("No dataset entry updates in catalog.json were necessary.")
            else:
                for result in response.results:
                    print(
                        f"S3 bucket {result.endpoint} updated {result.num_datasets} dataset "
                        f"entries."
                    )
            return True

        # Something failed
        print(f"Function error: {response.function_error}")
        print(f"Error message: {response.error_message}")
        return False


if __name__ == "__main__":
    # Require an instance name argument
    parser = argparse.ArgumentParser(
        prog="HelioCloud Cataloger Service Runner",
        description="Runs a HelioCloud instance's cataloger service to generate catalog.json "
        "files for the registry S3 buckets.",
    )
    parser.add_argument(
        "instance",
        type=str,
        help="Name of the HelioCloud instance whose Cataloger service should be run. "
        "This should match the instance configuration used to deploy the "
        "HelioCloud to AWS.",
    )
    args = parser.parse_args()

    # Run the Cataloger service
    runner = CatalogRunner(instance=args.instance, session=boto3.Session())
    if runner.execute():
        print("Cataloger service ran successfully.")
    else:
        print("Cataloger service failed!")
