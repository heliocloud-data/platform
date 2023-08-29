# Tool for running ingest jobs on a HelioCloud instance
import argparse
import boto3
import json


class IngestRunner(object):
    """
    Runner class to encapsulate invoking the Ingester AWS Lambda installed in a HelioCloud instance.
    Parameters needed are:
    - job folder
    - instance
    """

    def __init__(self):
        # Get the instance name and job folder from the args
        parser = argparse.ArgumentParser(
            prog="HelioCloud Ingest Runner",
            description="Enables manual invocation of the HelioCloud ingest service against a specified folder in a "
            "HelioCloud instance's ingest S3 bucket.",
        )
        parser.add_argument(
            "instance",
            type=str,
            help="Name of the HelioCloud instance whose Ingest service should be run. "
            "This should match the instance configuration used to deploy the "
            "HelioCloud to AWS.",
        )
        parser.add_argument(
            "job_folder",
            type=str,
            help="Name of the folder in the ingest bucket (an AWS S3 bucket) provisioned for the "
            "HelioCloud instance being called.",
        )
        args = parser.parse_args()

        self.__instance = args.instance
        self.__job_folder = args.job_folder
        self.__lambda_client = boto3.Session().client("lambda")

    def __get_function_name(self) -> str:
        """
        Get the handle of the lamdda function to invoke
        :return: the function name of the lambda
        """

        response = self.__lambda_client.list_functions()
        for function in response["Functions"]:
            function_name = str(function["FunctionName"])
            if ("Ingest" in function_name) and function_name.startswith(self.__instance):
                return function_name

    def execute(self) -> None:
        """
        Executes the Ingester Lambda on a specific HelioCloud instance
        :return: nothing
        """
        print(
            f"Invoking the Ingester service on HelioCloud {self.__instance} against folder {self.__job_folder}."
        )

        # Run the Ingester as requested and get the response
        payload = {"job_folder": self.__job_folder}
        response = self.__lambda_client.invoke(
            FunctionName=self.__get_function_name(), Payload=json.dumps(payload)
        )
        status_code = response["StatusCode"]

        # 200 indicates successful invocation of the lambda, but we have to pick apart the response to figure out if
        # the ingester itself ran to completion
        if status_code == 200:
            # There was an error
            if "FunctionError" in response:
                function_error = response["FunctionError"]
                payload_str = response["Payload"].read().decode()
                print(f"Ingester service reported an error: {function_error}")
                print(f"Response payload was:\n {payload_str}")

            # Invocation must have been successful
            else:
                payload_str = response["Payload"].read().decode()
                results = json.loads(payload_str)
                print(
                    f"Ingester service incorporated {results['files_contributed']} "
                    f"files into dataset {results['dataset_updated']}."
                )

        # Different problem in Lambda invocation
        else:
            print("Ingester service could not be invoked.")
            print(response)

        # Close resources
        self.__lambda_client.close()


if __name__ == "__main__":
    IngestRunner().execute()
