import boto3
import json
import pymongo
from botocore.exceptions import ClientError


def get_documentdb_client(session: boto3.session.Session, secret_name: str, tlsCAFile: str, local=False) -> pymongo.MongoClient:
    """
    Given an AWS Secret name and a PEM file, construct and return a MongoClient instance
    connected to a DocumentDB instance at hostname

    Parameters:
        session: boto3 session to use for accessing AWS services
        secret_name: name of the secret in AWS Secrets Manager containing DocumentDB connection credentials
        tlsCAFile: CA file to use in a secure connection
        local: defaults to False.  If set true, will use localhost as the hostname when trying to connect
               to DocumentDB, as is fitting in some development setups using an SSH tunnel to the DocumentDB
               cluster.
    """

    # Get the connection secrets
    sm_client = session.client("secretsmanager")
    try:
        response = sm_client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    secret_string = json.loads(response['SecretString'])
    username = secret_string['username']
    password = secret_string['password']
    port = secret_string['port']
    sm_client.close()

    # Allow localhost override (typically used in development scenarios)
    if local:
        return pymongo.MongoClient(host="localhost", port=port, username=username, password=password,
                                   tls=True, tlsInsecure=True, tlsCAFile=tlsCAFile, retryWrites=False)
    else:
        host = secret_string['host']
        return pymongo.MongoClient(host=host, port=port, username=username, password=password,
                                   tls=True, tlsCAFile=tlsCAFile, retryWrites=False)
