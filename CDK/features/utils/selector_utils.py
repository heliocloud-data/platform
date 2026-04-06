"""
Contains functions to select and interact with elements
in our application.
"""

import time

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from utils.webdriver_utils import webdriver_screenshot

PORTAL_LOGIN_PAGE_ID = "portal-login-page"
PORTAL_MAIN_PAGE_ID = "portal-main-page"
PORTAL_KEYPAIRS_PAGE_ID = "portal-keypairs-page"
PORTAL_LAUNCHINSTANCE_PAGE_ID = "portal-launch_instance-page"

DASKHUB_LOGIN_PAGE_ID = "daskhub-login-page"
DASKHUB_SERVERSPAWN_PAGE_ID = "daskhub-server_spawn-page"
DASKHUB_MAIN_PAGE_ID = "daskhub-main-page"
DASKHUB_HOME_PAGE_ID = "daskhub-home-page"
DASKHUB_CLASSIC_PAGE_ID = "daskhub-classic-page"

# pylint: disable=too-many-branches
# pylint: disable=unused-argument
# pylint: disable=too-many-arguments
# pylint: disable=too-many-statements


def get_url(base_url, page):
    """
    Get the full URL from the base and page identifier.
    """
    if page == PORTAL_LOGIN_PAGE_ID:
        return base_url
    if page == PORTAL_MAIN_PAGE_ID:
        return base_url
    if page == PORTAL_KEYPAIRS_PAGE_ID:
        return f"{base_url}/keypairs"
    if page == PORTAL_LAUNCHINSTANCE_PAGE_ID:
        return f"{base_url}/launch_instance"

    if page == DASKHUB_LOGIN_PAGE_ID:
        return base_url
    if page == DASKHUB_HOME_PAGE_ID:
        return f"{base_url}/hub/home"

    raise NotImplementedError(f"page {page} not supported")


def do_enter_text(driver, text, field, page):
    """
    Find a text input and enter text into it.
    """
    input_element = find_element_by_text_type_page(driver, field, "input", page)
    try:
        print(input_element.get_attribute("innerHTML"))
        input_element.send_keys(text)
    except:
        print(input_element.get_attribute("innerHTML"))
        raise


def do_click(driver, text, page, element_type="button"):
    """
    Find a button and click it.
    """
    button = find_element_by_text_type_page(driver, text, element_type, page)

    # Some links require mouse over before clicking.
    ActionChains(driver).move_to_element(button).perform()

    try:
        button.click()
    except:
        print(button.get_attribute("innerHTML"))
        raise


def do_double_click(driver, text, page, element_type="button"):
    """
    Find a button and click it.
    """
    button = find_element_by_text_type_page(driver, text, element_type, page)

    # Some links require mouse over before clicking.
    ActionChains(driver).move_to_element(button).double_click().perform()


def do_select_from_dropdown(driver, text, field, page):
    """
    Find a dropdown and select an item by name in it.
    """
    dropdown = find_element_by_text_type_page(driver, field, "dropdown", page)
    try:
        dropdown.click()
    except:
        print(dropdown.get_attribute("innerHTML"))
        raise

    dropdown.send_keys(text)


def find_element_by_text_type_page(driver, text, element_type, page):
    """
    Find an element.
    """

    ret = None
    if element_type == "daskhub-folder-item":
        xpath = f"//span[text() = '{text}']/.."
        ret = driver.find_element(By.XPATH, xpath)

    if element_type == "button":
        if text == "Close":
            if page == PORTAL_KEYPAIRS_PAGE_ID:
                ret = driver.find_element(By.XPATH, "/html/body/div/div[1]/button")
        elif text == "Sign in":
            ret = driver.find_element(By.NAME, "signInSubmitButton")
        elif text == "Create Key Pair":
            ret = driver.find_element(By.NAME, "create_keypair")
        elif text == "Download Keypair File":
            ret = driver.find_element(By.XPATH, "/html/body/div/div[1]/a")
        elif text == "Launch Instance":
            ret = driver.find_element(By.NAME, "launch_type")
        elif page == PORTAL_LAUNCHINSTANCE_PAGE_ID:
            if text.startswith("ami-"):
                # It's an AMI, the identifier of the radio button
                # will match
                ret = driver.find_element(By.ID, text)
            elif (
                "-ami-" in text
                or "Deep Learning AMI" in text
                or "Deep Learning OSS" in text
                or "HVM" in text
                or "hvm" in text
            ):
                # It's an AMI by name, we need to select the previous
                # sibling element.
                xpath = f"//*[text()[contains(.,'{text}')]]/../input"
                ret = driver.find_element(By.XPATH, xpath)
            elif text.startswith(("t2.", "m5.", "c5.", "r5.", "g4dn.")):
                # It's an Instance type, the identifier of the radio button
                xpath = f"//input[@id='{text}' and @value='{text}' and @type='radio']"
                ret = driver.find_element(By.XPATH, xpath)
            else:
                # It's those tab buttons
                #  Amazon Linux -> Amazon-Linuxtab
                button_id = f"{text.replace(' ', '-')}tab"
                ret = driver.find_element(By.ID, button_id)
        elif page == DASKHUB_SERVERSPAWN_PAGE_ID:
            if text == "Server":
                value_text = "server"
                xpath = f"//input[@value='{value_text}' and @type='radio']"
                ret = driver.find_element(By.XPATH, xpath)
            elif text == "Large Server":
                value_text = "large-server"
                xpath = f"//input[@value='{value_text}' and @type='radio']"
                ret = driver.find_element(By.XPATH, xpath)
            elif text == "GPU Server - X-Large":
                value_text = "gpu-server-x-large"
                xpath = f"//input[@value='{value_text}' and @type='radio']"
                ret = driver.find_element(By.XPATH, xpath)
            elif text == "Start":
                xpath = f"//input[@value='{text}' and @type='submit']"
                ret = driver.find_element(By.XPATH, xpath)
        elif page == DASKHUB_MAIN_PAGE_ID:
            if text == "File":
                xpath = "//div[text() = 'File']"
                ret = driver.find_element(By.XPATH, xpath)
            elif text == "Log Out":
                xpath = "//div[text() = 'Log Out']"
                ret = driver.find_element(By.XPATH, xpath)
        elif page == DASKHUB_HOME_PAGE_ID:
            if text == "Stop My Server":
                xpath = "//a[@id='stop']"
                ret = driver.find_element(By.XPATH, xpath)
            elif text == "Logout":
                xpath = "//a[@id='logout']"
                ret = driver.find_element(By.XPATH, xpath)
        # Classic Jupyter Notebook Page (Runtime: 2023.12.06)
        elif text == "restart the kernel, then re-run the whole notebook (with dialog)":
            xpath = f"//button[@title = '{text}']"
            ret = driver.find_element(By.XPATH, xpath)
        elif text == "Restart and Run All Cells":
            xpath = f"//button[text() = '{text}']"
            ret = driver.find_element(By.XPATH, xpath)
        # Classic Jupyter Notebook Page (Runtime: 2024.09.13)
        elif text == "Restart the kernel and run all cells":
            xpath = f"//jp-button[@data-command='notebook:restart-run-all']"
            ret = driver.find_element(By.XPATH, xpath)
        elif text == "Restart":
            xpath = f"//div[@aria-label='Confirm Kernel Restart']"
            ret = driver.find_element(By.XPATH, xpath)

    if element_type == "input":
        if text == "username":
            ret = driver.find_element(By.ID, "signInFormUsername")
        elif text == "password":
            ret = driver.find_element(By.ID, "signInFormPassword")
        elif text == "key-pair-name":
            ret = driver.find_element(By.ID, "keypair_name")
        elif text == "Volume Size (GB)":
            ret = driver.find_element(By.ID, "volume_size")
        elif text == "Instance Name":
            ret = driver.find_element(By.ID, "instance_name_for_custom")

    if element_type == "dropdown":
        if text == "Select Key Pair":
            ret = driver.find_element(By.ID, "key_pair")

    if ret is None:
        raise NotImplementedError(
            f'Selecting {element_type} with "{text}" on page {page} is not implemented'
        )
    return ret


def get_timeout_for_field(text, element_type, page):
    """
    Get the time in second we should wait before giving up
    when selecting a specific field.
    """
    ret = 5
    if element_type == "button":
        if text == "Download Keypair File":
            ret = 10
    if element_type == "button":
        if text == "Log Out":
            ret = 10
    return ret


def do_wait_for_element(driver, text, element_type, page, timeout, screenshot_file):
    """
    Wait for an element to appear and return it.
    """
    start_time = time.time()

    if screenshot_file is not None:
        webdriver_screenshot(driver, screenshot_file)

    while (time.time() - start_time) < timeout:
        try:
            return find_element_by_text_type_page(driver, text, element_type, page)
        except NoSuchElementException:
            time.sleep(0.5)

        if screenshot_file is not None:
            webdriver_screenshot(driver, screenshot_file)

    return find_element_by_text_type_page(driver, text, element_type, page)


def do_wait_for_element_not_present(driver, xpath, page, timeout, screenshot_file):
    """
    Wait for an element to appear and return it.
    """
    start_time = time.time()

    if screenshot_file is not None:
        webdriver_screenshot(driver, screenshot_file)

    while (time.time() - start_time) < timeout:
        try:
            driver.find_element(By.XPATH, xpath)
            time.sleep(0.5)
        except NoSuchElementException:
            return True

        if screenshot_file is not None:
            webdriver_screenshot(driver, screenshot_file)

    return False
