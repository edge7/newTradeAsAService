import datetime
import re
from bs4 import BeautifulSoup
import logging
import sys
from dateutil import parser

logger = logging.getLogger(__name__)

countries = [
    'country25', #Australia
    'country72',# Eurozone
    'country22',#France
    'country17',#Germany
    'country51', #Greece
    'country10',#Italy
    'country26',#Spain
    'country12',#Swiss
    'country4',#UK
    'country5',#US,
    'country43', #NZD,
    'country35',#Japan,
    'country6',#Canada
    'country37',#China
]
def remove_month(data):
    for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
        data = data.replace(m, "")
    for m in ["Q1", "Q2", "Q3", "Q4"]:
        data = data.replace(m, "")

    data = data.replace("(", "")
    data = data.replace(")", "")
    return data.strip()


def fix_numbers(x):
    #if x == "" or x == " " or x.replace(" ", '') == "":
    #    return x
    x = x.replace(',', '')
    if 'K' in x:
        return float(x.replace('K', '')) * 1000.0
    if 'M' in x:
        return float(x.replace('M', '')) * 1000000.0
    if 'B' in x:
        return float(x.replace('B', '')) * 1000000000.0
    if 'T' in x:
        return float(x.replace('T', '')) * 1000000000000.0
    if '%' in x:
        return float(x.replace('%', '')) / 100.0
    try:
        return float(x)
    except Exception as e:
        logger.error(e)
        logger.error(x)
    return None


def process_html(html):
    soup = BeautifulSoup(html, features="html5lib")
    l = soup.select("tbody")

    tbody = None
    for elem in l:
        if 'id' in elem.parent.attrs and 'economicCalendarData' in elem.parent.attrs['id']:
            tbody = elem
            break

    if tbody is None:
        logger.error("Table not found")
        sys.exit(1)

    to_return = []

    for row in tbody.select('tr'):
        counter = 0

        for column in row.select('td'):

            if 'id' in column.attrs and 'theDay' in column.attrs['id']:
                counter = -1
                date = parser.parse(column.text)
                continue

            if 'class' in column.attrs and 'time' in column.attrs['class'] and 'js-time' in column.attrs['class']:
                counter += 1
                try:
                    hour = column.text.split(':')[0]
                    minute = column.text.split(':')[1]
                    dateandtime = date + datetime.timedelta(hours=int(hour)) + datetime.timedelta(minutes=int(minute))

                except IndexError:
                    logger.warning("Not numeric date: " + str(column.text))
                    dateandtime = str(date)

                continue

            if 'class' in column.attrs and 'flagCur' in column.attrs['class']:
                currency = column.text[2:]
                # currency = str(currency.encode('utf-8'))
                currency = re.sub("[^a-zA-Z]+", "", currency)
                counter += 1
                continue

            if 'class' in column.attrs and 'sentiment' in column.attrs['class']:
                try:
                    volatility = column.attrs['title']
                except KeyError:
                    logger.warning('Sentiment: ' + column.text)
                    volatility = column.text
                counter += 1
                continue

            if 'class' in column.attrs and 'event' in column.attrs['class']:
                event = column.text
                event = remove_month(event)
                counter += 1
                continue

            if 'id' in column.attrs and 'eventActual' in column.attrs['id']:
                actual = column.text
                actual = fix_numbers(actual)
                # actual = str(actual.encode('utf-8'))
                sent = column.attrs.get('title', '')
                if 'Better' in sent:
                    sent = "Better"
                elif 'Worse' in sent:
                    sent = "Worse"
                elif 'Line' in sent:
                    sent = 'Neutro'
                else:
                    sent = 'None'
                counter += 1
                continue

            if 'id' in column.attrs and 'eventForecast' in column.attrs['id']:
                forecast = column.text
                forecast = fix_numbers(forecast)
                counter += 1
                continue

            if 'id' in column.attrs and 'eventPrevious' in column.attrs['id']:
                previous = column.text
                previous = fix_numbers(previous)
                # previous = str(previous.encode('utf-8'))
                counter += 1
                continue

        assert counter == 7 or counter == -1 or volatility == "Holiday"

        if counter == 7:
            d = {'Time': str(dateandtime).strip(), 'Previous': previous, 'Forecast': forecast,
                 'Actual': actual, 'Event': event.strip(), 'Volatility': volatility.strip(),
                 'Currency': currency.strip(), 'Sentiment': sent}
            to_return.append(d)

        if counter == -1:
            logger.info("New Day: " + str(date))

    return to_return
