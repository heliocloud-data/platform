import boto3
import pprint
import datetime

session = boto3.Session(
    profile_name="006885615091_CT-PowerUser-HelioCloud", region_name="us-east-1"
)
db = session.client("dynamodb", use_ssl=True, verify="/Users/yeakekl2/root_certificate.pem")
s3 = session.client("s3", use_ssl=True, verify="/Users/yeakekl2/root_certificate.pem")

# do a scan of the summary table
scan_response = db.scan(TableName="dataSummary")
pprint.pprint(scan_response)

# pull out MMS1 FGM survey data from 9/1/2018 - 9/2/2018
date1 = datetime.datetime(2018, 9, 1, 0, 0, 0).isoformat()
date2 = datetime.datetime(2018, 9, 5, 0, 0, 0).isoformat()
response = db.query(
    TableName="fileRegister",
    KeyConditionExpression="dataset = :dataset AND start_date BETWEEN :date1 AND :date2",
    IndexName="dataset_datesort",
    ExpressionAttributeValues={
        ":dataset": {"S": "mms_mms1_fgm_srvy_l2"},
        ":date1": {"S": date1},
        ":date2": {"S": date2},
    },
)
pprint.pprint(response["Items"])
