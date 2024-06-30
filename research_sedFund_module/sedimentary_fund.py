"""
1. 期货品种的沉淀资金是未平仓的期货合约（持仓量）所占用的保证金.
期货品种的沉淀资金越大说明这个品种非常受资金喜欢.
相反，如果期货品种的沉淀资金越小，说明这个品种越冷门.

2. 期货交易的本质就是资金的重新分配, 品种的沉淀资金越大, 未来有出现较大级别行情的机会就越大.
"""

import os
import re

from public_module.tqz_extern.tools.pandas_operator.pandas_operator import pandas

from public_module.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator
from public_module.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator

from server_api.api.tqz_tianqin_api import TQZTianQinDataManager

class TQZSedimentaryFund:

    __sed_fund_excel_path = TQZFilePathOperator.father_path(source_path=__file__) + f'/result_data/sed_fund.xlsx'
    __mean_sed_fund_excel_path = TQZFilePathOperator.father_path(source_path=__file__) + f'/result_data/mean_sed_fund.xlsx'

    __sed_fund_sheet_name = 'sed_fund'
    __mean_sed_fund_sheet_name = 'mean_sed_fund'

    @classmethod
    def create_sed_fund_excel(cls, days: int = 100):
        if os.path.exists(path=cls.__sed_fund_excel_path):
            print(f'{cls.__sed_fund_excel_path} is exist.')
            return

        content = cls.__contract_multiple_jsonfile_content()

        # tq_m_symbols & data source of tq
        tq_m_symbols = []
        for key in list(content.keys()):
            tq_m_symbols.append(f'KQ.m@{key}')
        tq_result = TQZTianQinDataManager.load_main_history_bars_map(
            tq_m_symbols=tq_m_symbols,
            tq_duration_seconds=86400,
            tq_data_length=days
        )

        # per sed_fund_df
        sed_fund_df_map = {}
        for tq_m_symbol, bars in tq_result.items():
            sed_fund_df = pandas.DataFrame(columns=['date', tq_m_symbol])

            contract_multiple = content[tq_m_symbol.split('@')[1]]["contract_multiple"]
            for bar in bars:
                ret_datetime_str = re.match('(\d+)-(\d+)-(\d+)', bar.datetime).group()
                new_row = len(sed_fund_df)
                sed_fund_df.loc[new_row, 'date'] = ret_datetime_str
                sed_fund_df.loc[new_row, tq_m_symbol] = bar.close_interest * 2 * bar.close_price * contract_multiple * 0.1

            sed_fund_df.set_index('date', inplace=True)
            sed_fund_df_map[tq_m_symbol] = sed_fund_df

        # merge dateframe
        new_sed_fund_df = pandas.DataFrame()
        for tq_m_symbol, sed_fund_df in sed_fund_df_map.items():
            if len(new_sed_fund_df) is 0:
                new_sed_fund_df = sed_fund_df
                continue

            new_sed_fund_df[tq_m_symbol] = sed_fund_df[tq_m_symbol]

        # write to excel
        new_sed_fund_df.reset_index(inplace=True)
        excel_writer = pandas.ExcelWriter(path=cls.__sed_fund_excel_path)
        new_sed_fund_df.to_excel(excel_writer, sheet_name=cls.__sed_fund_sheet_name, index=False, freeze_panes=(1, 1))
        excel_writer.save()


    @classmethod
    def create_mean_sed_fund_excel(cls):
        sed_fund_df = pandas.read_excel(io=cls.__sed_fund_excel_path, sheet_name=cls.__sed_fund_sheet_name)
        sed_fund_df.fillna(0, inplace=True)

        mean_sed_fund_map = {}
        for tq_m_symbol in sed_fund_df.columns.values[1:]:
            mean_sed_fund_map[tq_m_symbol] = sed_fund_df[tq_m_symbol].mean()

        # create mean_sed_fund_df
        mean_sed_fund_df = pandas.DataFrame(columns=['main_contract', 'mean_sed_fund'])
        mean_sed_fund_list = sorted(mean_sed_fund_map.items(), key=lambda x: x[1], reverse=True)
        for mean_sed_fund in mean_sed_fund_list:
            current_row = len(mean_sed_fund_df)
            mean_sed_fund_df.loc[current_row, 'main_contract'] = mean_sed_fund[0]
            mean_sed_fund_df.loc[current_row, 'mean_sed_fund'] = mean_sed_fund[1]

        # write to excel
        excel_writer = pandas.ExcelWriter(path=cls.__mean_sed_fund_excel_path)
        mean_sed_fund_df.to_excel(excel_writer, sheet_name=cls.__mean_sed_fund_sheet_name, index=False, freeze_panes=(1, 1))
        excel_writer.save()

    # --- private part ---
    @classmethod
    def __contract_multiple_jsonfile_content(cls):
        return TQZJsonOperator.tqz_load_jsonfile(
                jsonfile=TQZFilePathOperator.grandfather_path(
                    source_path=__file__
                ) + f'/back_tester_config/future/future_contracts_setting.json'
            )

if __name__ == '__main__':
    # TQZSedimentaryFund.create_sed_fund_excel(days=300)
    # TQZSedimentaryFund.create_mean_sed_fund_excel()
    pass