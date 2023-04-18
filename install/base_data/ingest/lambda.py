
def lambda_handler(event, context):
    """
    AWS Lambda to be invoked on an Ingest event, to load files into the data set registry
    """

    # On Success
    return {
        'statusCode': 200,
        'status': 'Successful ingest!'
    }
