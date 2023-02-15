import json
import boto3
import os
import urllib.parse


def lambda_handler(event, context):

    # get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'],
                                    encoding='utf-8')

    request_name = key.split('/')[-1].split('.')[0]

    # Get environment variables passed to lambda in stack
    state_machine_arn = os.environ.get('STEPFUNCTION_ARN')

    print(key)
    print(request_name)
    print('*****')
    # TODO requirement that within upload_manifest folder
    #  only run script if file is a 'upload_manifest'
    if 'upload_manifest/' in key:
        state_machine_input = {
            'request_name': request_name,
            'bucket': bucket,
            'key': key
        }
        print(state_machine_arn)
        print(bucket, key)
        try:
            client = boto3.client('stepfunctions')
            response = client.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps(state_machine_input)
            )
            print('success')
            return {
                'statusCode': 200,
                'request_name': request_name,
                'bucket': bucket,
                'key': key,
            }
        except Exception as e:
            print(e)
            print("Error fetching object")
            # raise e


