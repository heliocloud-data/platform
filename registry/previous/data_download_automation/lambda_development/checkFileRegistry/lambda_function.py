import json
import boto3
import datetime
from dateutil import parser

# use this function to check that the requested file is not all ready present in the S3 bucket
# after checking the bucket, check the file registry

# establish the s3 client
s3 = boto3.client('s3')

# get the file-registry
db = boto3.resource('dynamodb')
file_reg_table = db.Table('fileRegister')

def check_bucket_register(s3_filename, s3_bucket, source_update):
    # checks the register for the file, if already present compares the file load date
    # with the source update date, this compensates for files being updated without the
    # version number changing
    in_bucket = False
    in_register = False

    s3_response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_filename)
    if 'Contents' in s3_response:
        for obj in s3_response['Contents']:
            if s3_filename == obj['Key']:
                in_bucket = True

    db_response = file_reg_table.get_item(Key={'s3_filekey': s3_filename})
    print(db_response)
    if 'Item' in db_response:
        # compare date of when item was updated (by source) of what is already on S3 with the source update of this most recent file
        source_update_s3dt = parser.parse(db_response['Item']['source_update'])
        source_updatedt = parser.parse(source_update)

        if source_update_s3dt < source_updatedt:  # need to redownload and register
            in_bucket = False
            in_register = False
        else:
            in_register = True

    return in_bucket, in_register


def lambda_handler(event, context):
    # pull the information out of the SQS message
    mission = event['mission']
    spacecraft = event['spacecraft']
    dataset = event['dataset']
    instr = event['instr']
    instr_mode = event['instr_mode']
    level_proc = event['level_proc']
    source = event['source']
    download_url = event['download_url']
    s3_filename = event['s3_filename']
    s3_bucket = event['s3_bucket']
    source_update = event['source_update']

    # determine source type
    link_type = download_url.split(':')[0]
    if 'http' in link_type:
        source_type = 'web'
    elif 's3' in link_type:
        source_type = 's3'
    else:
        source_type = 'NaN' # unsupported source type

    # determine the file extension
    file_type = s3_filename.split('/')[-1].split('.')[-1]

    in_bucket, in_register = check_bucket_register(s3_filename, s3_bucket, source_update)

    file_meta = {
        'dataset': dataset,
        'mission': mission,
        'sc': spacecraft,
        'instr': instr,
        'instr_mode': instr_mode,
        'level_proc': level_proc,
        'source': source,
        'download_url': download_url,
        's3_filename': s3_filename,
        's3_bucket': s3_bucket,
        'file_type': file_type,
        'source_update': source_update,
        'source_type': source_type,
        'in_bucket': in_bucket,
        'in_register': in_register
    }

    return {
        'statusCode': 200,
        'file_meta': file_meta
    }
