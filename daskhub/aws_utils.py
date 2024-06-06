import boto3
import botocore.exceptions


def get_instance_types_by_region(region_name):
    ec2_client = boto3.client("ec2", region_name=region_name)
    instance_types = set()
    describe_args = {}

    print(f"Fetching supported instance types for region {region_name} ...")
    while True:
        describe_result = ec2_client.describe_instance_types(**describe_args)
        for i in describe_result["InstanceTypes"]:
            instance_types.add(i["InstanceType"])

        if "NextToken" not in describe_result:
            break
        describe_args["NextToken"] = describe_result["NextToken"]

    return instance_types


def find_route53_record_by_type_and_name(hosted_zone_id, record_type, record_name):
    ret = None
    route53_client = boto3.client("route53")

    start_record_identifier = None
    describe_args = {
        "HostedZoneId": hosted_zone_id,
    }

    print(f"Fetching Route53 RecordSets ...")
    while ret == None:
        try:
            resp = route53_client.list_resource_record_sets(**describe_args)
        except botocore.exceptions.ClientError as err:
            # This error will be thrown if the hosted zone doesn't exit, which will be the case
            # for the initial configuration.
            if err.response["Error"]["Code"] == "NoSuchHostedZone":
                break

            # All other client errors should cause a failure.
            raise err

        for i in resp["ResourceRecordSets"]:
            if i["Type"] != record_type or i["Name"] != record_name:
                continue
            ret = i
            break

        if "IsTruncated" in resp and resp["IsTruncated"] == True:
            describe_args["StartRecordIdentifier"] = resp["NextRecordIdentifier"]
        else:
            break

    return ret
