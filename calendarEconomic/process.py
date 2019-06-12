from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import pandas as pd
from pathlib import Path
import os
import time
from selenium.webdriver.common.keys import Keys


from datetime import timedelta

from calendarEconomic.processer import process_html, countries


def scroll_down(driver):
    """A method for scrolling the page."""

    # Get scroll height.
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load the page.
        time.sleep(10)

        # Calculate new scroll height and compare with last scroll height.
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    print("Page is loaded")


def get_calendar(start, end):
    print(start)
    print(end)

    print("----\n\n")
    os.environ["PATH"] += os.pathsep + str(Path(__file__).parent.parent) + "\\lib"

    # launch url
    url = "https://uk.investing.com/economic-calendar/"

    # create a new Firefox session
    options = webdriver.ChromeOptions()
    options.add_argument(r"user-data-dir=C:\\Users\\Administrator\\Desktop\\wapp")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(30)
    driver.get(url)

    python_button = driver.find_element_by_id('filterStateAnchor')
    python_button.click()
    time.sleep(3)
    elemts = driver.find_elements_by_tag_name('a')
    element = None
    for i in elemts:
        if i.text == 'Clear':
            element = i
            break

    if element is None:
        raise Exception('boom')

    element.click()

    for c in countries:
        driver.find_element_by_id(c).click()

    driver.find_element_by_id('ecSubmitButton').click()
    time.sleep(5)

    for i in range(2):
        driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
        time.sleep(1)

    driver.find_element_by_id('datePickerToggleBtn').click()
    driver.find_element_by_id('startDate').clear()
    driver.find_element_by_id('startDate').send_keys(start)
    driver.find_element_by_id('endDate').clear()
    driver.find_element_by_id('endDate').send_keys(end)
    driver.find_element_by_id('applyBtn').click()

    scroll_down(driver)
    html = driver.find_element_by_tag_name('body').get_attribute('innerHTML')
    driver.close()
    return process_html(html)