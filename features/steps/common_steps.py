"""
Cucumber step definition file for common stuff.
"""
import time

from utils.webdriver_utils import webdriver_screenshot

# pylint: disable=undefined-variable
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
# pylint: disable=function-redefined


@given("a fully deployed instance of HelioCloud")
def step_impl(context):
    print("Do nothing.")


@then("wait {time_in_sec} seconds")
def step_impl(context, time_in_sec):
    time.sleep(int(time_in_sec))


@then('take a screenshot with name "{name}"')
def step_impl(context, name):
    webdriver_screenshot(context.browser, f"temp/feature-tests/{name}")


@then('fail with message "{msg}"')
def step_impl(context, msg):
    raise ValueError(msg)
