import json
import boto3

ec2_client = boto3.client("ec2")
s3_client = boto3.client("s3")
rds_client = boto3.client("rds")
tag_to_check = "Owner"


def check_for_tag(my_list, check=tag_to_check):
    print("Looking for tag [" + check + "] in list " + json.dumps(my_list))
    for i in my_list:
        if "Key" in i:
            if i["Key"] == check:
                return True
        elif "key" in i:
            if i["key"] == check:
                return True
    return False


def tag_bucket(bucket, user):
    s3_client.put_bucket_tagging(
        Bucket=bucket,
        Tagging={
            "TagSet": [
                {
                    "Key": tag_to_check,
                    "Value": user,
                },
                {"Key": "Project", "Value": "hsdcloud"},
            ]
        },
    )


def tag_instance(instance, tag_name, val):
    ec2_client.create_tags(
        Resources=[instance],
        Tags=[
            {
                "Key": tag_name,
                "Value": val,
            }
        ],
    )


def tag_rds_instance(rds_instance, user):
    rds_client.add_tags_to_resource(
        ResourceName=rds_instance,
        Tags=[{"Key": tag_to_check, "Value": user}, {"Key": "Project", "Value": "hsdcloud"}],
    )


def lambda_handler(event, context):
    print(json.dumps(event))
    user = ""
    try:
        # IAM user
        user = event["detail"]["userIdentity"]["userName"]
    except:
        user = event["detail"]["userIdentity"]["arn"].rsplit("/", 1)[-1]
    if event["source"] == "aws.s3":
        bucket = event["detail"]["requestParameters"]["bucketName"]
        # check for existing tags
        try:
            bucket_tags = json.loads(s3_client.get_bucket_tagging(Bucket=bucket))
            if check_for_tag(bucket_tags["TagSet"]):
                print("Bucket [" + bucket + "] is already tagged with [" + tag_to_check + "]")
                return
            else:
                print("Tagging Bucket [" + bucket + "] with " + tag_to_check + "=" + user)
                tag_bucket(bucket, user)
                return
        except:
            # if an exception is raised, the bucket is not tagged
            print("No tags found on bucket [" + bucket + "]")
            print("Tagging Bucket [" + bucket + "] with " + tag_to_check + "=" + user)
            tag_bucket(bucket, user)
            return
    elif event["source"] == "aws.ec2":
        try:
            instances = event["detail"]["responseElements"]["instancesSet"]["items"]
        except:
            instances = None
        if instances is None:
            instances = []
        instances_list = []
        for j in instances:
            instances_list.append(j["instanceId"])
        print(str(instances_list))
        response = ec2_client.describe_instances(InstanceIds=instances_list)
        for i in instances:
            iid = i["instanceId"]
            itags = i["tagSet"]["items"]
            print(iid, itags)
            try:
                # ensure we have tag for Owner
                if not check_for_tag(itags):
                    print("Tagging Instance [" + iid + "] with " + tag_to_check + "=" + user)
                    tag_instance(iid, tag_name=tag_to_check, val=user)
                # ensure we have tag for Project
                if not check_for_tag(itags, check="Project"):
                    print("Tagging Instance [" + iid + "] with Project = hsdcloud")
                    tag_instance(iid, tag_name="Project", val="hsdcloud")
                # look for the 'Snapshot' tag on non-eks ec2 instances
                # we need to auto-tag user created ec2 volumes which should be backed up
                # EKS volumes are handled separately
                if not check_for_tag(itags, check="Snapshot"):
                    if user != "AutoScaling":
                        print("Tagging Instance [" + iid + "] with Snapshot = true")
                        tag_instance(iid, tag_name="Snapshot", val="true")
                return
            except:
                # if an exception is raised, the instance is not tagged
                print("No tags found on instance [" + iid + "]")
                print("Tagging Instance [" + iid + "] with " + tag_to_check + "=" + user)
                tag_instance(iid, tag_name=tag_to_check, val=user)
                try:
                    if user != "AutoScaling":
                        tag_instance(iid, tag_name="Snapshot", val="true")
                except:
                    pass
                return
    elif event["source"] == "aws.rds":
        rds_instance = event["detail"]["responseElements"]["dBInstanceArn"]
        rds_tags = rds_client.list_tags_for_resource(ResourceName=rds_instance)
        try:
            if check_for_tag(rds_tags["TagList"]):
                print(
                    "RDS Instance ["
                    + rds_instance
                    + "] is already tagged with ["
                    + tag_to_check
                    + "]"
                )
                return
            else:
                print(
                    "Tagging RDS Instance [" + rds_instance + "] with " + tag_to_check + "=" + user
                )
                tag_rds_instance(rds_instance, user)
                return
        except:
            # if an exception is raised, the instance is not tagged
            print("No tags found on RDS instance [" + rds_instance + "]")
            print("Tagging RDS Instance [" + rds_instance + "] with " + tag_to_check + "=" + user)
            tag_rds_instance(rds_instance, user)
            return
    return
