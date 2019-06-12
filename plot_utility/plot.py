import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates
from dateutil import parser



def create_candlestick(df, symbol):
    df = df.copy()
    df["TIME"] = df["TIME"].apply(mdates.date2num)

    ohlc = []
    for index, row in df.iterrows():
        append_me = row["TIME"], row["OPEN"], row["HIGH"], row["LOW"], row['CLOSE']
        ohlc.append(append_me)
    fig = plt.figure()
    ax1 = plt.subplot2grid((1, 1), (0, 0))
    candlestick_ohlc(ax1, ohlc, width = 0.5/(24*60), colorup='#77d879', colordown='#db3f3f')

    for label in ax1.xaxis.get_ticklabels():
        label.set_rotation(45)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.xaxis.set_major_locator(mticker.MaxNLocator(10))
    ax1.grid(False)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title(symbol)
    plt.legend()
    plt.subplots_adjust(left=0.09, bottom=0.20, right=0.94, top=0.90, wspace=0.2, hspace=0)
    return plt


def create_chart_with_objects(df, symbol, objects):
    df = df.copy()
    df['TIME'] = df['TIME'].apply(parser.parse)
    pl = create_candlestick(df, symbol)
    for index, object in objects.iterrows():
        if object['Type'] == 'TREND':
            time1 = mdates.date2num(parser.parse(object['time2']))
            time2 = mdates.date2num(df['TIME'].iloc[-1])
            if parser.parse(object['time2']) < df['TIME'].iloc[0]:
                continue
            value1 = object['price2']
            value2 = object['value']
            pl.plot([time1, time2], [value1, value2], label=object['name'])
        if object['Type'] == 'HLINE':
            value = object['value']
            plt.hlines(value,xmin=mdates.date2num(df['TIME'].iloc[0]), xmax=mdates.date2num(df['TIME'].iloc[-1]), label=object['name'])
    plt.legend()

    pl.savefig('C:\\Users\\Administrator\\Desktop\\MQL4\\charts\\' + symbol, dpi=300)
    plt.close('all')
    return 'C:\\Users\\Administrator\\Desktop\\MQL4\\charts\\' + symbol + ".png"



