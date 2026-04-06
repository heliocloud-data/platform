"""
Cucumber step definition file for daskhub.
"""
import time

from utils.common_utils import wait_until
from utils.heliocloud_utils import get_daskhub_url
from utils.selector_utils import (
    DASKHUB_LOGIN_PAGE_ID,
    DASKHUB_SERVERSPAWN_PAGE_ID,
    DASKHUB_MAIN_PAGE_ID,
    get_url,
    do_click,
    do_double_click,
    do_wait_for_element,
    do_wait_for_element_not_present,
)
from utils.webdriver_utils import webdriver_get, webdriver_screenshot

# pylint: disable=undefined-variable
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
# pylint: disable=function-redefined


@given('the user is on the "daskhub-{page}"')
def step_impl(context, page):
    full_page = f"daskhub-{page}"

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
    time_to_wait = None
    if full_page == "daskhub-classic-page":
        url = f"{base_url}/user/{context.user_name}/tree"
        time_to_wait = 10
    else:
        url = get_url(base_url, full_page)

    webdriver_get(context.browser, url, time_to_wait, f"temp/feature-tests/{full_page}.png")

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


@then('click folder item "{text}"')
def step_impl(context, text):
    timeout = 10
    if timeout is not None:
        do_wait_for_element(
            context.browser,
            text,
            "daskhub-folder-item",
            context.current_page,
            timeout,
            f"temp/feature-tests/{context.current_page}.png",
        )

    if text.endswith(".ipynb"):
        # We're attempting to open a notebook, daskhub
        # will launch this in a new browser window when
        # clicking the button, to get around this, we should
        # navigate directly to the target.
        url = f"{context.browser.current_url}/{text}"
        webdriver_get(
            context.browser,
            url,
            10,
            "temp/feature-tests/" + context.current_page + "__" + text + ".png",
        )
    else:
        do_click(context.browser, text, context.current_page, "daskhub-folder-item")
    context.current_page = context.current_page + "__" + text


@then('double click folder item "{text}"')
def step_impl(context, text):
    timeout = 10
    if timeout is not None:
        do_wait_for_element(
            context.browser,
            text,
            "daskhub-folder-item",
            context.current_page,
            timeout,
            f"temp/feature-tests/{context.current_page}.png",
        )

    if text.endswith(".ipynb"):
        # We're attempting to open a notebook, daskhub
        # will launch this in a new browser window when
        # clicking the button, to get around this, we should
        # navigate directly to the target.
        url = f"{context.browser.current_url}/{text}"
        webdriver_get(
            context.browser,
            url,
            10,
            "temp/feature-tests/" + context.current_page + "__" + text + ".png",
        )
    else:
        do_double_click(context.browser, text, context.current_page, "daskhub-folder-item")
    context.current_page = context.current_page + "__" + text


@then("wait up to {wait_time_in_sec} seconds for execution to complete")
def step_impl(context, wait_time_in_sec):
    # Current page should show a jupyter notebook.
    webdriver_screenshot(context.browser, f"temp/feature-tests/{context.current_page}.png")

    # When a notebook shows up, but hasn't run, it's display
    # `In [ ]` on the left before all items.  When execution
    # starts, these will transition to `In [*]`.  Once executed
    # they will display `In [1]`, ..., `In [N]` for each item.

    # First, we're going to check that the text `[ ]` doesn't
    # appear in the document, that's the visual cue that we've
    # started executing.
    time.sleep(10)

    # Next, we're going to check that the text `[*]` doesn't
    # appear in the document, that's the visual cue that we've
    # finished executing.
    if not do_wait_for_element_not_present(
        context.browser,
        "//div[contains(text(), '[*]')]",
        context.current_page,
        int(wait_time_in_sec),
        f"temp/feature-tests/{context.current_page}.png",
    ):
        raise ValueError(
            f"STEP: Notebook did not finish executing after {wait_time_in_sec} seconds"
        )

    # Take a screenshot!
    webdriver_screenshot(context.browser, f"temp/feature-tests/{context.current_page}.png")
