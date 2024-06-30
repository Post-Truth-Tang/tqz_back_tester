import matplotlib.pyplot as pyplot
import re

from math import floor

from datetime import datetime

from back_tester_branch.back_tester_source_data import TQZBackTesterStockSourceData, TQZBackTesterStockConfigPath, TQZBackTesterResultPath
from public_module.tqz_extern.tools.pandas_operator.pandas_operator import pandas

from server_api.api.tqz_tushare_api import TQZTushareClient

from public_module.tqz_extern.tqz_constant import TQZStockIntervalType
from public_module.object import BarData, Exchange


class TQZBackTesterStock:
    __if300_df = pandas.read_excel(io=TQZBackTesterStockConfigPath.stock_pool_setting_path(), sheet_name='if300')
    __ic500_df = pandas.read_excel(io=TQZBackTesterStockConfigPath.stock_pool_setting_path(), sheet_name='ic500')

    @classmethod
    def start(cls):
        stock_strategy_templates = TQZBackTesterStockSourceData.load_stock_strategy_templates()

        for strategy_name, data in stock_strategy_templates.items():  # strategy templates
            for stock_name in cls.__if300_df['stock_list'].tolist():  # if300
                per_result_df = pandas.DataFrame(columns={'date', 'close_price', 'pos'})
                bars = TQZTushareClient.query_history_bars(
                    ts_symbol=stock_name,
                    exchange=Exchange(stock_name.split('.')[1]),
                    start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
                    end_date=datetime.strptime(data['end_date'], '%Y-%m-%d'),
                    interval=TQZStockIntervalType.DAILY
                )

                strategy, single_strategy_name = None, f'{stock_name}.{strategy_name}'
                if strategy_name == 'TQZStockDoubleMaStrategy':
                    strategy = data['stock_strategy_template'](None, single_strategy_name, stock_name, {
                        "class_name": single_strategy_name,
                        "fast_window": 30,
                        "slow_window": 250,
                        "strategy_fund": data['strategy_fund']
                    })
                elif strategy_name == "TQZMarcoTradingStrategy":
                    strategy = data['stock_strategy_template'](None, single_strategy_name, stock_name, {
                        "class_name": single_strategy_name,
                        "ma_window": 250,
                        "donchian_channel_window": 20,
                        "clear_position_days_window": 10,
                        "n_window": 20,
                        "strategy_fund": data['strategy_fund']
                    })
                elif strategy_name in ["TQZStockRenkoScalpingStrategy", "TQZStockRenkoWaveStrategy"]:
                    strategy = data['stock_strategy_template'](None, single_strategy_name, stock_name, {
                        "class_name": single_strategy_name,
                        "fast_window": 30,
                        "slow_window": 250,
                        "strategy_fund": data['strategy_fund'],
                        "renko_size": cls.__get_renko_size(bars=bars),
                        "min_tick_price_flow": data['tick_value']
                    })
                elif strategy_name in ["TQZStockRenkoWaveAutoFundManageStrategy", "TQZStockRenkoScalpingAutoFundManageStrategy"]:
                    strategy = data['stock_strategy_template'](None, single_strategy_name, stock_name, {
                        "class_name": single_strategy_name,
                        "fast_window": 10,
                        "slow_window": 60,
                        "strategy_fund": data['strategy_fund'],
                        "min_tick_price_flow": data['tick_value']
                    })

                strategy.on_init()
                strategy.on_start()

                for bar in bars:
                    strategy.on_bar(bar=bar)
                    per_result_df = cls.__update_per_result_df(per_result_df=per_result_df, bar=bar, strategy=strategy)

                strategy.on_stop()
                per_result_df['net_value'] = per_result_df['balance'] / strategy.strategy_fund

                strategy_name_format = single_strategy_name.replace(".", "_")
                cls.__create_netValue_png(
                    per_result_df=per_result_df,
                    strategy_name_format=strategy_name_format,
                    path=TQZBackTesterResultPath.stock_if300_fold() + f'/{strategy_name}/{strategy_name_format}.png'
                )

            for stock_name in cls.__ic500_df['stock_list'].tolist():  # ic500
                per_result_df = pandas.DataFrame(columns={'date', 'close_price', 'pos'})
                bars = TQZTushareClient.query_history_bars(
                    ts_symbol=stock_name,
                    exchange=Exchange(stock_name.split('.')[1]),
                    start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
                    end_date=datetime.strptime(data['end_date'], '%Y-%m-%d'),
                    interval=TQZStockIntervalType.DAILY
                )

                strategy, single_strategy_name = None, f'{stock_name}.{strategy_name}'
                if strategy_name == 'TQZStockDoubleMaStrategy':
                    strategy = data['stock_strategy_template'](None, single_strategy_name, stock_name, {
                        "class_name": single_strategy_name,
                        "fast_window": 30,
                        "slow_window": 250,
                        "strategy_fund": data['strategy_fund']
                    })
                elif strategy_name == "TQZMarcoTradingStrategy":
                    strategy = data['stock_strategy_template'](None, single_strategy_name, stock_name, {
                        "class_name": single_strategy_name,
                        "ma_window": 250,
                        "donchian_channel_window": 20,
                        "clear_position_days_window": 10,
                        "n_window": 20,
                        "strategy_fund": data['strategy_fund']
                    })
                elif strategy_name in ["TQZStockRenkoScalpingStrategy", "TQZStockRenkoWaveStrategy"]:
                    strategy = data['stock_strategy_template'](None, single_strategy_name, stock_name, {
                        "class_name": single_strategy_name,
                        "fast_window": 30,
                        "slow_window": 250,
                        "strategy_fund": data['strategy_fund'],
                        "renko_size": cls.__get_renko_size(bars=bars),
                        "min_tick_price_flow": data['tick_value']
                    })
                elif strategy_name in ["TQZStockRenkoWaveAutoFundManageStrategy", "TQZStockRenkoScalpingAutoFundManageStrategy"]:
                    strategy = data['stock_strategy_template'](None, single_strategy_name, stock_name, {
                        "class_name": single_strategy_name,
                        "fast_window": 10,
                        "slow_window": 60,
                        "strategy_fund": data['strategy_fund'],
                        "min_tick_price_flow": data['tick_value']
                    })

                strategy.on_init()
                strategy.on_start()

                for bar in bars:
                    strategy.on_bar(bar=bar)
                    per_result_df = cls.__update_per_result_df(per_result_df=per_result_df, bar=bar, strategy=strategy)

                strategy.on_stop()
                per_result_df['net_value'] = per_result_df['balance'] / strategy.strategy_fund

                strategy_name_format = single_strategy_name.replace(".", "_")
                cls.__create_netValue_png(
                    per_result_df=per_result_df,
                    strategy_name_format=strategy_name_format,
                    path=TQZBackTesterResultPath.stock_ic500_fold() + f'/{strategy_name}/{strategy_name_format}.png'
                )


    # --- private part ---
    @classmethod
    def __create_netValue_png(cls, per_result_df: pandas.DataFrame, strategy_name_format: str, path: str):
        pyplot.figure(figsize=(15, 10))  # size

        begin_date = per_result_df['date'].tolist()[0]
        end_date = per_result_df['date'].tolist()[-1]

        pyplot.title(f'{strategy_name_format}   {begin_date}~{end_date}')
        pyplot.gca().get_xaxis().set_visible(False)  # clear x title
        pyplot.plot(per_result_df['date'], per_result_df['net_value'], alpha=0.9)  # data
        pyplot.savefig(path)
        pyplot.close()

    @classmethod
    def __update_per_result_df(cls, per_result_df: pandas.DataFrame, bar: BarData, strategy) -> pandas.DataFrame:
        current_row = len(per_result_df)
        per_result_df.loc[current_row, 'date'] = re.match('(\d+)-(\d+)-(\d+)', str(bar.datetime)).group()
        per_result_df.loc[current_row, 'close_price'] = bar.close_price
        per_result_df.loc[current_row, 'pos'] = strategy.pos

        if current_row is 0:
            per_result_df.loc[current_row, 'cc_diff'] = 0
        else:
            per_result_df.loc[current_row, 'cc_diff'] = bar.close_price - per_result_df.loc[current_row - 1, 'close_price']

        per_result_df.loc[current_row, 'cc_pnl'] = per_result_df.loc[current_row, 'cc_diff'] * per_result_df.loc[current_row, 'pos']


        if current_row is 0:
            per_result_df.loc[current_row, 'pnl'] = 0
        elif current_row is not 0 and per_result_df.loc[current_row, 'pos'] is not 0 and per_result_df.loc[current_row - 1, 'pos'] is 0:
            per_result_df.loc[current_row, 'pnl'] = per_result_df.loc[current_row - 1, 'pnl']
        elif current_row is not 0 and per_result_df.loc[current_row, 'pos'] is 0 and per_result_df.loc[current_row - 1, 'pos'] is not 0:
            per_result_df.loc[current_row, 'pnl'] = per_result_df.loc[current_row - 1, 'pnl'] + per_result_df.loc[current_row, 'cc_diff'] * per_result_df.loc[current_row - 1, 'pos']
        else:
            per_result_df.loc[current_row, 'pnl'] = per_result_df.loc[current_row, 'cc_pnl'] + per_result_df.loc[current_row - 1, 'pnl']

        per_result_df.loc[current_row, 'balance'] = per_result_df.loc[current_row, 'pnl'] + strategy.strategy_fund

        return per_result_df

    @classmethod
    def __get_renko_size(cls, bars: list, min_tick_price_flow: float = 0.01) -> int:
        if len(bars) > 250:
            bars = bars[:250]

        trs = []
        for bar in bars:
            hl_diff = bar.high_price - bar.low_price
            trs.append(hl_diff)

        trs.sort()

        begin_index = floor(len(trs) * 0.1)
        end_index = len(trs) - begin_index
        avg_tr = sum(trs[begin_index:end_index]) / len(trs[begin_index:end_index])

        return int((avg_tr * 0.5) / min_tick_price_flow)

if __name__ == '__main__':
    TQZBackTesterStock.start()
