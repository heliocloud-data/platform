import datetime
from dateutil.tz import tzutc
from config import region
from ec2_config import (
    instance_types_master_dict,
    security_group_id,
    default_ec2_role_arn,
    default_ec2_role_name,
)
from aws import create_user_tag, get_ec2_pricing


### keypairs
def create_key_pair(aws_session, username, keypair_name):
    ec2_client = aws_session.client("ec2", region_name=region)
    response = ec2_client.create_key_pair(
        KeyName=keypair_name,
        TagSpecifications=[
            {
                "ResourceType": "key-pair",
                "Tags": [
                    {"Key": "Owner", "Value": username},
                    {"Key": "Dashboard", "Value": "True"},
                ],
            }
        ],
    )
    return response


def list_key_pairs(aws_session, username):
    ec2_client = aws_session.client("ec2", region_name=region)
    response = ec2_client.describe_key_pairs(Filters=[{"Name": "tag:Owner", "Values": [username]}])
    return response["KeyPairs"]


def delete_key_pair(aws_session, keypair_name):
    ec2_client = aws_session.client("ec2", region_name=region)
    response = ec2_client.delete_key_pair(KeyName=keypair_name)
    return response


def get_running_instances(aws_session, username):
    instances = get_instances(aws_session, username)
    running_instances = [
        ins for ins in instances if ins["instance_state"] in ["running", "pending"]
    ]
    return running_instances


### instance actions
def create_instance(aws_session, username, instance_launch_info):
    ec2_client = aws_session.client("ec2", region_name=region)
    tag_specifications = [
        {
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Owner", "Value": username},
                {"Key": "Name", "Value": instance_launch_info["instance_name"]},
                {"Key": "Dashboard", "Value": "True"},
            ],
        }
    ]
    response = ec2_client.run_instances(
        BlockDeviceMappings=[
            {
                "DeviceName": instance_launch_info["device_name"],
                "Ebs": {
                    "DeleteOnTermination": True,
                    "VolumeSize": instance_launch_info["volume_size"],
                    "VolumeType": instance_launch_info["volume_type"],
                },
            },
        ],
        ImageId=instance_launch_info["image_id"],
        InstanceType=instance_launch_info["instance_type"],
        MaxCount=1,
        MinCount=1,
        Monitoring={"Enabled": False},
        KeyName=instance_launch_info["key_pair"],
        TagSpecifications=tag_specifications,
        SecurityGroupIds=[
            security_group_id,
        ],
        IamInstanceProfile={
            "Arn": default_ec2_role_arn,
            "Name": default_ec2_role_name,
        },
    )
    return response


def stop_instance(aws_session, instance_id):
    ec2 = aws_session.client("ec2", region_name=region)
    response = ec2.stop_instances(InstanceIds=[instance_id])
    return response


def start_instance(aws_session, instance_id):
    ec2 = aws_session.client("ec2", region_name=region)
    response = ec2.start_instances(InstanceIds=[instance_id])
    return response


def terminate_instance(aws_session, instance_id):
    ec2 = aws_session.client("ec2", region_name=region)
    response = ec2.terminate_instances(InstanceIds=[instance_id])
    return response


### list instances
def list_instance_types(aws_session):
    instance_types = {}
    all_it = []
    for use_case_dict in instance_types_master_dict.values():
        all_it.extend(use_case_dict["types"])
    pricing_dict = get_ec2_pricing(aws_session, all_it)
    for use_case, use_case_dict in instance_types_master_dict.items():
        itypes = use_case_dict["types"]
        use_case_types = {it: pricing_dict[it] for it in itypes}
        instance_types[use_case] = {
            "types": use_case_types,
            "description": use_case_dict["description"],
        }
    return instance_types


def get_instances(aws_session, username):
    ec2_client = aws_session.client("ec2", region_name=region)
    user_tag_dict = create_user_tag(username)
    resp = ec2_client.describe_instances(
        Filters=[
            user_tag_dict,
            {
                "Name": "instance-state-name",
                "Values": ["pending", "running", "stopped", "stopping"],
            },
        ]
    )
    response = []
    for r in resp["Reservations"]:
        instance_dict = {}
        image_resp = ec2_client.describe_images(
            ImageIds=[instance["ImageId"] for instance in r["Instances"]]
        )
        image_dict = {ir["ImageId"]: ir["Name"] for ir in image_resp["Images"]}
        for instance in r["Instances"]:
            instance_id = instance["InstanceId"]
            for key, val in instance.items():
                instance_dict[key] = val
            time_since_start_seconds = (
                datetime.datetime.now(tz=tzutc()) - instance_dict["LaunchTime"]
            ).total_seconds()
            if time_since_start_seconds < 60:  # less than 1 min
                time_since_start = "Just Launched"
                time_color_indicator = "bg-light"
            elif time_since_start_seconds < 60 * 60 * 5:  # less than 5 hours
                time_since_start = f"{int(time_since_start_seconds/60.)} minutes"
                time_color_indicator = "bg-light"
            elif time_since_start_seconds < 60 * 60 * 24 * 2:  # less than 2 days
                time_since_start = f"{int(time_since_start_seconds/(60*60))} hours"
                time_color_indicator = "bg-warning"
            else:
                time_since_start = f"{int(time_since_start_seconds/(60*60*24))} days"
                time_color_indicator = "bg-danger"
            instance_dict["time_since_start"] = time_since_start
            instance_dict["time_color_indicator"] = time_color_indicator
            instance_state = instance_dict["State"]["Name"]
            instance_dict["instance_state"] = instance_state
            instance_dict["instance_id"] = instance_id
            instance_dict["instance_name"] = ""
            for tag_dicts in instance["Tags"]:
                if tag_dicts["Key"] == "Name":
                    instance_dict["instance_name"] = tag_dicts["Value"]
                if tag_dicts["Key"] == "nbtoken":
                    instance_dict["nbtoken"] = tag_dicts["Value"]
            if (
                instance_dict["PlatformDetails"] == "Linux/UNIX"
                and instance_dict["RootDeviceName"] == "/dev/xvda"
            ):
                instance_dict["ssh_user"] = "ec2-user"
                instance_dict["platform_inferred"] = "Amazon Linux"
            elif (
                instance_dict["PlatformDetails"] == "Linux/UNIX"
                and instance_dict["RootDeviceName"] == "/dev/sda1"
            ):
                instance_dict["ssh_user"] = "ubuntu"
                instance_dict["platform_inferred"] = "Ubuntu"
            elif instance_dict["PlatformDetails"] == "Red Hat Enterprise Linux":
                instance_dict["ssh_user"] = "ec2-user"
                instance_dict["platform_inferred"] = "Red Hat"
            elif instance_dict["PlatformDetails"] == "Windows":  # no ssh connection
                instance_dict["ssh_user"] = "None"
                instance_dict["platform_inferred"] = "Windows"
            if instance_dict["ImageId"] in image_dict.keys():
                instance_dict["image_name"] = image_dict[instance_dict["ImageId"]]
            else:
                instance_dict["image_name"] = ""
            response.append(instance_dict)
    return response


def get_ami_info(aws_session, ami_list):
    ec2_client = aws_session.client("ec2", region_name=region)
    resp_dict = {}
    resp = ec2_client.describe_images(ImageIds=ami_list)
    for r in resp["Images"]:
        resp_dict[r["ImageId"]] = r
        if "BlockDeviceMappings" in r.keys():
            resp_dict[r["ImageId"]]["DeviceName"] = r["BlockDeviceMappings"][0]["DeviceName"]
            resp_dict[r["ImageId"]]["VolumeSize"] = r["BlockDeviceMappings"][0]["Ebs"]["VolumeSize"]
            resp_dict[r["ImageId"]]["VolumeType"] = r["BlockDeviceMappings"][0]["Ebs"]["VolumeType"]
    return resp_dict
