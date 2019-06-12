import time
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/39.0.2171.95 Safari/537.36'}

    try:
        with closing(get(url, headers = headers,  stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors.
    This function just prints them, but you can
    make it do anything.
    """
    logger.error(e)


class YieldsSpread(object):
    def __init__(self):
        self.rest_period = 60
        self.URL = 'https://www.investing.com/rates-bonds/government-bond-spreads'

    def loop_and_update(self):
        while True:
            self.run()
            time.sleep(self.rest_period)

    def run(self):
        html = simple_get(self.URL)
        html = BeautifulSoup(html, 'html.parser')
        table_to_use = None
        for table in html.select('table'):
            if table['id'] == "bonds":
                table_to_use = table
                break
        if table_to_use is None:
            logger.error("Unable to find Table Bonds")
            return
        data = None
        for row in table.children:
            if 'Australia' in row.text:
                data = row.text
                break
        if data is None:
            logger.error("Unable to find data")
            return
        for country in row.children:
            for info in country.children:
                print(info)
        print(countries)


y = YieldsSpread()
y.loop_and_update()