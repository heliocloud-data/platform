"""
Cucumber step definition file for portal.
"""
import os

from selenium.webdriver.common.by import By

from utils.common_utils import wait_until
from utils.heliocloud_utils import get_portal_url
from utils.selector_utils import (
    PORTAL_KEYPAIRS_PAGE_ID,
    PORTAL_LAUNCHINSTANCE_PAGE_ID,
    PORTAL_LOGIN_PAGE_ID,
    PORTAL_MAIN_PAGE_ID,
    get_url,
    do_enter_text,
    do_click,
    do_select_from_dropdown,
    get_timeout_for_field,
    do_wait_for_element,
)
from utils.webdriver_utils import webdriver_get, webdriver_screenshot

# pylint: disable=undefined-variable
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
# pylint: disable=function-redefined


@given("the user is logged in")
def step_impl(context):
    full_page = PORTAL_LOGIN_PAGE_ID

    base_url = get_portal_url(context.hc_instance)
    url = get_url(base_url, full_page)

    webdriver_get(context.browser, url, None, f"temp/feature-tests/{full_page}.png")

    context.current_page = full_page


@given('no existing sshkey named "{sshkey}" exists')
def step_impl(context, sshkey):
    loc = os.path.expanduser(f"~/Downloads/{sshkey}")
    if os.path.isfile(loc):
        os.remove(loc)


@then('go to the "portal-{page}"')
def step_impl(context, page):
    full_page = f"portal-{page}"

    base_url = get_portal_url(context.hc_instance)
    url = get_url(base_url, full_page)

    webdriver_get(context.browser, url, None, f"temp/feature-tests/{full_page}.png")

    context.current_page = full_page


@then('verify the "portal-{page}"')
def step_impl(context, page):
    full_page = f"portal-{page}"

    webdriver_screenshot(context.browser, f"temp/feature-tests/{full_page}.png")

    if full_page == PORTAL_LOGIN_PAGE_ID:
        assert "Signin" == context.browser.title
    elif full_page == PORTAL_MAIN_PAGE_ID:
        assert "HelioCloud User Portal" == context.browser.title
    elif full_page == PORTAL_KEYPAIRS_PAGE_ID:
        context.browser.find_element(By.NAME, "create_keypair")
    elif full_page == PORTAL_LAUNCHINSTANCE_PAGE_ID:
        context.browser.find_element(By.NAME, "launch_type")
    else:
        raise NotImplementedError(f'STEP: Then verify the "{full_page}"')

    context.current_page = full_page


@then('enter "{text}" in the "{field}" field')
def step_impl(context, field, text):
    do_enter_text(context.browser, text, field, context.current_page)


@then('enter the password in the "{field}" field')
def step_impl(context, field):
    do_enter_text(context.browser, context.user_password, field, context.current_page)


@then('click "{text}"')
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
    do_click(context.browser, text, context.current_page)


@then('confirm file "{name}" exists in the Downloads directory')
def step_impl(context, name):
    max_wait_time = 10
    loc = os.path.expanduser(f"~/Downloads/{name}")

    if wait_until(lambda: os.path.isfile(loc), max_wait_time):
        return

    if os.path.isfile(loc) is False:
        raise ValueError(f"File {loc} was not found")


@then('select "{text}" in the "{field}" dropdown')
def step_impl(context, text, field):
    do_select_from_dropdown(context.browser, text, field, context.current_page)
