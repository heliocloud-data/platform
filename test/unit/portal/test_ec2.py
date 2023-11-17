"""
Tests for ec2.py in the Portal
"""
import datetime
import unittest
from unittest.mock import patch

import dateutil.tz as tz

import portal.lib.ec2 as ec2


class TestEc2(unittest.TestCase):
    def test_get_time_since_start_msg_just_launched(self):
        launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(seconds=30)
        self.assertEqual(ec2.get_time_since_start_msg(launch_time), "Just Launched")

    def test_get_time_since_start_msg_minutes(self):
        launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(minutes=15)
        self.assertIn("minutes", ec2.get_time_since_start_msg(launch_time))

    def test_get_time_since_start_msg_hours(self):
        launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(hours=6)
        self.assertIn("hours", ec2.get_time_since_start_msg(launch_time))

    def test_get_time_since_start_msg_days(self):
        launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(days=5)
        self.assertIn("days", ec2.get_time_since_start_msg(launch_time))

    def test_get_time_color_indicator_light(self):
        launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(seconds=10)
        self.assertEqual("bg-light", ec2.get_time_color_indicator(launch_time))

    def test_get_time_color_indicator_warning(self):
        launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(days=1)
        self.assertEqual("bg-warning", ec2.get_time_color_indicator(launch_time))

    def test_get_time_color_indicator_danger(self):
        launch_time = datetime.datetime.now(tz=tz.tzutc()) - datetime.timedelta(weeks=4)
        self.assertEqual("bg-danger", ec2.get_time_color_indicator(launch_time))

    def test_get_ssh_user_windows(self):
        user = ec2.get_ssh_user(platform_details="Windows", root_device_name="")
        self.assertEqual(user, "None")

    def test_get_ssh_user_rhel(self):
        user = ec2.get_ssh_user(platform_details="Red Hat Enterprise Linux", root_device_name="")
        self.assertEqual(user, "ec2-user")

    def test_get_ssh_user_linux(self):
        user = ec2.get_ssh_user(platform_details="Linux/UNIX", root_device_name="/dev/xvda")
        self.assertEqual(user, "ec2-user")
        user = ec2.get_ssh_user(platform_details="Linux/UNIX", root_device_name="/dev/sda1")
        self.assertEqual(user, "ubuntu")

    def test_get_platform_amazon(self):
        self.assertEqual(
            "Amazon Linux",
            ec2.get_platform(platform_details="Linux/UNIX", root_device_name="/dev/xvda"),
        )

    def test_get_platform_ubuntu(self):
        self.assertEqual(
            "Ubuntu", ec2.get_platform(platform_details="Linux/UNIX", root_device_name="/dev/sda1")
        )

    def test_get_platform_red_hat(self):
        self.assertEqual(
            "Red Hat",
            ec2.get_platform(platform_details="Red Hat Enterprise Linux", root_device_name=""),
        )

    def test_get_platform_windows(self):
        self.assertEqual(
            "Windows", ec2.get_platform(platform_details="Windows", root_device_name="")
        )

    @patch("boto3.session.Session")
    def test_get_ami_info(self, session):
        # TODO: implement a check on ec2.get_ami_info that checks the structure of the result
        #   returned to protect from future changes
        pass

    @patch("boto3.session.Session")
    def test_list_instance_types(self, session):
        # TODO: Implement
        pass

    def test_get_running_instances(self):
        # TODO: Implement
        pass
