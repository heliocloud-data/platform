"""
Cucumber environment.
"""

import os

from utils.webdriver_utils import create_webdriver

# pylint: disable=missing-function-docstring
# pylint: disable=unused-argument

CREATE_NEW_WEBDRIVER_PER_SCENARIO = False


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


def get_window_size(context):
    if context.app == "portal":
        window_size = "320,2840"
    elif context.app == "daskhub":
        window_size = "320,710"
    else:
        window_size = "1024,768"
    return window_size


def get_log_output(context, scenario=None):
    if scenario is None:
        default_log_output = f"temp/feature-tests/browser-{context.app}.log"
    else:
        default_log_output = f"temp/feature-tests/browser-{context.app}-({scenario}).log"

    if context.app == "portal":
        log_output = default_log_output
    elif context.app == "daskhub":
        log_output = default_log_output
    else:
        log_output = "temp/feature-tests/browser.log"
    return log_output


def before_all(context):
    init_heliocloud_context(context)

    context.user_password = "pAssword123!!"


def before_feature(context, feature):
    if len(feature.tags) > 0:
        context.app = feature.tags[0].lower()
    else:
        context.app = "unknown"

    if not CREATE_NEW_WEBDRIVER_PER_SCENARIO:
        context.log_output = get_log_output(context)
        context.window_size = get_window_size(context)
        context.new_login_required = False

        # Initialize the web driver.
        context.browser = create_webdriver(context.window_size, context.log_output)


def before_scenario(context, scenario):
    if CREATE_NEW_WEBDRIVER_PER_SCENARIO:
        context.log_output = get_log_output(context, scenario)
        context.window_size = get_window_size(context)
        context.new_login_required = True

        # Initialize the web driver.
        context.browser = create_webdriver(context.window_size, context.log_output)


def after_feature(context, feature):
    if not CREATE_NEW_WEBDRIVER_PER_SCENARIO:
        context.browser.quit()
        context.browser = None

        context.window_size = None
    context.app = None


def after_scenario(context, scenario):
    if CREATE_NEW_WEBDRIVER_PER_SCENARIO:
        context.browser.quit()
        context.browser = None


def after_all(context):
    context.user_password = None
