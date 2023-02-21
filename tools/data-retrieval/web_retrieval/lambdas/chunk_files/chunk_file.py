from io import StringIO
import os
import boto3
import pandas as pd
import numpy as np

# set up the s3 bucket where we will receive the event
s3 = boto3.client('s3')


def split_csv(df, chunk_size, bucket, key, request_name):
    '''
    Breaks up the csv file into smaller chunks and writes to a new directory in the S3 bucket
    :param dataframe:
    :return:
    '''
    chunk_list = []
    num_request_items = len(df)  # total number of items being requested
    num_chunks = int(np.ceil(num_request_items / chunk_size))
    chunks = np.array_split(df, num_chunks)
    # write chunks to the S3 bucket

    for i, c in enumerate(chunks):
        chunk_name = request_name + '_chunk' + str(i) + '.csv'
        chunk_key = os.path.join('upload_chunk', chunk_name)
        try:
            save_path = os.path.join('s3://' + bucket, chunk_key)
            print('####')
            print(save_path)
            c.to_csv(save_path, index=False)
            chunk_list.append(chunk_key)
        except:
            print('Could not write object.')

    # convert the chunk list into a dictionary
    chunk_json = []

    for i in chunk_list:
        dict = {}
        dict['chunk'] = i
        dict['request_name'] = request_name
        dict['bucket'] = bucket
        chunk_json.append(dict)
    return chunk_json


def lambda_handler(event, context):
    bucket = event['bucket']
    key = event['key']
    request_name = event['request_name']

    chunk_size = 100  # number of requests to split into each file

    # only run script if file is a 'upload_manifest'
    if 'upload_manifest/' in key:
        try:
            s = s3.get_object(Bucket=bucket, Key=key)
            # load in to a pandas dataframe
            df = pd.read_csv(StringIO(s['Body'].read().decode('utf-8')))

            chunked_files = split_csv(
                df, chunk_size, bucket, key, request_name)
            return {
                'statusCode': 200,
                'request_name': request_name,
                'bucket': bucket,
                'chunked_files': chunked_files
            }
        except Exception as e:
            print(e)
            print("Error fetching object")
            # raise e
