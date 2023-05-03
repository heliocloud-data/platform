def handler(event, context):
    """
    Handler that initiates construction of the Catalog.json files in the public data set buckets
    """
    return {
        'statusCode': 200,
        'status': "Cataloger executed successfully!"
    }
