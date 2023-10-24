"""
Cucumber environment.
"""

import os

from utils.webdriver_utils import create_webdriver

# pylint: disable=missing-function-docstring


def init_heliocloud_context(context):
    """
    Initialize the heliocloud context
    """

    context.hc_instance = os.environ["HC_INSTANCE"]
    context.aws_default_region = os.environ["AWS_DEFAULT_REGION"]

    print("Loading environment variable(s) for test(s):")
    print(f" * HC_INSTANCE: {context.hc_instance}")
    print(f" * AWS_DEFAULT_REGION: {context.aws_default_region}")
    print()


def before_all(context):
    init_heliocloud_context(context)

    # Initialize the web driver.
    context.browser = create_webdriver()
    context.user_password = "pAssword123!!"


def after_all(context):
    context.browser.quit()
    context.browser = None
    context.user_password = None
