import os
import threading
import time
import logging
import pandas as pd
import datetime

logger = logging.getLogger(__name__)

from directory_utility.utility import get_immediate_subdirectories
from generic_utility.utility import exception, notify


def get_pips(CROSS, body):
    CROSS = CROSS.upper()
    if 'JPY' in CROSS or 'XAU' in CROSS or 'XAG' in CROSS:
        multiply = 100.0
    else:
        multiply = 10000.0
    return body * multiply


class ManualScan(object):
    def __init__(self, base_path):
        self.path = os.path.join(base_path, 'manual')
        self.rest_period = 60
        self.info = []
        self.objects = {}
        self.prices = {}
        self.lock = threading.Lock()
        self.last_notification = None

    @exception
    def read_objects(self, path, symbol):
        self.objects[symbol] = pd.read_csv(path)

    def get_trend_line(self, symbol, bearish=False):
        trends = self.objects[symbol][self.objects[symbol]["Type"] == "TREND"]
        res = []
        for index, row in trends.iterrows():
            name = row['name']
            if bearish and 'bullish' in name:
                continue
            if not bearish and 'bearish' in name:
                continue
            name = name.replace('service.', "")
            diff = row['dist']
            diff = float(diff)
            diff = get_pips(symbol, diff)
            diff = round(diff, 2)
            res.append({'name': str(name), 'dist': diff})
        return res

    def get_lines(self, symbol, bearish=False):
        lines = self.objects[symbol][self.objects[symbol]["Type"] == "HLINE"]
        res = []
        for index, row in lines.iterrows():
            name = row['name']
            if bearish and 'bullish' in name:
                continue
            if not bearish and 'bearish' in name:
                continue
            name = name.replace('service.', "")
            diff = row['dist']
            diff = float(diff)
            diff = get_pips(symbol, diff)
            diff = round(diff, 2)
            res.append({'name': str(name), 'dist': diff})
        return res

    def get_symbols(self):
        return get_immediate_subdirectories(self.path)

    def loop_and_update(self):
        while True:
            self.run()
            self.send_notifications()
            time.sleep(self.rest_period)

    def run(self):
        with self.lock:
            subs_first_level = self.get_symbols()
            logger.info("Manual Thread: Symbols: " + str(subs_first_level))
            for symbol in subs_first_level:
                dir = os.path.join(self.path, symbol)
                files = os.listdir(dir)
                for file in files:
                    if file == "objects":
                        self.read_objects(os.path.join(dir, file), symbol)
                    elif file == "price":
                        self.read_price(os.path.join(dir, file), symbol)
                    else:
                        logger.warning("Skipping file: %s " % file)
            self.last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    @exception
    def read_price(self, param, symbol):
        self.prices[symbol] = pd.read_csv(param)

    @exception
    def get_info(self):
        to_return = []
        symbols1 = {*self.objects}
        symbols2 = {*self.prices}
        assert symbols1 == symbols2
        with self.lock:
            for symbol in symbols1:
                last_close = float(self.prices[symbol]['CLOSE'].iloc[-1])
                trend_bearish = self.get_trend_line(symbol, bearish=True)
                trend_bullish = self.get_trend_line(symbol, bearish=False)
                line_bullish = self.get_lines(symbol, bearish=False)
                line_bearish = self.get_trend_line(symbol, bearish=True)
                to_return.append({'symbol': symbol, 'close': last_close, 'trend_bearish': trend_bearish,
                                  'trend_bullish': trend_bullish, 'line_bearish': line_bearish,
                                  'line_bullish': line_bullish, 'last_update': self.last_update})
        return to_return

    def send_notifications(self):
        if self.last_notification is None:
            self.last_notification = datetime.datetime.now()

        if (datetime.datetime.now() - self.last_notification).total_seconds() < 60 * 15:
            return
        else:
            self.last_notification = datetime.datetime.now()

        symbols1 = {*self.objects}
        for symbol in symbols1:
            trend_bearish = self.get_trend_line(symbol, bearish=True)
            trend_bullish = self.get_trend_line(symbol, bearish=False)
            line_bullish = self.get_lines(symbol, bearish=False)
            line_bearish = self.get_trend_line(symbol, bearish=True)

            self.send_actual_notification_threshold(trend_bullish, symbol)
            self.send_actual_notification_threshold(trend_bearish, symbol)
            self.send_actual_notification_threshold(line_bullish, symbol)
            self.send_actual_notification_threshold(line_bearish, symbol)

    def send_actual_notification_threshold(self, objs, symbol, threshold=15):
        for obj in objs:
            if obj['dist'] < threshold:
                notify(symbol, str(obj))
