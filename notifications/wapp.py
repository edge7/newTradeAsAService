# - download http://chromedriver.storage.googleapis.com/index.html?path=2.21/
# - details https://sites.google.com/a/chromium.org/chromedriver/downloads
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
import logging as logger

driver = None


def wait(web_opening_time=3):
    time.sleep(web_opening_time)


## load web driver for selenium : chrome
def web_driver_load():
    global driver
    options = webdriver.ChromeOptions()
    options.add_argument(r"user-data-dir=/home/edge7/Desktop/Documenti/wapp")
    driver = webdriver.Chrome(options=options)


def web_driver_quit():
    if (os.system("killall chrome") == 0):
        logger.info("Chrome closed")

    if (os.system("killall chrome") == 0):
        logger.info("Chrome closed")


def whatsapp_login():
    name = 'ED7-Trading signals-MAS'
    driver.get('https://web.whatsapp.com/')
    time.sleep(5)
    counter = 0
    while counter < 10:
        time.sleep(5)
        counter += 1
        try:
            appLoad = driver.find_element_by_xpath("//div[@class='_2wP_Y']")
            if appLoad:
                res = gotoChathead(name)
                if res:
                    break
                else:
                    logger.warn("Unable to find class")

        except NoSuchElementException as e:
            logger.warning(e)

        logger.info('Trying again')

    if counter == 10:
        logger.error("Message will not be sent")
        return 1

    return 0


def sendMessage(msg):
    web_obj = driver.find_element_by_xpath("//div[@contenteditable='true']")
    web_obj.send_keys(msg)
    web_obj.send_keys(Keys.RETURN)


def gotoChathead(name):
    recentList = driver.find_elements_by_xpath("//div[@class='_2wP_Y']")
    for head in recentList:
        if name in head.text:
            head.click()
            return 1
    return 0


### Main Method
def send_wapp_mess(message):
    web_driver_load()
    res = whatsapp_login()
    if res == 0:
        sendMessage(message)
        logger.info("Process complete successfully")
    web_driver_quit()

    return res
