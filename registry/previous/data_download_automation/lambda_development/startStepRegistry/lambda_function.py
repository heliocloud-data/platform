import json
import boto3


def lambda_handler(event, context):
    message = event["Records"][0]["body"]
    print(json.loads(message))

    # message = event['Records'][0]['messageAttributes']

    client = boto3.client("stepfunctions")

    response = client.start_execution(
        stateMachineArn="arn:aws:states:us-east-1:006885615091:stateMachine:DataUploadRegister",
        input=message,
    )
