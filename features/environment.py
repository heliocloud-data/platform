"""
Cucumber environment.
"""

import os

from utils.webdriver_utils import create_webdriver

# pylint: disable=missing-function-docstring
# pylint: disable=unused-argument


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

    context.user_password = "pAssword123!!"


def before_feature(context, feature):
    if len(feature.tags) > 0:
        context.app = feature.tags[0].lower()
    else:
        context.app = "unknown"

    log_output = f"temp/feature-tests/browser-{context.app}.log"
    if context.app == "portal":
        window_size = "320,2840"
    elif context.app == "daskhub":
        window_size = "320,710"
    else:
        window_size = "1024,768"
        log_output = "temp/feature-tests/browser.log"
    context.window_size = window_size

    # Initialize the web driver.
    context.browser = create_webdriver(window_size, log_output)


def after_feature(context, feature):
    context.browser.quit()
    context.browser = None

    context.window_size = None
    context.app = None


def after_all(context):
    context.user_password = None
