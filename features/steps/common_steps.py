"""
Cucumber step definition file for common stuff.
"""
import time

from utils.heliocloud_utils import get_base_url

from utils.selector_utils import (
    get_url,
    do_enter_text,
    do_click,
    do_double_click,
    get_timeout_for_field,
    do_wait_for_element,
)

from utils.webdriver_utils import webdriver_get, webdriver_screenshot

# pylint: disable=undefined-variable
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
# pylint: disable=function-redefined


@given("a fully deployed instance of HelioCloud")
def step_impl(context):
    print("Do nothing.")


@given("the user is logged in")
def step_impl(context):
    full_page = f"{context.app}-login-page"

    base_url = get_base_url(context.hc_instance, context.app)
    url = get_url(base_url, full_page)

    webdriver_get(context.browser, url, None, None)  # f"temp/feature-tests/{full_page}.png")
    context.current_page = full_page

    if context.new_login_required:
        do_enter_text(context.browser, context.user_name, "username", context.current_page)
        do_enter_text(context.browser, context.user_password, "password", context.current_page)
        do_click(context.browser, "Sign in", context.current_page)

        context.current_page = full_page


@then("wait {time_in_sec} seconds")
def step_impl(context, time_in_sec):
    time.sleep(int(time_in_sec))


@then('take a screenshot with name "{name}"')
def step_impl(context, name):
    webdriver_screenshot(context.browser, f"temp/feature-tests/{name}")


@then('fail with message "{msg}"')
def step_impl(context, msg):
    raise ValueError(msg)


@then('enter "{text}" in the "{field}" field')
def step_impl(context, field, text):
    do_enter_text(context.browser, text, field, context.current_page)

    if field == "username":
        context.user_name = text


@then('enter the password in the "{field}" field')
def step_impl(context, field):
    do_enter_text(context.browser, context.user_password, field, context.current_page)


@then('click "{text}"')
def step_impl(context, text):
    # "Restart the kernel and run all cells"
    # if it's this we probably need
    # /html/body/dialog/div/div[2]/button[2]/div[2]
    # <div class="jp-Dialog-buttonLabel" title="" aria-label="Confirm Kernel Restart">Restart</div>
    timeout = get_timeout_for_field(text, "button", context.current_page)
    if timeout is not None:
        do_wait_for_element(
            context.browser,
            text,
            "button",
            context.current_page,
            timeout,
            f"temp/feature-tests/{context.current_page}_01.png",
        )
    do_click(context.browser, text, context.current_page)

    if "Restart the kernel and run all cells" == text:
        # look for modal dialog button
        if timeout is not None:
            # I think it's OK if it's not here...
            do_wait_for_element(
                context.browser,
                "Restart",
                "button",
                context.current_page,
                timeout,
                f"temp/feature-tests/{context.current_page}_02.png",
            )

        do_click(context.browser, "Restart", context.current_page)

        time.sleep(2)

        webdriver_screenshot(context.browser, f"temp/feature-tests/{context.current_page}_03.png")


@then('double click "{text}"')
def step_impl(context, text):
    timeout = get_timeout_for_field(text, "button", context.current_page)
    if timeout is not None:
        do_wait_for_element(
            context.browser,
            text,
            "button",
            context.current_page,
            timeout,
            f"temp/feature-tests/{context.current_page}.png",
        )
    do_double_click(context.browser, text, context.current_page)
