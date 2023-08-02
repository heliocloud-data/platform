import json
import boto3
import urllib.request
import os
import glob
import hashlib

# get the bucket
s3 = boto3.client("s3")


def download_cdaweb_file(url, filename, bucket):
    # # for each given URL link, download the file into the specified bucket
    lambda_file = filename.split("/")
    file_type = lambda_file[-1].split(".")[-1]
    lambda_file = "_".join(lambda_file)

    # determine if the tmp directory is already full and if so delete anything in it
    if glob.glob("/tmp/*"):
        for i in glob.glob("/tmp/*"):
            print(i)
            os.remove(i)

    # save url contents to a local file
    urllib.request.urlretrieve(url, os.path.join("/tmp", lambda_file))

    # upload the local data to S3
    response = s3.upload_file(os.path.join("/tmp", lambda_file), bucket, filename)


def lambda_handler(event, context):
    file_meta = event["file_meta"]
    url = file_meta["download_url"]
    s3_filename = file_meta["s3_filename"]
    s3_bucket = file_meta["s3_bucket"]

    download_cdaweb_file(url, s3_filename, s3_bucket)

    return {"statusCode": 200, "file_meta": file_meta}
