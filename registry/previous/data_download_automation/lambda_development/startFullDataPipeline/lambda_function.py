import json
import boto3
import urllib.parse


def lambda_handler(event, context):
    # get the object from the event and show its content type
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")

    request_name = key.split("/")[-1].split(".")[0]

    # only run script if file is a 'upload_manifest'
    if "upload_manifest" in request_name:
        state_machine_input = {"request_name": request_name, "bucket": bucket, "key": key}
        try:
            client = boto3.client("stepfunctions")
            response = client.start_execution(
                stateMachineArn="arn:aws:states:us-east-1:006885615091:stateMachine:FullUploadPipelineV2",
                input=json.dumps(state_machine_input),
            )
            return {
                "statusCode": 200,
                "request_name": request_name,
                "bucket": bucket,
                "key": key,
            }
        except Exception as e:
            print(e)
            print("Error fetching object")
            # raise e
