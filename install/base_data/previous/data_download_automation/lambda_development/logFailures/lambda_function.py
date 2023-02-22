import boto3
from datetime import datetime as dt


db = boto3.resource('dynamodb')
fail_table = db.Table('failUploadRegister')

def write_faildb(meta, err_type, err_cause):
    '''
    Write all meta data about the request to a dynamodb along with the failure log message
    :param meta:
    :return:
    '''

    db_item = {
        'mission': meta['mission'],
        'spacecraft': meta['sc'],
        'dataset': meta['dataset'],
        'instr': meta['instr'],
        'instr_mode': meta['instr_mode'],
        'level_proc': meta['level_proc'],
        'source': meta['source'],
        'download_url': meta['download_url'],
        's3_filekey': meta['s3_filename'],
        's3_bucket': meta['s3_bucket'],
        'source_update': meta['source_update'],
        'upload_date': dt.now().isoformat(),
        'fail_type': err_type,
        'fail_cause': err_cause
    }

    fail_table.put_item(Item=db_item)


def lambda_handler(event, context):
    file_meta = event['file_meta']
    error_type = event['error']['Error']
    error_cause = event['error']['Cause']
    write_faildb(file_meta, error_type, error_cause)

    return{
        'statusCode': 200,
        'file_meta': file_meta,
        'error_type': error_type,
        'error_cause': error_cause
    }