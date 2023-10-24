"""
Contains functions for interacting with the selenium
webdriver.
"""
import os
import time

from pathlib import Path

from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

DEBUG = True


def create_webdriver():
    """
    Create the webdriver.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--remote-allow-origins=*")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=320,2840")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def webdriver_get(driver, url, time_to_wait, screenshot_file):
    """
    Load a page in the browser.
    """
    if DEBUG:
        print(f"Going to: {url}")

    start_time = time.time()
    driver.get(url)
    end_time = time.time()

    if time_to_wait is not None:
        if DEBUG:
            print(f"Waiting {time_to_wait} second(s)")

        time.sleep(time_to_wait)

    if DEBUG:
        print(f"Request took {end_time - start_time} second(s)")

    if screenshot_file is not None:
        if DEBUG:
            print(f"Capturing a screenshot and saving to {screenshot_file}")
        path = Path(screenshot_file)

        os.makedirs(path.parent.absolute(), 777, True)
        driver.get_screenshot_as_file(screenshot_file)


def webdriver_screenshot(driver, screenshot_file):
    """
    Capture a screenshot.
    """
    if screenshot_file is not None:
        if DEBUG:
            print(f"Capturing a screenshot and saving to {screenshot_file}")
        path = Path(screenshot_file)

        os.makedirs(path.parent.absolute(), 777, True)
        driver.get_screenshot_as_file(screenshot_file)
