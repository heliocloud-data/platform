def lambda_handler(event, context):
    file_meta = event["file_meta"]
    error_type = event["error"]["Error"]
    error_cause = event["error"]["Cause"]

    return {
        "statusCode": 200,
        "file_meta": file_meta,
        "error_type": error_type,
        "error_cause": error_cause,
    }
