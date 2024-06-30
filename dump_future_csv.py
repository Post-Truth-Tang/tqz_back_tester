"""
下载期货小时数据csv。。。
"""

from server_api.api.tqz_tianqin_api import TQZTianQinClient
from datetime import date

if __name__ == '__main__':
    TQZTianQinClient().dump_history_df_to_csv(
        tq_symbols=[
            "KQ.m@CZCE.FG"
        ], tq_duration_seconds=5 * 60, start_dt=date(2019, 1, 1), end_dt=date(2022, 4, 1))