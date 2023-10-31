"""
Cucumber step definition file for daskhub.
"""

from utils.common_utils import wait_until
from utils.heliocloud_utils import get_daskhub_url
from utils.selector_utils import (
    DASKHUB_LOGIN_PAGE_ID,
    DASKHUB_SERVERSPAWN_PAGE_ID,
    DASKHUB_MAIN_PAGE_ID,
    get_url,
)
from utils.webdriver_utils import webdriver_get, webdriver_screenshot

# pylint: disable=undefined-variable
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
# pylint: disable=function-redefined


@given('the user is on the "daskhub-{page}"')
def step_impl(context, page):
    full_page = f"daskhub-{page}"

    print(context.browser.title)
    if full_page == DASKHUB_SERVERSPAWN_PAGE_ID:
        assert "JupyterHub" == context.browser.title
    elif full_page == DASKHUB_MAIN_PAGE_ID:
        assert "JupyterLab" == context.browser.title
    else:
        raise NotImplementedError(f'STEP: Given the user is on the "{full_page}"')

    context.current_page = full_page


@then('go to the "daskhub-{page}"')
def step_impl(context, page):
    full_page = f"daskhub-{page}"

    base_url = get_daskhub_url(context.hc_instance)
    url = get_url(base_url, full_page)

    webdriver_get(context.browser, url, None, f"temp/feature-tests/{full_page}.png")

    context.current_page = full_page


@then('verify the "daskhub-{page}"')
def step_impl(context, page):
    full_page = f"daskhub-{page}"

    wait_time_in_sec = 0

    if context.current_page == DASKHUB_SERVERSPAWN_PAGE_ID and full_page == DASKHUB_MAIN_PAGE_ID:
        # We are navigating from the spawn server page to the main page
        # this can take a full 10 minutes
        wait_time_in_sec = 600

    if wait_time_in_sec > 0:
        if DASKHUB_MAIN_PAGE_ID:
            if not wait_until(lambda: "JupyterLab" == context.browser.title, wait_time_in_sec):
                print(f"Page did not load after {wait_time_in_sec}")

    webdriver_screenshot(context.browser, f"temp/feature-tests/{full_page}.png")

    if full_page == DASKHUB_LOGIN_PAGE_ID:
        assert "Signin" == context.browser.title
    elif full_page == DASKHUB_SERVERSPAWN_PAGE_ID:
        assert "JupyterHub" == context.browser.title
    elif full_page == DASKHUB_MAIN_PAGE_ID:
        assert "JupyterLab" == context.browser.title
    else:
        raise NotImplementedError(f'STEP: Then verify the "{full_page}"')

    context.current_page = full_page
