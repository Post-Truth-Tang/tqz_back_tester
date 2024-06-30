import re
import math
import matplotlib.pyplot as pyplot

from public_module.object import BarData
from public_module.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator
from public_module.tqz_extern.tools.pandas_operator.pandas_operator import pandas

from back_tester_branch.back_tester_source_data import TQZBackTesterFutureSourceData
from back_tester_source_data import TQZBackTesterFutureConfigPath, TQZBackTesterResultPath
from back_tester_branch.create_future_strategies_setting_jsonfile import TQZFutureStrategiesSetting, TQZFutureContractFund


class TQZBackTesterFuture:
    __future_contracts_setting = TQZJsonOperator.tqz_load_jsonfile(
        jsonfile=TQZBackTesterFutureConfigPath.future_contracts_setting_path()
    )

    @classmethod
    def start(cls):
        TQZFutureStrategiesSetting.refresh()

        _strategies = TQZBackTesterFutureSourceData.load_future_strategies()

        back_tester_result = {}
        for strategy_name, data in _strategies.items():
            strategy, bars = data['strategy'], data['bars']
            per_result_df, daily_per_result_df = pandas.DataFrame(columns={'date', 'close_price', 'pos'}), pandas.DataFrame(columns={'date', 'balance'})

            # back tester single strategy
            strategy.on_init()
            strategy.on_start()

            strategy_fund = TQZFutureContractFund.get_contract_fund(tq_sym=strategy.vt_symbol)
            for bar in bars:
                strategy.on_bar(bar)
                per_result_df = cls.__update_per_result_df(per_result_df=per_result_df, bar=bar, strategy=strategy)

                search_result = re.search('(\d+)-(\d+)-(\d+) 14:(\d+):(\d+)', bar.datetime)
                if search_result is not None:
                    daily_per_result_df_current_row = len(daily_per_result_df)
                    daily_per_result_df.loc[daily_per_result_df_current_row, 'date'] = re.match('(\d+)-(\d+)-(\d+)', bar.datetime).group()
                    daily_per_result_df.loc[daily_per_result_df_current_row, 'balance'] = per_result_df[-1:]['balance'].tolist()[0]
                    daily_per_result_df.loc[daily_per_result_df_current_row, 'net_value'] = daily_per_result_df.loc[daily_per_result_df_current_row, 'balance'] / strategy_fund

            daily_per_result_df['fund'] = strategy_fund
            strategy.on_stop()
            back_tester_result[strategy_name] = daily_per_result_df

            # print("per_result_df: " + str(per_result_df))

        cls.__settle_back_tester_result(back_tester_result=back_tester_result)


    # --- private part ---
    @classmethod
    def __settle_back_tester_result(cls, back_tester_result: {str, pandas.DataFrame}):
        back_tester_result_dictionary = {}
        all_strategies_df = pandas.DataFrame(columns={'date', 'fund', 'balance'})
        for strategy_name, per_back_tester_result in back_tester_result.items():
            # single strategy.
            cls.__create_netValue_png(strategy_name=strategy_name, source_df=per_back_tester_result)
            max_net_value_drop_down = cls.__max_drop_down(values=per_back_tester_result['net_value'].tolist())
            back_tester_result_dictionary[strategy_name] = {
                "max_net_value_drop_down": max_net_value_drop_down,
                "sharpe_ratio": cls.__sharp_ratio(source_df=per_back_tester_result),
                "profit_risk_ratio": round((per_back_tester_result['net_value'].tolist()[-1] - 1) / abs(max_net_value_drop_down), 4)
            }

            # merge all_strategies_df
            cls.__merge_all_strategies_df(all_strategies_df=all_strategies_df, per_back_tester_result=per_back_tester_result)

        # calculate all_strategies back_tester result
        all_strategies_name = TQZJsonOperator.tqz_load_jsonfile(
            jsonfile=TQZBackTesterFutureConfigPath.future_back_tester_setting_path()
        )['future_strategy_template']
        all_strategies_df['net_value'] = all_strategies_df['balance'] / all_strategies_df['fund']  # 如果有多策略合并回测结果的需求, 可以把 all_strategies_df 的 净值 dump下来;


        all_strategies_df.reset_index(inplace=True)
        excel_writer = pandas.ExcelWriter(path=f'{all_strategies_name}.xlsx')
        all_strategies_df.to_excel(excel_writer, sheet_name=f'{all_strategies_name}', index=False, freeze_panes=(1, 1))
        excel_writer.save()

        cls.__create_netValue_png(strategy_name=all_strategies_name, source_df=all_strategies_df)
        max_net_value_drop_down = cls.__max_drop_down(values=all_strategies_df['net_value'].tolist())
        back_tester_result_dictionary[all_strategies_name] = {
            'max_net_value_drop_down': max_net_value_drop_down,
            "sharpe_ratio": cls.__sharp_ratio(source_df=all_strategies_df),
            "profit_risk_ratio": round((all_strategies_df['net_value'].tolist()[-1] - 1) / abs(max_net_value_drop_down), 4)
        }

        # write back_tester_result.json
        TQZJsonOperator.tqz_write_jsonfile(
            content=back_tester_result_dictionary,
            target_jsonfile=TQZBackTesterResultPath.future_fold() + f'/per_back_tester_result.json'
        )

    @classmethod
    def __create_netValue_png(cls, strategy_name, source_df):
        strategy_name_format = strategy_name.replace(".", "_")
        bt_result_excel = TQZBackTesterResultPath.future_fold() + f'/{strategy_name_format}.png'

        pyplot.figure(figsize=(15, 10))  # size

        begin_date = source_df['date'].tolist()[0]
        end_date = source_df['date'].tolist()[-1]

        pyplot.title(f'{strategy_name_format}   {begin_date}~{end_date}')
        pyplot.gca().get_xaxis().set_visible(False)  # clear x title
        pyplot.plot(source_df['date'], source_df['net_value'], alpha=0.9)  # data
        pyplot.savefig(bt_result_excel)
        pyplot.close()

    @classmethod
    def __max_drop_down(cls, values: list) -> float:
        net_values_counts = len(values)

        max_drop_downs = []
        for i in range(net_values_counts):
            i_begin = values[i]

            max_drop_down = 0
            new_loop = True
            for j in range(i + 1, net_values_counts):
                if new_loop is True or max_drop_down < i_begin - values[j]:
                    max_drop_down = i_begin - values[j]
                    new_loop = False
                else:
                    break

            max_drop_downs.append(max_drop_down)

        return round(max(max_drop_downs) * -1, 4)

    @classmethod
    def __sharp_ratio(cls, source_df: pandas.DataFrame):
        source_df['net_value_flow_per_day'] = source_df['net_value'] - source_df['net_value'].shift(1)
        yield_rate_annualized = round(((source_df['net_value'].values.tolist()[-1] - 1) / len(source_df)) * 250, 5)

        if source_df['net_value_flow_per_day'].std(ddof=0) is 0:
            sharpe_ratio = 0
        else:
            sharpe_ratio = round(yield_rate_annualized / source_df['net_value_flow_per_day'].std(ddof=0) / math.sqrt(250), 4)
        del source_df['net_value_flow_per_day']

        return sharpe_ratio


    @classmethod
    def __update_per_result_df(cls, per_result_df: pandas.DataFrame, bar: BarData, strategy) -> pandas.DataFrame:
        current_row = len(per_result_df)
        per_result_df.loc[current_row, 'date'] = bar.datetime
        per_result_df.loc[current_row, 'close_price'] = bar.close_price
        per_result_df.loc[current_row, 'pos'] = strategy.pos

        if current_row is 0:
            per_result_df.loc[current_row, 'cc_diff'] = 0
        else:
            per_result_df.loc[current_row, 'cc_diff'] = bar.close_price - per_result_df.loc[current_row - 1, 'close_price']

        per_result_df.loc[current_row, 'cc_pnl'] = per_result_df.loc[current_row, 'cc_diff'] * per_result_df.loc[current_row, 'pos']


        # pos  date  close_price  cc_diff  cc_pnl  pnl  real_pnl  balance
        if current_row is 0:
            per_result_df.loc[current_row, 'pnl'] = 0
        elif current_row is not 0 and per_result_df.loc[current_row, 'pos'] is not 0 and per_result_df.loc[current_row - 1, 'pos'] is 0:
            per_result_df.loc[current_row, 'pnl'] = per_result_df.loc[current_row - 1, 'pnl']
        elif current_row is not 0 and per_result_df.loc[current_row, 'pos'] is 0 and per_result_df.loc[current_row - 1, 'pos'] is not 0:
            per_result_df.loc[current_row, 'pnl'] = per_result_df.loc[current_row - 1, 'pnl'] + per_result_df.loc[current_row, 'cc_diff'] * per_result_df.loc[current_row - 1, 'pos']
        elif current_row is not 0 and per_result_df.loc[current_row, 'pos'] > 0 and per_result_df.loc[current_row - 1, 'pos'] < 0:
            per_result_df.loc[current_row, 'pnl'] = per_result_df.loc[current_row - 1, 'pnl'] + per_result_df.loc[current_row, 'cc_diff'] * per_result_df.loc[current_row - 1, 'pos']
        elif current_row is not 0 and per_result_df.loc[current_row, 'pos'] < 0 and per_result_df.loc[current_row - 1, 'pos'] > 0:
            per_result_df.loc[current_row, 'pnl'] = per_result_df.loc[current_row - 1, 'pnl'] + per_result_df.loc[current_row, 'cc_diff'] * per_result_df.loc[current_row - 1, 'pos']
        else:
            per_result_df.loc[current_row, 'pnl'] = per_result_df.loc[current_row, 'cc_pnl'] + per_result_df.loc[current_row - 1, 'pnl']

        per_result_df.loc[current_row, 'real_pnl'] = per_result_df.loc[current_row, 'pnl'] * cls.__future_contracts_setting[strategy.vt_symbol]['contract_multiple']
        per_result_df.loc[current_row, 'balance'] = per_result_df.loc[current_row, 'real_pnl'] + TQZFutureContractFund.get_contract_fund(tq_sym=strategy.vt_symbol)

        return per_result_df


    @classmethod
    def __merge_all_strategies_df(cls, all_strategies_df: pandas.DataFrame, per_back_tester_result: pandas.DataFrame):

        if len(all_strategies_df) is 0:
            all_strategies_df['date'] = per_back_tester_result['date']
            all_strategies_df['fund'] = per_back_tester_result['fund']
            all_strategies_df['balance'] = per_back_tester_result['balance']
        else:
            all_strategies_df.set_index("date", inplace=True)
            per_back_tester_result.set_index("date", inplace=True)

            all_strategies_df["temp_balance"] = per_back_tester_result["balance"]
            all_strategies_df["temp_fund"] = per_back_tester_result["fund"]
            all_strategies_df.fillna(0, inplace=True)
            all_strategies_df['fund'] = all_strategies_df['fund'] + all_strategies_df["temp_fund"]
            all_strategies_df['balance'] = all_strategies_df['balance'] + all_strategies_df["temp_balance"]
            del all_strategies_df["temp_fund"], all_strategies_df["temp_balance"]

            all_strategies_df.reset_index(inplace=True)
            per_back_tester_result.reset_index(inplace=True)


if __name__ == '__main__':
    TQZBackTesterFuture.start()