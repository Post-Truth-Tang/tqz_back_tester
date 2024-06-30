import tushare

from datetime import datetime
from typing import List

from public_module.object import BarData
from public_module.constant import Exchange
from public_module.tqz_extern.tools.pandas_operator.pandas_operator import TQZPandas  # noqa

from public_module.tqz_extern.tqz_constant import TQZEquitExchangeType, TQZStockIntervalType

class TQZTushareClient:

    __api = tushare.pro_api()

    # --- api part ---
    @classmethod
    def query_multi_stocks_history_bars(cls, stock_list: list, start: datetime, end: datetime, interval: TQZStockIntervalType = TQZStockIntervalType.DAILY) -> dict:
        """
        Api of query history bars(multi stocks) with (stock_list, start_date, end_date).
        """

        stock_bars_map = {}
        for stock_name in stock_list:
            stock_code, stock_exchange = stock_name.split('.')[0], stock_name.split('.')[1]
            if stock_exchange in [TQZEquitExchangeType.SZ.value]:
                stock_exchange = Exchange.SZ
            elif stock_exchange in [TQZEquitExchangeType.SH.value]:
                stock_exchange = Exchange.SH
            elif stock_exchange in [TQZEquitExchangeType.BJ.value]:
                stock_exchange = Exchange.BJ
            else:
                assert False, f'bad stock_exchange: {stock_exchange}'

            assert interval in [TQZStockIntervalType.DAILY, TQZStockIntervalType.WEEKLY, TQZStockIntervalType.MONTHLY], f'bad interval: {interval}'

            stock_bars_map[stock_name] = cls.query_history_bars(ts_symbol=stock_name, exchange=stock_exchange, start_date=start, end_date=end, interval=interval)

        return stock_bars_map


    @classmethod
    def query_history_bars(cls, ts_symbol: str, exchange: Exchange, start_date: datetime, end_date: datetime, interval: TQZStockIntervalType = TQZStockIntervalType.DAILY):
        """
        Api of query history bars(single stock) with (start_date, end_date).
        """

        bars_dataframe = cls.__load_stock_history_dataframe(
            ts_symbol=ts_symbol,
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d'),
            interval=interval
        )

        bar_list: List[BarData] = []
        if bars_dataframe is not None:
            for ix, row in bars_dataframe.iterrows():
                bar = BarData(
                    symbol=ts_symbol.split('.')[0],  # noqa
                    exchange=exchange,  # noqa
                    interval=interval,  # noqa
                    datetime=datetime.strptime(row["trade_date"], "%Y%m%d"),  # noqa
                    open_price=row["open"],  # noqa
                    high_price=row["high"],  # noqa
                    low_price=row["low"],  # noqa
                    close_price=row["close"],  # noqa
                    volume=row["vol"],  # noqa
                    open_interest=row["amount"],  # noqa
                    gateway_name="TQZTushare",   # noqa
                )
                bar_list.append(bar)

        return bar_list


    # --- private part ---
    @classmethod
    def __load_stock_dataframe(cls, ts_symbol: str, offset: int, interval: TQZStockIntervalType = TQZStockIntervalType.DAILY):
        """
        Get data of single stock with ts_symbol and offset_days(from today).
        """

        if interval in [TQZStockIntervalType.WEEKLY]:
            source_dataframe = cls.__api.weekly(
                ts_code=ts_symbol,
                fields='ts_code,trade_date,open,high,low,close,vol,amount'
            )
        elif interval in [TQZStockIntervalType.MONTHLY]:
            source_dataframe = cls.__api.monthly(
                ts_code=ts_symbol,
                fields='ts_code,trade_date,open,high,low,close,vol,amount'
            )
        elif interval in [TQZStockIntervalType.DAILY]:
            source_dataframe = cls.__api.daily(ts_code=ts_symbol)
        else:
            assert False, f'bad interval {interval}'

        stock_dataframe = source_dataframe[:offset].iloc[::-1]
        stock_dataframe.reset_index(inplace=True)
        del stock_dataframe['index']

        return stock_dataframe

    @classmethod
    def __load_stock_history_dataframe(cls, ts_symbol: str, start_date: str, end_date: str, interval: TQZStockIntervalType = TQZStockIntervalType.DAILY):
        """
        Get data of single stock with ts_symbol、start_date and end_date.
        """

        if interval in [TQZStockIntervalType.WEEKLY]:
            source_dataframe = cls.__api.weekly(
                ts_code=ts_symbol,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,open,high,low,close,vol,amount'
            )
        elif interval in [TQZStockIntervalType.MONTHLY]:
            source_dataframe = cls.__api.monthly(
                ts_code=ts_symbol,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,open,high,low,close,vol,amount'
            )
        elif interval in [TQZStockIntervalType.DAILY]:
            source_dataframe = cls.__api.daily(
                ts_code=ts_symbol,
                start_date=start_date,
                end_date=end_date
            )
        else:
            assert False, f'bad interval {interval}'

        stock_dataframe = source_dataframe.iloc[::-1]
        stock_dataframe.reset_index(inplace=True)
        del stock_dataframe['index']

        return stock_dataframe


if __name__ == '__main__':
    # double_stocks_dataframes = api.daily(ts_code='000001.SZ,600000.SH', start_date='20180701', end_date='20180718')

    """
    start_test = datetime.strptime('2017-04-30', '%Y-%m-%d')
    end_test = datetime.strptime('2022-04-30', '%Y-%m-%d')
    bars_map = TQZTushareClient.query_multi_stocks_history_bars(
        stock_list=['000001.SZ'],
        start=start_test,
        end=end_test
    )
    """

    start_test = datetime.strptime('2017-04-30', '%Y-%m-%d')
    end_test = datetime.strptime('2022-04-30', '%Y-%m-%d')
    _ts_symbol = '000001.SZ'
    _bars = TQZTushareClient.query_history_bars(
        ts_symbol=_ts_symbol,
        exchange=Exchange(_ts_symbol.split('.')[1]),
        start_date=start_test,
        end_date=end_test,
        interval=TQZStockIntervalType.DAILY
    )

    print("_bars[:5]: " + str(_bars[:5]))
