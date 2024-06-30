
import math
import matplotlib.pyplot as pyplot
from public_module.tqz_extern.tools.pandas_operator.pandas_operator import pandas


def get_sharpe_ratio(source_dataframe: pandas.DataFrame()):
    source_dataframe['net_value_flow_per_day'] = source_dataframe['net_value'] - source_dataframe['net_value'].shift(1)
    yield_rate_annualized = round(((merge_result['net_value'].values.tolist()[-1] - 1) / len(merge_result)) * 250, 5)

    if merge_result['net_value_flow_per_day'].std(ddof=0) is 0:
        sharpe_ratio = 0
    else:
        sharpe_ratio = round(yield_rate_annualized / merge_result['net_value_flow_per_day'].std(ddof=0) / math.sqrt(250), 4)
    del merge_result['net_value_flow_per_day']

    return sharpe_ratio


def get_max_drop_down(values: list):
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


def create_netValue_png(strategy_name, source_df):
    strategy_name_format = strategy_name.replace(".", "_")
    bt_result_excel = f'{strategy_name_format}.png'

    pyplot.figure(figsize=(15, 10))  # size

    begin_date = source_df['date'].tolist()[0]
    end_date = source_df['date'].tolist()[-1]

    pyplot.title(f'{strategy_name_format}   {begin_date}~{end_date}')
    pyplot.gca().get_xaxis().set_visible(False)  # clear x title
    pyplot.plot(source_df['date'], source_df['net_value'], alpha=0.9)  # data
    pyplot.savefig(bt_result_excel)
    pyplot.close()


if __name__ == '__main__':
    TQZFutureRenkoScalpingAutoFundManageStrategy = pandas.read_excel(
        io='TQZFutureRenkoScalpingAutoFundManageStrategy.xlsx',
        sheet_name='TQZFutureRenkoScalpingAutoFundManageStrategy'
    )
    TQZFutureRenkoWaveAutoFundManageStrategy = pandas.read_excel(
        io='TQZFutureRenkoWaveAutoFundManageStrategy.xlsx',
        sheet_name='TQZFutureRenkoWaveAutoFundManageStrategy'
    )

    """
    TQZMarcoTradingStrategy = pandas.read_excel(
        io='TQZMarcoTradingStrategy.xlsx',
        sheet_name='TQZMarcoTradingStrategy'
    )
    """


    merge_result = pandas.DataFrame(columns={'fund', 'balance'})
    merge_result['date'] = TQZFutureRenkoWaveAutoFundManageStrategy['date']
    merge_result['fund'] = TQZFutureRenkoWaveAutoFundManageStrategy['fund'] + TQZFutureRenkoScalpingAutoFundManageStrategy['fund']
    merge_result['balance'] = TQZFutureRenkoWaveAutoFundManageStrategy['balance'] + TQZFutureRenkoScalpingAutoFundManageStrategy['balance']

    merge_result['net_value'] = merge_result['balance'] / merge_result['fund']

    _sharpe_ratio = get_sharpe_ratio(source_dataframe=merge_result)
    _max_drop_down = get_max_drop_down(values=merge_result['net_value'].to_list())
    _profit_risk_ratio = round((merge_result['net_value'].tolist()[-1] - 1) / abs(_max_drop_down), 4)

    create_netValue_png(strategy_name='strategies_total_2', source_df=merge_result)

    print("merge_result: " + str(merge_result))
    print("sharpe ratio: " + str(_sharpe_ratio))
    print("max_drop_down: " + str(_max_drop_down))
    print("profit_risk_ratio: " + str(_profit_risk_ratio))


