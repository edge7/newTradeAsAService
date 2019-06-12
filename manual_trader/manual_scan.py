import os
import threading
import time
import logging
import pandas as pd
import datetime

from calendarEconomic.process import get_calendar
from manual_trader.keep_eye import SELL, BUY
from plot_utility.plot import create_chart_with_objects

logger = logging.getLogger(__name__)

from directory_utility.utility import get_immediate_subdirectories
from generic_utility.utility import exception, notify, get_msg_calendar, correlation


def get_pips(CROSS, body):
    CROSS = CROSS.upper()
    if 'JPY' in CROSS or 'XAU' in CROSS or 'XAG' in CROSS or 'WTI' in CROSS:
        multiply = 100.0
    else:
        multiply = 10000.0
    return body * multiply


class ManualScan(object):
    def __init__(self, base_path):
        self.shapes = {}
        self.path = os.path.join(base_path, 'manual')
        self.rest_period = 60 * 5
        self.info = []
        self.objects = {}
        self.prices = {}
        self.lock = threading.Lock()
        self.last_notification = None
        self.last_notification_calendar = None
        self.calendar = {}

    @exception
    def read_objects(self, path, symbol):
        old_objects = self.objects.get(symbol, None)
        self.objects[symbol] = pd.read_csv(path)
        if old_objects is None:
            return
        old_rows = old_objects.shape[0]
        new_rows = self.objects[symbol].shape[0]
        if old_rows != new_rows:
            return
        for i in range(old_rows):
            row_old = old_objects.iloc[i]
            row_new = self.objects[symbol].iloc[i]
            old_diff = row_old['dist']
            new_diff = row_new['dist']
            if old_diff * new_diff < 0:
                now = "Now is Up"
                if new_diff < 0:
                    now = "Now is Down"

                msg = "Possible (False) Breakout " + row_new['Type'] + " - " + now + "\n"
                msg += "Name Line is: " + row_new['name']
                notify(msg, symbol)

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
                    elif file == "price.csv":
                        self.read_price(os.path.join(dir, file), symbol)
                    else:
                        logger.warning("Skipping file: %s " % file)
            self.last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

            if self.last_notification_calendar is None:
                self.last_notification_calendar = datetime.datetime.now()

            elif (datetime.datetime.now() - self.last_notification_calendar).total_seconds() < 12 * 60 * 60:
                return

            self.last_notification_calendar = datetime.datetime.now()
            start_datetime = datetime.datetime.today() - datetime.timedelta(days=46)
            end = datetime.datetime.today()
            #rows = get_calendar(start_datetime.strftime('%d/%m/%Y'), end.strftime('%d/%m/%Y'))
            #calendar = pd.DataFrame(pd.DataFrame(rows).sort_values(by=['Time']))
            #self.calendar = get_msg_calendar(calendar, self.calendar)


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
                last_close = round(float(self.prices[symbol]['CLOSE'].iloc[-1]), 4)
                trend_bearish = self.get_trend_line(symbol, bearish=True)
                trend_bullish = self.get_trend_line(symbol, bearish=False)
                line_bullish = self.get_lines(symbol, bearish=False)
                line_bearish = self.get_lines(symbol,
                                              bearish=True)
                rsi = self.prices[symbol]["RSI"].iloc[-1]
                dist_bb_25_up = int(get_pips(symbol, self.prices[symbol]["DIST_BB_25_UP"].iloc[-1]))
                dist_bb_25_down = int(get_pips(symbol, self.prices[symbol]["DIST_BB_25_DOWN"].iloc[-1]))
                to_return.append({'symbol': symbol, 'close': last_close, 'trend_bearish': trend_bearish,
                                  'trend_bullish': trend_bullish, 'line_bearish': line_bearish,
                                  'line_bullish': line_bullish, 'last_update': self.last_update,
                                  'rsi': rsi, 'dist_bb_up': dist_bb_25_up, 'dist_bb_down': dist_bb_25_down})
        return to_return

    def send_notifications(self):
        if self.last_notification is None:
            self.last_notification = datetime.datetime.now()
        elif (datetime.datetime.now() - self.last_notification).total_seconds() < 60 * 5:
            return
        else:
            self.last_notification = datetime.datetime.now()

        symbols1 = {*self.objects}
        ok = False
        for symbol in symbols1:
            old_shape = self.shapes.get(symbol, 0)
            if old_shape != self.prices[symbol].shape[0]:
                self.shapes[symbol] = self.prices[symbol].shape[0]
            else:
                continue
            trend_bearish = self.get_trend_line(symbol, bearish=True)
            trend_bullish = self.get_trend_line(symbol, bearish=False)
            line_bullish = self.get_lines(symbol, bearish=False)
            line_bearish = self.get_lines(symbol, bearish=True)
            pin_bar_up = self.get_pin_bar_up(symbol)
            pin_bar_down = self.get_pin_bar_down(symbol)
            ok =True
            self.send_actual_notification_threshold(trend_bullish, symbol)
            self.send_actual_notification_threshold(trend_bearish, symbol)
            self.send_actual_notification_threshold(line_bullish, symbol)
            self.send_actual_notification_threshold(line_bearish, symbol)
            rsi = self.prices[symbol]["RSI"].iloc[-1]
            dist_bb_25_up = int(get_pips(symbol, self.prices[symbol]["DIST_BB_25_UP"].iloc[-1]))
            dist_bb_25_down = int(get_pips(symbol, self.prices[symbol]["DIST_BB_25_DOWN"].iloc[-1]))

            if rsi < 27 or rsi > 73:
                 notify(symbol, "RSI: " + str(rsi))
            if pin_bar_down:
                notify(symbol, 'PIN_BAR_DOWN (BUY)' )
            if pin_bar_up:
                notify(symbol, 'PIN_BAR_UP (SELL)')
            #
            # if dist_bb_25_up > -5:
            #     notify(symbol, "Bollinger UP: " + str(dist_bb_25_up))
            #
            # if dist_bb_25_down < 5:
            #     notify(symbol, "Bollinger DOWN: " + str(dist_bb_25_down))

            # self.analyse_high_and_low(symbol)
            # self.notify_trends(symbol, avg=25, long=20)
            #self.notify_break(symbol, avg=25, long=20)
            #self.notify_buy_sell(symbol, avg=25)
        if ok:
            correlation(self.prices)

    def send_actual_notification_threshold(self, objs, symbol, threshold=50):
        for obj in objs:
            if abs(obj['dist']) < threshold:
                notify(symbol, "TREND LINE " + str(obj))

    def analyse_high_and_low(self, symbol):
        # LOWINPIPS, HIGHINPIPS
        df = self.prices[symbol].copy()
        df['AVG_LOW'] = df['LOWINPIPS'].rolling(window=5).mean()
        if df['AVG_LOW'].iloc[-1] < df['LOWINPIPS'].iloc[-1] and get_pips(symbol, df['LOWINPIPS'].iloc[-1]) > 15:
            notify(symbol, "LOW Signal")

        df['AVG_HIGH'] = df['HIGHINPIPS'].rolling(window=5).mean()
        if df['AVG_HIGH'].iloc[-1] < df['HIGHINPIPS'].iloc[-1] and get_pips(symbol, df['HIGHINPIPS'].iloc[-1]) > 15:
            notify(symbol, "HIGH Signal")

    def create_chart(self, symbol):
        with self.lock:
            return create_chart_with_objects(self.prices[symbol], symbol, self.objects[symbol])

    def notify_trends(self, symbol, avg=20, long=10):
        def consecutive_mean(x):
            pos = 0
            neg = 0
            for j in x:
                if j >= 0:
                    pos += 1
                else:
                    neg += 1
            if pos == len(x):
                return 1
            if neg == len(x):
                return -1
            return 0

        df = self.prices[symbol].copy()
        # APPLY AVG
        df['AVG'] = df['CLOSE'] - df['CLOSE'].ewm(span=avg).mean()
        df['consecutive'] = df['AVG'].rolling(window=long).apply(lambda x: consecutive_mean(x))
        trending = ""
        if df['consecutive'].iloc[-1] == 1:
            trending = 1
        if df['consecutive'].iloc[-1] == -1:
            trending = -1
        if trending != "":
            for i in range(1, 30, 1):
                df['target' + str(i)] = -df['CLOSE'].diff(-i)
                df['target' + str(i)] = df['target' + str(i)].apply(lambda x: get_pips(symbol, x))

            df = df[df['consecutive'] == trending]
            to_send = []
            for i in range(1, 30, 1):
                to_send.append('Ahead: ' + str(i) + 'pips: ' + str(df['target' + str(i)].mean()))
            to_send = "\n".join(to_send)

            if trending == 1:
                trending = "UP"
            else:
                trending = "DOWN"

            notify("TRENDING: " + trending + "\n" + to_send, symbol)

    def notify_break(self, symbol, avg=20, long=10):
        def consecutive_mean(x):
            pos = 0
            neg = 0
            for j in x:
                if j >= 0:
                    pos += 1
                else:
                    neg += 1
            if pos == len(x):
                return 1
            if neg == len(x):
                return -1
            return 0

        df = self.prices[symbol].copy()

        # APPLY AVG
        df['AVG'] = df['CLOSE'] - df['CLOSE'].ewm(span=avg).mean()
        df['consecutive'] = df['AVG'].rolling(window=long).apply(lambda x: consecutive_mean(x))
        trending = ""

        if df['consecutive'].iloc[-1] == 0 and df['consecutive'].iloc[-2] == 1:
            trending = "Possible retracement DOWN"

        if df['consecutive'].iloc[-1] == 0 and df['consecutive'].iloc[-2] == -1:
            trending = "Possible retracement UP"

        if trending != "":
            for i in range(1, 30, 1):
                df['target' + str(i)] = -df['CLOSE'].diff(-i)
                df['target' + str(i)] = df['target' + str(i)].apply(lambda x: get_pips(symbol, x))

            df['consecutive_'] = df['consecutive'].shift(1)
            if 'UP' in trending:
                df = df[(df['consecutive'] == 0) & (df['consecutive_'] == -1)]
            else:
                df = df[(df['consecutive'] == 0) & (df['consecutive_'] == 1)]

            to_send = []
            for i in range(1, 30, 1):
                to_send.append('Ahead: ' + str(i) + 'pips: ' + str(df['target' + str(i)].mean()))
            to_send = "\n".join(to_send)

            notify("BREAKING AVG20: " + trending + "\n" + to_send, symbol)

        # Look for pullback
        tot = 0
        pos = 0
        neg = 0
        for dist in list(df['AVG'].tail(60)):
            if dist >= 0:
                pos += 1
            if dist <= 0:
                neg += 1
            tot += 1
        pos = pos / tot
        neg = neg / tot
        if pos >= 0.8:
            l = list(df['AVG'].tail(3))
            if l[2] > 0 > l[1] and l[0] < 0:
                notify("Possible Pullback (BUY)", symbol)

        if neg >= 0.8:
            l = list(df['AVG'].tail(3))
            if l[2] < 0 and l[1] > 0 and l[0] > 0:
                notify("Possible Pullback (SELL)", symbol)

    def notify_buy_sell(self, symbol, avg):
        return
        df = self.prices[symbol].copy()
        df['AVG'] = df['CLOSE'] - df['CLOSE'].ewm(span=avg).mean()
        last = df['AVG'].iloc[-1]
        penu = df['AVG'].iloc[-2]

        if symbol in SELL:
            if last < 0 < penu:
                notify("You might Want to SELL " + symbol + " now", symbol)

        if symbol in BUY:
            if penu < 0 < last:
                notify("You might Want to BUY " + symbol + " now", symbol)

    def get_pin_bar_up(self, symbol):
        df = self.prices[symbol].copy()
        last_close = df['CLOSE'].iloc[-1]
        close_ago = df['CLOSE'].iloc[-4]
        if last_close > close_ago:
            body = df['BODY'].iloc[-1]
            highp = df['HIGHINPIPS'].iloc[-1]
            lowp = df['LOWINPIPS'].iloc[-1]
            if body * 2.2 < highp and lowp *1.3 < highp:
                return True
        return False

    def get_pin_bar_down(self, symbol):
        df = self.prices[symbol].copy()
        last_close = df['CLOSE'].iloc[-1]
        close_ago = df['CLOSE'].iloc[-4]
        if last_close < close_ago:
            body = df['BODY'].iloc[-1]
            highp = df['HIGHINPIPS'].iloc[-1]
            lowp = df['LOWINPIPS'].iloc[-1]
            if body * 2.2 < lowp and highp *1.3 < lowp:
                return True
        return False

