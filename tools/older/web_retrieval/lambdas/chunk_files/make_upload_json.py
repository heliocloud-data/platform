import os
from io import StringIO
from dateutil import parser
import pandas as pd
import boto3

s3 = boto3.client("s3")


def fillempty(val):
    if not val:
        val = "None"
    return val


def parse_csv(dataframe, save_s3_bucket):
    """
    Reads in the dataframe and populates a json object to be passed to the next Map state
    :param df:
    :return:
    """
    upload_req = []
    for i, row in dataframe.iterrows():
        message = {
            "mission": fillempty(row["mission"]),
            "spacecraft": fillempty(row["sc"]),
            "dataset": fillempty(row["product"]),
            "instr": fillempty(row["instr"]),
            "instr_mode": fillempty(row["instr_mode"]),
            "level_proc": fillempty(row["level_proc"]),
            "source": fillempty(row["source"]),
            "download_url": fillempty(row["source_path"]),
            "s3_filename": fillempty(row["s3_key"]),
            "s3_bucket": save_s3_bucket,
            "source_update": parser.parse(fillempty(row["source_update"])).isoformat(),
        }
        upload_req.append(message)
    return upload_req


def lambda_handler(event, context):
    request_name = event["request_name"]
    key = event["chunk"]
    bucket = event["bucket"]
    save_s3_bucket = os.environ.get("SAVE_S3_BUCKET")

    s = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(StringIO(s["Body"].read().decode("utf-8")))
    upload_reqs = parse_csv(df, save_s3_bucket)

    return {
        "statusCode": 200,
        "request_name": request_name,
        "key": key,
        "bucket": bucket,
        "upload_reqs": upload_reqs,
    }
