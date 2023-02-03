import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

def check_registry(bucket, key):
    '''
    Check the fileRegistry DynamoDB instance - remove the file if it is already present
    :param s3_bucket:
    :param s3_key:
    :return:
    '''
    filereg_table = dynamodb.Table('fileRegister')
    summary_table = dynamodb.Table('dataSummary')
    response = filereg_table.get_item(
        Key={'s3_filekey': key}
    )

    print(response)

    if 'Item' in response: # should only be one item present in the response
        item = response['Item']
        dataset = item['dataset']
        mission = item['mission']
        start_date = item['start_date']
        end_date = item['end_date']

        # remove the item from the fileRegistry
        filereg_table.delete_item(Key={'s3_filekey': key})

        # determine if this was the last item in the fileregistry for that data product and then remove the
        # summary table object, otherwise delete the summary table entry for this data product

        # query the filereg_table and retrieve the number of objects
        filereg_response = filereg_table.query(
            IndexName='dataset_datesort',
            KeyConditionExpression=Key('dataset').eq(dataset)
        )
        print(filereg_response)

        if 'Items' in filereg_response:
            item_content = filereg_response['Items']

            if item_content: # if there are any contents left in the file registry then update the summary table
                # edit the entry for the summary table item but don't delete the summary table
                summary_response = summary_table.get_item(
                    Key={
                        'mission': mission,
                        'dataset': dataset
                    }
                )
                print(summary_response)

                if 'Item' in summary_response:
                    sum_item = summary_response['Items']
                    # determine if there's been a change in the date range
                    # cannot change the variables -- would have to scan every item in the file register which is not doable
                    if start_date == sum_item['dataset_start']:
                        sum_item['dataset_start'] = end_date
                    elif end_date == sum_item['dataset_end']:
                        sum_item['dataset_end'] = start_date

                    summary_table.put_item(Item=sum_item)

            else:
                print('The last item in the summary table')
                # remove the summary table object because there are no remaining objects in the file register
                summary_table.delete_item(Key={
                    'mission': mission,
                    'dataset': dataset
                })


def lambda_handler(event, context):
    objects = event['Records']
    for obj in objects:
        s3_info = obj['s3']
        s3_bucket = s3_info['bucket']['name']
        s3_key = s3_info['object']['key']

        check_registry(s3_bucket, s3_key)

