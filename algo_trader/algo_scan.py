import os
import threading
import time
import logging
import pandas as pd
import datetime
from dateutil import parser

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


class AlgoScan(object):
    def __init__(self, base_path):
        self.path = os.path.join(base_path, 'algo')
        self.rest_period = 60 * 10
        self.lock = threading.Lock()
        self.last_notification = None
        self.orders = {}

    def get_symbols(self):
        return get_immediate_subdirectories(self.path)

    def loop_and_update(self):
        while True:
            self.run()
            self.send_notifications()
            time.sleep(self.rest_period)

    @exception
    def run(self):
        with self.lock:
            subs_first_level = self.get_symbols()
            logger.info("Scan Thread Algo: Symbols: " + str(subs_first_level))
            for symbol in subs_first_level:
                for strategy in get_immediate_subdirectories(os.path.join(self.path, symbol)):
                    dir = os.path.join(self.path, symbol, strategy)
                    files = os.listdir(dir)
                    for file in files:
                        if file == "ORDERS.csv":
                            self.read_orders(os.path.join(dir, file), symbol, strategy)
                        else:
                            logger.warning("Skipping file: %s " % file)
            self.last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    def read_orders(self, param, symbol, strategy):
        df = pd.read_csv(param)
        if self.orders.get(symbol, None) is None:
            self.orders[symbol] = {strategy: df}
        else:
            self.orders[symbol][strategy] = df

    def send_notifications(self):
        for symbol, strategy in self.orders.items():
            for strat, order in self.orders[symbol].items():
                for index, row in order.iterrows():
                    t = parser.parse(row['TIME']) - datetime.timedelta(hours=2)

                    if (datetime.datetime.now() - t).total_seconds() < 60 * 60:
                        value = "Type: " + row['TYPE'] + " -- SL:" + str(row['SL']) + " -- TP:" + str(
                            row['TP']) + " -- OPEN_AT:" + \
                                str(row['OPEN_AT']) + ' -- TIME ' + str(row['TIME'])
                        notify("[Strategy:  " + strat + " ] " + value, symbol)

    def get_info(self):
        to_return = []
        with self.lock:
            for symbol, strategy in self.orders.items():
                for strat, order in self.orders[symbol].items():
                    for index, row in order.iterrows():
                        res = {'Symbol': symbol, 'Strategy': strat, 'Type': row['TYPE'], 'SL': round(row['SL'], 4), 'TP': round(row['TP'], 4),
                               'Open_at': round(row['OPEN_AT'], 4), 'Time': row['TIME']}
                        to_return.append(res)
        return to_return

    def get_info_back_path(self, symbol, strategy):
        dir = os.path.join(self.path, symbol, strategy)
        return os.path.join(dir, 'info.png')

    def get_info_equity_path(self, symbol, strategy):
        dir = os.path.join(self.path, symbol, strategy)
        return os.path.join(dir, 'equity.png')