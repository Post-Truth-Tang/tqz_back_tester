import datetime
import re

from tqsdk import TqApi, TqAuth
from tqsdk.tools import DataDownloader
from contextlib import closing

from public_module.tqz_extern.tools.pandas_operator.pandas_operator import pandas  # noqa
from public_module.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator # noqa

from server_api.tqz_object import TickData, BarData, Exchange
import csv

TIME_GAP = 8 * 60 * 60 * 1000000000

class TQZTianQinClient:
    """
    天勤接口 每次只能拉取单一合约的数据！
    """

    __tq_symbols = None

    def __init__(self, account: str = "nimahannisha", pass_word: str = "tnt19860427"):
        self.api = TqApi(auth=TqAuth(account, pass_word))

        if TQZTianQinClient.__tq_symbols is None:
            TQZTianQinClient.__tq_symbols = self.api.query_quotes(ins_class="FUTURE", expired=False)

    def query_history_bars(self, tq_symbol: str, tq_duration_seconds: int, tq_data_length: int = 8964) -> list:
        assert tq_symbol in TQZTianQinClient.__tq_symbols, f'bad tq_symbol: {tq_symbol}'

        tq_result = self.api.get_kline_serial(symbol=tq_symbol, duration_seconds=tq_duration_seconds, data_length=tq_data_length)
        self.api.close()

        tq_result["datetime"] = pandas.to_datetime(tq_result["datetime"] + TIME_GAP)
        tq_result['datetime'] = tq_result['datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))  # %f是毫秒

        history_bars = []
        if tq_result is not None:
            for ix, row in tq_result.loc[tq_result["id"] >= 0].iterrows():
                history_bars.append(
                    BarData(
                        symbol=tq_symbol.split(".")[1],
                        exchange=Exchange(tq_symbol.split(".")[0]),
                        interval='any_interval',  # noqa
                        datetime=row["datetime"],
                        open_price=row["open"],
                        high_price=row["high"],
                        low_price=row["low"],
                        close_price=row["close"],
                        volume=row["volume"],
                        open_interest=row.get("open_oi", 0),
                        gateway_name="TQ",
                    )
                )

        return history_bars

    def query_index_history_bars(self, tq_index_symbol: str, tq_duration_seconds: int, tq_data_length: int = 8964) -> list:
        tq_result = self.api.get_kline_serial(symbol=tq_index_symbol, duration_seconds=tq_duration_seconds, data_length=tq_data_length)
        self.api.close()

        tq_result["datetime"] = pandas.to_datetime(tq_result["datetime"] + TIME_GAP)
        tq_result['datetime'] = tq_result['datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))  # %f是毫秒

        history_bars = []
        if tq_result is not None:
            for ix, row in tq_result.loc[tq_result["id"] >= 0].iterrows():
                history_bars.append(
                    BarData(
                        symbol=f'{tq_index_symbol.split(".")[2]}000',
                        exchange=Exchange("TQZ_INDEX"),
                        interval='any_interval',  # noqa
                        datetime=row["datetime"],
                        open_price=row["open"],
                        high_price=row["high"],
                        low_price=row["low"],
                        close_price=row["close"],
                        volume=row["volume"],
                        open_interest=row.get("open_oi", 0),
                        close_interest=row.get("close_oi", 0),
                        gateway_name="TQ",
                    )
                )

        return history_bars

    def query_main_history_bars(self, tq_main_symbol: str, tq_duration_seconds: int, tq_data_length: int = 8964) -> list:
        tq_result = self.api.get_kline_serial(symbol=tq_main_symbol, duration_seconds=tq_duration_seconds, data_length=tq_data_length)
        self.api.close()

        tq_result["datetime"] = pandas.to_datetime(tq_result["datetime"] + TIME_GAP)
        tq_result['datetime'] = tq_result['datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))  # %f是毫秒

        history_bars = []
        if tq_result is not None:
            for ix, row in tq_result.loc[tq_result["id"] >= 0].iterrows():
                history_bars.append(
                    BarData(
                        symbol=f'{tq_main_symbol.split(".")[2]}888',
                        exchange=Exchange("TQZ_MAIN"),
                        interval='any_interval',  # noqa
                        datetime=row["datetime"],
                        open_price=row["open"],
                        high_price=row["high"],
                        low_price=row["low"],
                        close_price=row["close"],
                        volume=row["volume"],
                        open_interest=row.get("open_oi", 0),
                        close_interest=row.get("close_oi", 0),
                        gateway_name="TQ",
                    )
                )

        return history_bars

    @staticmethod
    def query_history_bars_from_csv(tq_m_symbol, csv_path: str):
        tq_result = pandas.read_csv(csv_path)

        history_bars = []
        if tq_result is not None:
            for ix, row in tq_result.iterrows():
                history_bars.append(
                    BarData(
                        symbol=f'{tq_m_symbol.split(".")[2]}888',
                        exchange=Exchange("TQZ_MAIN"),
                        interval='any_interval',  # noqa
                        datetime=row["datetime"],
                        open_price=row[f'{tq_m_symbol}.open'],
                        high_price=row[f'{tq_m_symbol}.high'],
                        low_price=row[f'{tq_m_symbol}.low'],
                        close_price=row[f'{tq_m_symbol}.close'],
                        volume=row[f'{tq_m_symbol}.volume'],
                        open_interest=row.get(f'{tq_m_symbol}.open_oi', 0),
                        gateway_name="TQ",
                    )
                )

        return history_bars

    def dump_history_df_to_csv(self, tq_symbols: list, tq_duration_seconds: int, start_dt, end_dt):
        downloading_result = {}  # noqa

        for tq_symbol in tq_symbols:
            csv_file_name = f'{tq_symbol.replace(".", "_")}.csv'
            downloading_result[tq_symbol] = DataDownloader(
                self.api,
                symbol_list=tq_symbol,
                dur_sec=tq_duration_seconds,
                start_dt=start_dt,
                end_dt=end_dt,
                csv_file_name=csv_file_name
            )

        with closing(self.api):
            while not all([v.is_finished() for v in downloading_result.values()]):
                self.api.wait_update()
                print("progress: ", {k: ("%.2f%%" % v.get_progress()) for k, v in downloading_result.items()})

    def load_all_tq_symbols(self):
        self.api.close()
        return TQZTianQinClient.__tq_symbols

    def query_quote(self, tq_symbol: str) -> dict:
        result = self.api.get_quote(symbol=tq_symbol)
        self.api.close()
        return result  # noqa

    # --- tick part ---
    @staticmethod
    def query_history_ticks_from_csv(tq_symbol: str, csv_path: str) -> list:
        csv_read = csv.reader(open(csv_path))

        tq_sym = tq_symbol.split('@')[1]

        history_ticks = []
        for line in csv_read:
            if line[0] == 'datetime':
                continue

            std_datetime_string = re.match('(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+\.[\d]{4})', line[0]).group()
            tick_data = TickData(
                    symbol=f'{tq_sym.split(".")[1]}888',
                    exchange=Exchange(tq_sym.split('.')[0]),
                    name=tq_symbol,
                    datetime=datetime.datetime.strptime(std_datetime_string, "%Y-%m-%d %H:%M:%S.%f"),
                    last_price=float(line[2]),
                    high_price=float(line[3]),
                    low_price=float(line[4]),
                    volume=float(line[5]),
                    open_interest=float(line[7]),
                    bid_price_1=float(line[8]),
                    bid_volume_1=float(line[9]),
                    ask_price_1=float(line[10]),
                    ask_volume_1=float(line[11]),
                    gateway_name="csv_ticks"
                )  # noqa
            history_ticks.append(tick_data)  # 如果程序 crash 了, 尝试去掉这句话, 直接打印 tick_data.
            print("tick_data: " + str(tick_data))

        return history_ticks


class TQZTianQinDataManager:
    """
    小时线: 一天6根
    1493个交易日

    30分钟线: 一天12根
    746个交易日

    10分钟线: 一天36根
    248个交易日
    """

    __load_history_bars_map: dict = None
    __load_main_history_bars_map: dict = None

    @classmethod
    def load_history_bars_map(cls, tq_symbols: list, tq_duration_seconds: int, tq_data_length: int = 8964) -> dict:
        """
        Load history bars of multi symbols from tianqin, and only load once time before back tester.
        :param tq_symbols: list of multi symbols
        :param tq_duration_seconds: just tq_duration_seconds
        :param tq_data_length: data length
        :return: history bars map
        """

        load_history_bars_map = {}
        if cls.__load_history_bars_map is None:
            for tq_symbol in tq_symbols:
                if tq_symbol not in load_history_bars_map.keys():
                    load_history_bars_map[tq_symbol] = TQZTianQinClient().query_history_bars(
                        tq_symbol=tq_symbol,
                        tq_duration_seconds=tq_duration_seconds,
                        tq_data_length=tq_data_length
                    )

            cls.__load_history_bars_map = load_history_bars_map

        return cls.__load_history_bars_map

    @classmethod
    def load_main_history_bars_map(cls, tq_m_symbols: list, tq_duration_seconds: int, tq_data_length: int = 8964) -> dict:
        """
        Load history bars of multi symbols from tianqin, and only load once time before back tester.
        :param tq_m_symbols: list of multi symbols
        :param tq_duration_seconds: just tq_duration_seconds
        :param tq_data_length: data length
        :return: history bars map
        """

        load_main_history_bars_map = {}
        if cls.__load_main_history_bars_map is None:
            for tq_m_symbol in tq_m_symbols:
                if tq_m_symbol not in load_main_history_bars_map.keys():
                    load_main_history_bars_map[tq_m_symbol] = TQZTianQinClient().query_main_history_bars(
                        tq_main_symbol=tq_m_symbol,
                        tq_duration_seconds=tq_duration_seconds,
                        tq_data_length=tq_data_length
                    )

            cls.__load_main_history_bars_map = load_main_history_bars_map

        return cls.__load_main_history_bars_map

    @classmethod
    def load_main_history_ticks_from_csv(cls, tq_m_symbol: str, csv_path: str):
        return TQZTianQinClient.query_history_ticks_from_csv(tq_symbol=tq_m_symbol, csv_path=csv_path)

    @classmethod
    def load_main_history_bars_from_csv(cls, tq_m_symbols: list) -> dict:  # {tq_m_symbol: csv_path}
        main_history_bars_map = {}
        for tq_m_symbol in tq_m_symbols:
            main_history_bars_map[tq_m_symbol] = TQZTianQinClient.query_history_bars_from_csv(
                tq_m_symbol=tq_m_symbol,
                csv_path=TQZHistoryCsvPath.history_bars_csv_path + f'/{tq_m_symbol.replace(".", "_")}.csv'
            )

        return main_history_bars_map

    """
    @classmethod
    def load_main_history_bars_from_csv(cls, tq_m_symbol_csv_path_map: dict) -> dict:  # {tq_m_symbol: csv_path}
        main_history_bars_map = {}
        for tq_m_symbol, csv_path in tq_m_symbol_csv_path_map.items():
            main_history_bars_map[tq_m_symbol] = TQZTianQinClient.query_history_bars_from_csv(
                tq_m_symbol=tq_m_symbol,
                csv_path=csv_path
            )

        return main_history_bars_map
    """


class TQZHistoryCsvPath:

    history_ticks_csv_path = TQZFilePathOperator.grandfather_path(source_path=__file__) + f'/history_ticks_csv'
    history_bars_csv_path = TQZFilePathOperator.grandfather_path(source_path=__file__) + f'/history_bars_csv'


if __name__ == '__main__':
    """ contract data
    content = TQZTianQinDataManager.load_history_bars_map(tq_symbols=["CZCE.SM206", "SHFE.rb2205"], tq_duration_seconds=60 * 60)
    i_content = TQZTianQinDataManager.load_history_index_bars_map(tq_index_symbols=["KQ.i@CFFEX.IC"], tq_duration_seconds=60 * 60, tq_data_length=3)
    m_content = TQZTianQinDataManager.load_history_main_bars_map(tq_main_symbols=["KQ.m@CFFEX.IC"], tq_duration_seconds=60 * 60, tq_data_length=3)
    print("m_content: " + str(m_content))
    """

    """ 放弃python 下的 tick 模式回测
    cu_file = TQZFilePathOperator.grandfather_path(source_path=__file__) + f'/history_ticks_csv/KQ_m@DCE_lh.csv'
    ticks_content = TQZTianQinDataManager.load_main_history_ticks_from_csv(tq_m_symbol="KQ.m@DCE.lh", csv_path=cu_file)
    """

    """ load bars from csv
    content = TQZTianQinDataManager.load_main_history_bars_from_csv(tq_m_symbols=["KQ.m@SHFE.cu"])
    print("content: " + str(content))
    """

    pass