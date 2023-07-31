import json
import boto3
import urllib.parse
import pandas as pd
from io import StringIO
from dateutil import parser

# set up the destination queue that we will write the filenames to
sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName="testSQS")

# set up the s3 bucket where we will receive the event
s3 = boto3.client("s3")


def fillempty(val):
    if not val:
        val = "None"
    return val


def load_queue(dataframe):
    """
    Cycles through the pandas dataframe (loaded from the CSV file) and fills the SQS
    """
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
            "s3_bucket": fillempty(row["s3_bucket"]),
            "source_update": parser.parse(fillempty(row["source_update"])).isoformat(),
        }
        queue.send_message(MessageBody=json.dumps(message))


def lambda_handler(event, context):
    print("Received the file: " + json.dumps(event, indent=2))

    # get the object from the event and show its content type
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")

    # only run script if file is a 'upload_manifest'
    if "upload_manifest" in key:
        try:
            s = s3.get_object(Bucket=bucket, Key=key)

            # load in to a pandas dataframe
            df = pd.read_csv(StringIO(s["Body"].read().decode("utf-8")))

            load_queue(df)

            return {"statusCode": 200}
        except Exception as e:
            print(e)
            print("Error fetching object")
            # raise e
