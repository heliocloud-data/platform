"""
Functions for managing EC2 instances created via the Portal.
"""

import datetime
from dateutil.tz import tzutc

# Local imports
from .config import region
from .ec2_config import (
    instance_types_master_dict,
    security_group_id,
    default_ec2_instance_profile_arn,
    default_subnet_id,
)
from .aws import create_user_tag, get_ec2_pricing


# keypairs
def create_key_pair(aws_session, username, keypair_name):
    """
    Creates an AWS EC2 keypair of name 'keypair_name'
    owned by 'username' within the AWS region the Portal is running in.
    """
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
    """
    Retrieves a list of the AWS EC2 keypairs owned by 'username' within the
    AWS region in which this Portal instance is operating.
    """
    ec2_client = aws_session.client("ec2", region_name=region)
    response = ec2_client.describe_key_pairs(Filters=[{"Name": "tag:Owner", "Values": [username]}])
    return response["KeyPairs"]


def delete_key_pair(aws_session, keypair_name):
    """
    Deletes an AWS EC2 keypair by name within the AWS region in which this Portal instance
    is running.
    """
    ec2_client = aws_session.client("ec2", region_name=region)
    response = ec2_client.delete_key_pair(KeyName=keypair_name)
    return response


def get_running_instances(aws_session, username):
    """
    Gets a list of running OR pending AWS EC2 instances owned by 'username' within the
    AWS region in which this Portal instance is running.
    """
    instances = get_instances(aws_session, username)
    running_instances = [
        ins for ins in instances if ins["instance_state"] in ["running", "pending"]
    ]
    return running_instances


# instance actions
def create_instance(aws_session, username, instance_launch_info):
    """
    Creates a new AWS EC2 instance owned by 'username' within the AWS region
    in which this Portal instance is operating.
    """
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
        SubnetId=default_subnet_id,
        SecurityGroupIds=[
            security_group_id,
        ],
        IamInstanceProfile={
            "Arn": default_ec2_instance_profile_arn,
        },
    )
    return response


def stop_instance(aws_session, instance_id):
    """
    Stops a specific AWS EC2 instance running in the AWS region in which this Portal
    instance is operating.
    """
    ec2 = aws_session.client("ec2", region_name=region)
    response = ec2.stop_instances(InstanceIds=[instance_id])
    return response


def start_instance(aws_session, instance_id):
    """
    Starts a specific AWS EC2 instance in the AWS region in which this Portal
    instance is operating.
    """
    ec2 = aws_session.client("ec2", region_name=region)
    response = ec2.start_instances(InstanceIds=[instance_id])
    return response


def terminate_instance(aws_session, instance_id):
    """
    Terminates a specific AWS EC2 instance in the AWS region in which this Portal
    instance is operating.
    """
    ec2 = aws_session.client("ec2", region_name=region)
    response = ec2.terminate_instances(InstanceIds=[instance_id])
    return response


# list instances
def list_instance_types(aws_session):
    """
    Lists all AWS EC2 instances of the supported types in the Portal config
    that happen to be in the AWS region the Portal is operating in.
    """
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


def get_time_since_start_msg(launch_time: datetime) -> str:
    """
    Returns a specially formatted string for communicating the time elapsed since
    the instance was started.
    """
    time_elapsed = (datetime.datetime.now(tz=tzutc()) - launch_time).total_seconds()
    if time_elapsed < 60:
        return "Just Launched"

    # Less than 5 hours
    if time_elapsed < (60 * 60 * 5):
        return f"{int(time_elapsed / 60)} minutes"

    # Less than 2 days
    if time_elapsed < (60 * 60 * 24 * 2):
        return f"{int(time_elapsed / (60 * 60))} hours"

    # Its been a while...
    return f"{int(time_elapsed / (60 * 60 * 24))} days"


def get_time_color_indicator(launch_time: datetime) -> str:
    """
    Returns a specially formatted string for communicating the importance of the
    amount of time elapsed since the instance was started.
    """
    time_elapsed = (datetime.datetime.now(tz=tzutc()) - launch_time).total_seconds()

    # Less than 5 hours
    if time_elapsed < (60 * 60 * 5):
        return "bg-light"

    # Less than 2 days
    if time_elapsed < (60 * 60 * 24 * 2):
        return "bg-warning"

    # Been a while...
    return "bg-danger"


def get_ssh_user(platform_details: str, root_device_name: str) -> str:
    """
    Returns the name of the SSH user to use for the instance based on
    the platform details
    """
    # Amazon Linux or Ubuntu
    if platform_details == "Linux/UNIX":
        if root_device_name == "/dev/xvda":
            return "ec2-user"
        if root_device_name == "/dev/sda1":
            return "ubuntu"
        # Not sure what we are dealing with
        return "UNKNOWN"

    # RHEL
    if platform_details == "Red Hat Enterprise Linux":
        return "ec2-user"
    if platform_details == "Windows":
        return "None"

    # Defaulted
    return "UNKNOWN"


def get_platform(platform_details: str, root_device_name: str) -> str:
    """
    Returns the name of the OS platform based on the platform
    details and root device name provided.
    """
    if platform_details == "Linux/UNIX":
        if root_device_name == "/dev/xvda":
            return "Amazon Linux"
        if root_device_name == "/dev/sda1":
            return "Ubuntu"
        # Not sure what we are dealing with
        return "Unknown"

    # RHEL
    if platform_details == "Red Hat Enterprise Linux":
        return "Red Hat"

    # Windows
    if platform_details == "Windows":
        return "Windows"

    # Don't know what it is
    return "UNKNOWN"


def get_instances(aws_session, username):
    """
    Gets all the AWS EC2 instances for a particular username
    that are within the AWS region in which this Portal is operating.
    """

    # Get instance desriptions
    ec2_client = aws_session.client("ec2", region_name=region)
    resp = ec2_client.describe_instances(
        Filters=[
            create_user_tag(username),
            {
                "Name": "instance-state-name",
                "Values": ["pending", "running", "stopped", "stopping"],
            },
        ]
    )

    response = []
    for reservation in resp["Reservations"]:
        instance_dict = {}
        image_resp = ec2_client.describe_images(
            ImageIds=[instance["ImageId"] for instance in reservation["Instances"]]
        )
        image_dict = {ir["ImageId"]: ir["Name"] for ir in image_resp["Images"]}

        for instance in reservation["Instances"]:
            instance_dict["instance_id"] = instance["InstanceId"]
            instance_dict.update(instance.items())

            l_time = instance_dict.get("LaunchTime")
            instance_dict["time_since_start"] = get_time_since_start_msg(launch_time=l_time)
            instance_dict["time_color_indicator"] = get_time_color_indicator(launch_time=l_time)
            instance_dict["instance_state"] = instance_dict["State"]["Name"]

            for tag_dicts in instance["Tags"]:
                if tag_dicts["Key"] == "Name":
                    instance_dict["instance_name"] = tag_dicts["Value"]
                if tag_dicts["Key"] == "nbtoken":
                    instance_dict["nbtoken"] = tag_dicts["Value"]

            # Getting platform information
            platform_details = instance_dict.get("PlatformDetails")
            root_device_name = instance_dict.get("RootDeviceName")
            instance_dict["ssh_user"] = get_ssh_user(
                platform_details=platform_details, root_device_name=root_device_name
            )
            instance_dict["platform_inferred"] = get_platform(
                platform_details=platform_details, root_device_name=root_device_name
            )

            if instance_dict["ImageId"] in image_dict.keys():
                instance_dict["image_name"] = image_dict[instance_dict["ImageId"]]
            else:
                instance_dict["image_name"] = ""
            response.append(instance_dict)
    return response


def get_ami_info(aws_session, ami_list) -> dict:
    """
    Returns a dictionary of AWS EC2 image information for all
    images supported in the AWS region in which the Portal is operating.
    """
    ec2_client = aws_session.client("ec2", region_name=region)
    resp_dict = {}
    resp = ec2_client.describe_images(ImageIds=ami_list)
    for image in resp["Images"]:
        resp_dict[image["ImageId"]] = image
        if "BlockDeviceMappings" in image.keys():
            resp_dict[image["ImageId"]]["DeviceName"] = image["BlockDeviceMappings"][0][
                "DeviceName"
            ]
            resp_dict[image["ImageId"]]["VolumeSize"] = image["BlockDeviceMappings"][0]["Ebs"][
                "VolumeSize"
            ]
            resp_dict[image["ImageId"]]["VolumeType"] = image["BlockDeviceMappings"][0]["Ebs"][
                "VolumeType"
            ]
    return resp_dict
