from decimal import Decimal
from io import BytesIO
import json
import logging
import os
from pprint import pprint
import requests
from zipfile import ZipFile
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def exists(session, table_name):
    """
    Determines whether a table exists. As a side effect, stores the table in
    a member variable.
    :param table_name: The name of the table to check.
    :return: True when the table exists; otherwise, False.
    """
    exists = False
    try:
        tables = session.list_tables()['TableNames']
        if table_name in tables:
            exists = True
            print('Table already exists in the account!')
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            exists = False
        else:
            logger.error(
                "Couldn't check for existence of %s. Here's why: %s: %s",
                table_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
    return exists


def create_fileregister_table(session, table_name, units):
    """
    Creates an Amazon DynamoDB table that can be used to store movie data.
    The table uses the release year of the movie as the partition key and the
    title as the sort key.
    :param table_name: The name of the table to create.
    :return: The newly created table.
    """
    try:
        table = session.create_table(
            AttributeDefinitions=[ # describes only the attributes that are used for the key schema of the table
                {
                    'AttributeName': 's3_filekey', # primary partition key - where the file is located in S3
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'dataset', # dataset descriptor, e.g. mms1_fgm_l2_srvy
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'start_date', # iso-8601 string describing the start time of the data file
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'mission', # describes which mission/system the data belongs to
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'instrument', # describes the instrument the data belongs to
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'level_processing', # the level of processing for the data
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'date_upload', # the date the data was uploaded/registered
                    'AttributeType': 'S'
                }
            ],
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 's3_filekey',
                 'KeyType': 'HASH'},  # Primary partition key
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'dataset_datesort', # grabs all data within a 'dataset' and sorts by date
                    'KeySchema': [
                         {
                             'AttributeName': 'dataset',
                             'KeyType': 'HASH',
                         },
                         {
                             'AttributeName': 'start_date',
                             'KeyType': 'RANGE'
                         }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': units,
                        'WriteCapacityUnits': units
                    }
                 },
                {
                    'IndexName': 'dataset_uploadsort', # grabs all data within a 'dataset' and sorts by the upload date
                    'KeySchema': [
                        {
                            'AttributeName': 'dataset',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'date_upload',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': units,
                        'WriteCapacityUnits': units
                    }
                },
                {
                    'IndexName': 'mission_id',
                    'KeySchema': [
                        {
                            'AttributeName': 'mission',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'start_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': units,
                        'WriteCapacityUnits': units
                    }
                },
                {
                    'IndexName': 'instr_id',
                    'KeySchema': [
                        {
                            'AttributeName': 'instrument',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'start_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': units,
                        'WriteCapacityUnits': units
                    }
                },
                {
                    'IndexName': 'level_id',
                    'KeySchema': [
                        {
                            'AttributeName': 'level_processing',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'start_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': units,
                        'WriteCapacityUnits': units
                    }
                }
            ],

            ProvisionedThroughput={'ReadCapacityUnits': units, 'WriteCapacityUnits': units})
        # table.wait_until_exists()
    except ClientError as err:
        logger.error(
            "Couldn't create table %s. Here's why: %s: %s", table_name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        return table

def create_datasummary_table(session, table_name, units):
    '''
    Will create a higher level table describing the data in the lower level file registry
    Will have significantly less entries so we can easily list all the contents for a given mission
    :param session:
    :param tablename:
    :return:
    '''
    try:
        table = session.create_table(
            AttributeDefinitions=[ # describes only the attributes that are used for the key schema of the table
                {
                    'AttributeName': 'mission', # <mission>_<sc>, if no sc, then just <mission>
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'instrument', # lists all the instruments
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'dataset', # dataset descriptor (same as the fileRegister dynamoDB)
                    'AttributeType': 'S'
                }
            ],
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'mission',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'dataset',
                    'KeyType': 'RANGE'
                }
            ],
            LocalSecondaryIndexes=[
                {
                    'IndexName': 'mission_instr',
                    'KeySchema': [
                         {
                             'AttributeName': 'mission',
                             'KeyType': 'HASH',
                         },
                         {
                             'AttributeName': 'instrument',
                             'KeyType': 'RANGE'
                         }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                 }
                ],
            ProvisionedThroughput={'ReadCapacityUnits': units, 'WriteCapacityUnits': units})
        # table.wait_until_exists()
    except ClientError as err:
        logger.error(
            "Couldn't create table %s. Here's why: %s: %s", table_name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        return table

def create_failure_table(session, table_name, units):
    '''
    Writes all failed data uploads ot a Dynamo instance
    :param session:
    :param tablename:
    :return:
    '''
    try:
        table = session.create_table(
            AttributeDefinitions=[ # describes only the attributes that are used for the key schema of the table
                {
                    'AttributeName': 's3_filekey', # lists all the instruments
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'dataset',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'upload_date', # dataset descriptor (same as the fileRegister dynamoDB)
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'fail_type', # what type of failure occured
                    'AttributeType': 'S'
                }
            ],
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 's3_filekey',
                    'KeyType': 'HASH'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'dataset_datesort',  # grabs all data within a 'dataset' and sorts by date
                    'KeySchema': [
                        {
                            'AttributeName': 'dataset',
                            'KeyType': 'HASH',
                        },
                        {
                            'AttributeName': 'upload_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': units,
                        'WriteCapacityUnits': units
                    }
                },
                {
                    'IndexName': 'fail_sort',  # grabs all the data with a particular fail type (do not add the fail cause)
                    'KeySchema': [
                        {
                            'AttributeName': 'fail_type',
                            'KeyType': 'HASH',
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': units,
                        'WriteCapacityUnits': units
                    }
                }
            ],
            ProvisionedThroughput={'ReadCapacityUnits': units, 'WriteCapacityUnits': units})
        # table.wait_until_exists()
    except ClientError as err:
        logger.error(
            "Couldn't create table %s. Here's why: %s: %s", table_name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        return table

if __name__ == '__main__':
    session = boto3.Session(profile_name='006885615091_CT-PowerUser-HelioCloud', region_name='us-east-1')
    db = session.client('dynamodb', use_ssl=True, verify='/Users/yeakekl2/root_certificate.pem')
    read_write_units = 10 # the read/write capacity for the table - weighs heavily on the cost of the table

    if not exists(db, 'fileRegister'):
        create_fileregister_table(db, 'fileRegister', read_write_units)
    if not exists(db, 'dataSummary'):
        create_datasummary_table(db, 'dataSummary', read_write_units)
    if not exists(db, 'failUploadRegister'):
        create_failure_table(db, 'failUploadRegister', 5)