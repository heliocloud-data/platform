"""
Tests for ec2.py in the Portal
"""
import datetime
import dateutil.tz as tz
import portal.lib.ec2 as ec2


def test_get_time_since_start_msg_just_launched():
    launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(seconds=30)
    assert "Just Launched" in ec2.get_time_since_start_msg(launch_time)


def test_get_time_since_start_msg_minutes():
    launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(minutes=15)
    assert "minutes" in ec2.get_time_since_start_msg(launch_time)


def test_get_time_since_start_msg_hours():
    launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(hours=6)
    assert "hours" in ec2.get_time_since_start_msg(launch_time)


def test_get_time_since_start_msg_days():
    launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(days=5)
    assert "days" in ec2.get_time_since_start_msg(launch_time)


def test_get_time_color_indicator_light():
    launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(seconds=10)
    assert "bg-light" in ec2.get_time_color_indicator(launch_time)


def test_get_time_color_indicator_warning():
    launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(days=1)
    assert "bg-warning" in ec2.get_time_color_indicator(launch_time)


def test_get_time_color_indicator_danger():
    launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(weeks=4)
    assert "bg-danger" in ec2.get_time_color_indicator(launch_time)


def test_get_ssh_user_windows():
    user = ec2.get_ssh_user(platform_details="Windows", root_device_name="")
    assert user == "None"


def test_get_ssh_user_rhel():
    user = ec2.get_ssh_user(platform_details="Red Hat Enterprise Linux", root_device_name="")
    assert "ec2-user" == user


def test_get_ssh_user_linux():
    user = ec2.get_ssh_user(platform_details="Linux/UNIX", root_device_name="/dev/xvda")
    assert user == "ec2-user"
    user = ec2.get_ssh_user(platform_details="Linux/UNIX", root_device_name="/dev/sda1")
    assert user == "ubuntu"


def test_get_platform_amazon():
    platform = ec2.get_platform(platform_details="Linux/UNIX", root_device_name="/dev/xvda")
    assert platform == "Amazon Linux"


def test_get_platform_ubuntu():
    platform = ec2.get_platform(platform_details="Linux/UNIX", root_device_name="/dev/sda1")
    assert platform == "Ubuntu"


def test_get_platform_red_hat():
    platform = ec2.get_platform(platform_details="Red Hat Enterprise Linux", root_device_name="")
    assert platform == "Red Hat"


def test_get_platform_windows():
    platform = ec2.get_platform(platform_details="Windows", root_device_name="")
    assert platform == "Windows"


def test_get_ami_info():
    # TODO: implement a check on ec2.get_ami_info that checks the structure of the result
    #   returned to protect from future changes
    pass


def test_list_instance_types():
    # TODO: Implement
    pass


def test_get_running_instances():
    # TODO: Implement
    pass
