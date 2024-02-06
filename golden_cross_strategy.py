from utils import get_ticker_data_yfinance
import plotly.graph_objs as go
import pandas as pd


def golden_cross_strategy_graph(ticker, period, interval, MAS, MAL):
    data = get_ticker_data_yfinance(ticker, period, interval)

    data[f'MA{str(MAS)}'] = data['Close'].rolling(MAS).mean()
    data[f'MA{str(MAL)}'] = data['Close'].rolling(MAL).mean()

    # declare figure
    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'], name='market data'))

    # Add Moving average on the graph
    fig.add_trace(
        go.Scatter(x=data.index, y=data[f'MA{str(MAL)}'], line=dict(color='blue', width=1.5), name='Long Term MA'))
    fig.add_trace(
        go.Scatter(x=data.index, y=data[f'MA{str(MAS)}'], line=dict(color='orange', width=1.5), name='Short Term MA'))

    # Updating X axis and graph
    # X-Axes
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=3, label="3d", stepmode="backward"),
                dict(count=5, label="5d", stepmode="backward"),
                dict(count=7, label="WTD", stepmode="todate"),
                dict(step="all")
            ])
        )
    )

    # Show
    fig.show()


def golden_cross_strategy_lines(ticker, period, interval, MAS, MAL):
    data = get_ticker_data_yfinance(ticker, period, interval)

    data[f'MA{str(MAS)}'] = data['Close'].rolling(MAS).mean()
    data[f'MA{str(MAL)}'] = data['Close'].rolling(MAL).mean()
    return data, data[f'MA{str(MAS)}'], data[f'MA{str(MAL)}']


def get_signal(MASV, MALV, old_signal):
    if MASV >= MALV:
        sig = "BUY"
    else:
        sig = "SELL"

    if sig == old_signal:
        sig = "NUNCH"
    return sig


class GoldenCrossStrategyTraderBot:

    def __init__(self, ticker, interval="90m", start_period="15d", MAS=5, MAL=20):
        self.ticker = ticker
        self.interval = interval
        self.start_period = start_period
        self.MAS = MAS
        self.MAL = MAL

        self.data = get_ticker_data_yfinance(self.ticker, self.start_period, self.interval)
        self.data[f'MA{str(self.MAS)}'] = self.data['Close'].rolling(self.MAS).mean()
        self.data[f'MA{str(self.MAL)}'] = self.data['Close'].rolling(self.MAL).mean()

        if self.data[f'MA{str(self.MAS)}'].to_list()[-1] >= self.data[f'MA{str(self.MAL)}'].to_list()[-1]:
            self.sig = "BUY"
        elif self.data[f'MA{str(self.MAS)}'].to_list()[-1] < self.data[f'MA{str(self.MAL)}'].to_list()[-1]:
            self.sig = "SELL"
        else:
            print("SORRY, IT LOOKS LIKE THERE WAS SOME SORT OF ERROR, LIKELY IN DOWNLOADING REALTIME DATA.")
        self.sig = "NUNCH"

    def recalcMA(self):
        self.data[f'MA{str(self.MAS)}'] = self.data['Close'].rolling(self.MAS).mean()
        self.data[f'MA{str(self.MAL)}'] = self.data['Close'].rolling(self.MAL).mean()

    def get_trade_signal(self, old_signal):
        currMAS = self.data[f'MA{str(self.MAS)}'].to_list()[-1]
        currMAL = self.data[f'MA{str(self.MAL)}'].to_list()[-1]
        sig = get_signal(currMAS, currMAL)
        return sig

    def redownload_data(self):
        self.data = get_ticker_data_yfinance(self.ticker, self.start_period, self.interval)

    def update(self):
        self.redownload_data()
        self.recalcMA()
        current_sig = self.sig
        currMAS = self.data[f'MA{str(self.MAS)}'].to_list()[-1]
        currMAL = self.data[f'MA{str(self.MAL)}'].to_list()[-1]

    def make_inference(self):
        self.recalcMA()
        current_sig = self.sig
        currMAS = self.data[f'MA{str(self.MAS)}'].to_list()[-1]
        currMAL = self.data[f'MA{str(self.MAL)}'].to_list()[-1]
        signal = get_signal(currMAS, currMAL, old_signal=current_sig)
        self.sig = signal
        print(f"MAS: {self.data[f'MA{str(self.MAS)}'].to_list()[-1]}")
        print(f"MAL: {self.data[f'MA{str(self.MAL)}'].to_list()[-1]}")
        return signal

    @staticmethod
    def percentage_increase(initial, end):
        return (abs(end - initial)) / initial * 100

    def test(self, start_cash, volume=1):
        money = start_cash
        num_asset = 0

        orig_data = self.data
        self.data = self.data[0:30]

        currMAS = self.data[f'MA{str(self.MAS)}'].to_list()[-1]
        currMAL = self.data[f'MA{str(self.MAL)}'].to_list()[-1]
        curr_price = self.data["Close"].to_list()[-1]
        if currMAS >= currMAL:
            last_trade = "BUY"
            money -= curr_price * volume
            num_asset += volume
        else:
            last_trade = "SELL"
            money += curr_price * volume
            num_asset = 0

        for i in range(len(orig_data) - 30):
            self.data = orig_data[0:i + 30]
            self.make_inference()
            curr_price = self.data["Close"].to_list()[-1]
            print(curr_price)
            print("")

            currMAS = self.data[f'MA{str(self.MAS)}'].to_list()[-1]
            currMAL = self.data[f'MA{str(self.MAL)}'].to_list()[-1]

            if currMAS >= currMAL:
                trade = "BUY"
            else:
                trade = "SELL"

            if trade == last_trade:
                pass
            else:
                if currMAS >= currMAL:
                    last_trade = "BUY"
                    money -= curr_price * volume
                    num_asset = volume
                else:
                    last_trade = "SELL"
                    money += curr_price * volume
                    num_asset = 0

        print(f"TOTAL ENDING VALUE: {money + (num_asset * curr_price)}")
        print(f'{self.percentage_increase(start_cash, (money + (num_asset * curr_price)))}% gain!')
        print(num_asset)
        print(curr_price)
        print(money)

    def test_with_graph(self, start_cash, volume=1):

        # declare figure
        fig = go.Figure()

        # Candlestick
        fig.add_trace(go.Candlestick(x=self.data.index,
                                     open=self.data['Open'],
                                     high=self.data['High'],
                                     low=self.data['Low'],
                                     close=self.data['Close'], name='market data'))

        # Add Moving average on the graph
        fig.add_trace(
            go.Scatter(x=self.data.index, y=self.data[f'MA{str(self.MAL)}'], line=dict(color='blue', width=1.5), name='Long Term MA'))
        fig.add_trace(
            go.Scatter(x=self.data.index, y=self.data[f'MA{str(self.MAS)}'], line=dict(color='orange', width=1.5),
                       name='Short Term MA'))

        money = start_cash
        num_asset = 0

        orig_data = self.data
        self.data = self.data[0:30]

        currMAS = self.data[f'MA{str(self.MAS)}'].to_list()[-1]
        currMAL = self.data[f'MA{str(self.MAL)}'].to_list()[-1]
        curr_price = self.data["Close"].to_list()[-1]

        if currMAS >= currMAL:
            last_trade = "BUY"
            money -= curr_price * volume
            num_asset += volume
        else:
            last_trade = "SELL"

        nw = []
        for i in range(len(orig_data) - 30):
            self.data = orig_data[0:i + 30]
            self.make_inference()
            curr_price = self.data["Close"].to_list()[-1]
            print(f' Current Net Worth: {money + (num_asset * curr_price)}')
            nw.append(money + (num_asset * curr_price))
            print(curr_price)
            print("")

            currMAS = self.data[f'MA{str(self.MAS)}'].to_list()[-1]
            currMAL = self.data[f'MA{str(self.MAL)}'].to_list()[-1]

            if currMAS >= currMAL:
                trade = "BUY"
            else:
                trade = "SELL"

            if trade == last_trade:
                pass
            else:
                if currMAS >= currMAL:
                    last_trade = "BUY"
                    money -= curr_price * volume
                    num_asset = volume
                else:
                    last_trade = "SELL"
                    money += curr_price * volume
                    num_asset = 0

        print(f"TOTAL ENDING VALUE: {money + (num_asset * curr_price)}")
        print(f'{self.percentage_increase(start_cash, (money + (num_asset * curr_price)))}% gain!')
        print(num_asset)
        print(curr_price)
        print(money)

        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(x=orig_data.index, y=nw, line=dict(color='red', width=1.5),
                       name='Worth of All Assets'))
        fig.show()
        fig1.show()

    def load_data_from_csv(self, path):
        self.data = pd.read_csv(path)
        self.data[f'MA{str(self.MAS)}'] = self.data['Close'].rolling(self.MAS).mean()
        self.data[f'MA{str(self.MAL)}'] = self.data['Close'].rolling(self.MAL).mean()
"""
data, MASL, MALL = golden_cross_strategy_lines(ticker="BTC-USD", interval="90m", period="15d", MAS=5, MAL=20)
data.to_csv("stock_data_btc.csv")
"""
bot = GoldenCrossStrategyTraderBot("AMZN", MAS=50, MAL=100, start_period="60d", interval="30m")
#bot.load_data_from_csv(path="coin_Bitcoin.csv")
bot.test_with_graph(start_cash=40000, volume=10)
