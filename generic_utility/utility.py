import functools
import logging
import time
import threading
from datetime import datetime
from scipy.stats.stats import pearsonr
from itertools import combinations
from notifications.email import try_to_send_email
from pathlib import Path
import os
import http.client, urllib

logger = logging.getLogger(__name__)


def exception(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        exc = None
        for i in range(1, 4):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                # log the exception
                err = "There was an exception in  "
                err += function.__name__
                logger.exception(err)
                logger.exception(e)
                exc = e
                time.sleep(5)

        logger.error("Unable to fix Exception .. raising")
        raise exc

    return wrapper


def notify_the_boss(message):
    try_to_send_email(message)


def pushover(msg, cross):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
                 urllib.parse.urlencode({
                     "user": "gbwc2km9qz9yi6pkew11z9mfx29qik",
                     "message": msg,
                     'title': cross,
                     'token': "apq8s9bb2eq9ps58ktvhfihaxj2kzg",
                 }), {"Content-type": "application/x-www-form-urlencoded"})
    response = conn.getresponse()
    return response.status


def notify(msg, CROSS):
    os.environ["PATH"] += os.pathsep + str(Path(__file__).parent.parent) + "/lib"
    status = pushover(msg, CROSS)
    if status == 200:
        return
    print('ERROR ')
    print(status)
    msg = "[" + CROSS + "] " + msg
    th = threading.Thread(target=notify_the_boss, args=(msg,))
    th.start()

    msg = "CRASH PUSHOVER "
    th = threading.Thread(target=notify_the_boss, args=(msg,))
    th.start()


def remove_month(data):
    for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
        data = data.replace(m, "")
    for m in ["Q1", "Q2", "Q3", "Q4"]:
        data = data.replace(m, "")

    data = data.replace("(", "")
    data = data.replace(")", "")
    data = data.replace(" ", "")
    return data


def remove_symbols(x):
    x = x.replace(',', '')
    if '%' in x:
        x = x.replace('%', '')
        x = float(x) / 100.0
    elif 'B' in x:
        x = x.replace('B', '')
        x = float(x) * 1000000000
    elif ('K' in x) or ('k' in x):
        x = x.replace('K', '').replace('k', '')
        x = float(x) * 1000.0
    elif 'M' in x:
        x = x.replace('M', '')
        x = float(x) * 1000000
    elif 'T' in x:
        x = x.replace('T', '')
        x = float(x) * 1000000000000
    return round(float(x), 4)


def get_msg_calendar(df, last_msgs):
    df['Event'] = df['Event'].apply(lambda x: remove_month(x))
    df = df[df['Actual'].notnull()]
    df = df[~df['Time'].str.contains("Tentative")]
    df = df[df['Sentiment'] != 'None']
    df = df[df['Actual'] != '']
    df = df[df['Forecast'] != '']
    df['Actual'] = df['Actual'].apply(lambda x: remove_symbols(x))
    df['Forecast'] = df['Forecast'].apply(lambda x: remove_symbols(x))
    df = df[df['Volatility'] != 'Low Volatility Expected']
    crs = set(list(df['Currency']))
    rank = []
    one_notify = False
    for cur in crs:
        tmp = df[df['Currency'] == cur]
        #tmp = tmp.tail(12)
        pos = 0
        res = ""
        for index, row in tmp.iterrows():
            expect = row['Forecast']
            real = row['Actual']
            sent = row['Sentiment']
            if expect == 0:
                continue
            if sent != 'Neutro':
                perc = round((abs(real - expect)/abs(expect)) *100.0, 2)
                perc = 1
            if 'High' in row['Volatility']:
                weight = 1.3
            else:
                weight = 0.9
            if sent == 'Better':
                pos += weight*perc
            elif sent == 'Worse':
                pos -= weight*perc
            elif sent == 'Neutro':
                pos += round(weight / 3.0, 3)

            else:
                notify("Error" + str(row), 'Calendar')
            res += "Event: " + row['Event'] + '\n' + ' Result: ' + str(sent) + "\n" + 'Expected: ' + str(
                row['Forecast']) + '\n' + 'Actual: ' + str(row['Actual']) + "\n\n"

        pos = round(pos, 3)
        rank.append((cur, pos))
        res += "\n\nSummary is: " + str(pos)

        if cur not in last_msgs:
            last_msgs[cur] = ''

        if last_msgs[cur][0:30] != res[0:30]:
            one_notify = True
            #notify(res, cur)

        last_msgs[cur] = res

    rank.sort(key=lambda tup: tup[1])
    rank.reverse()
    msg = ""
    for i in rank:
        msg += str(i) + "\n"

    if one_notify:
        notify(msg, 'Summary Calendar')


    return last_msgs

def correlation(dirs):
    all_symbols = list(dirs.keys())
    pair = [list(x) for x in combinations(all_symbols, 2)]
    res = []
    for p in pair:
        a = dirs[p[0]].copy().tail(500)
        b = dirs[p[1]].copy().tail(500)
        a = a['BODY']
        b = b['BODY']
        coerr, pvalue = pearsonr(list(a), list(b))
        coerr = round(coerr, 4)
        if( abs(coerr)) >= 0.6:
            res.append((coerr, pvalue, (str(p[0]) + "-" + str(p[1]))))

    res.sort(key=lambda tup: tup[0])
    res.reverse()

    res = ["\n" + str(x[2]) + " \nCoerr: " + str(x[0]) + "\npValue: " + str(x[1]) for x in res]
    msg = "\n".join(res)
    notify(msg, "Correlation")