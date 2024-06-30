import os
from math import floor

from public_module.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator
from public_module.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator
from server_api.api.tqz_tianqin_api import TQZTianQinDataManager
from back_tester_branch.back_tester_source_data import TQZBackTesterFutureConfigPath

from public_module.tqz_extern.tqz_constant import TQZDataSourceType

class TQZFundManage:

    __future_contracts_setting = TQZJsonOperator.tqz_load_jsonfile(
        jsonfile=TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_config/future/future_contracts_setting.json'
    )

    @classmethod
    def refresh_avg_tr_json(cls, source_type: TQZDataSourceType):
        avg_tr_map = {}
        for tq_m_symbol, bars in cls.__source_content(source_type=source_type).items():
            trs = []
            for bar in bars:
                hl_diff = bar.high_price - bar.low_price
                trs.append(hl_diff)

            trs.sort()

            begin_index = floor(len(trs) * 0.25)
            end_index = len(trs) - begin_index
            avg_tr = sum(trs[begin_index:end_index]) / len(trs[begin_index:end_index])

            tq_sym = tq_m_symbol.split('@')[1]
            min_tick_price_flow = cls.__future_contracts_setting[tq_sym]["min_tick_price_flow"]
            contract_multiple = cls.__future_contracts_setting[tq_sym]["contract_multiple"]

            avg_tr_map[tq_sym] = {
                "avg_tr": avg_tr,
                "min_tick_price_flow": min_tick_price_flow,
                "contract_multiple": contract_multiple,
                "avg_tr_ticks": int(avg_tr / min_tick_price_flow),
                "std_avg_tr_ticks": cls.__get_std_avg_tr_ticks(avg_tr_ticks=int(avg_tr / min_tick_price_flow)),
            }

        TQZJsonOperator.tqz_write_jsonfile(content=avg_tr_map, target_jsonfile=cls.__avg_tr_path(source_type=source_type))

    @classmethod
    def refresh_pos_json(cls, origin_balance: float, tq_syms: list, per_loss_percent: float = 0.01, source_type: TQZDataSourceType = TQZDataSourceType.CSV):
        assert os.path.exists(cls.__avg_tr_path(source_type=source_type)) is True, f'{cls.__avg_tr_path(source_type=source_type)} not exist'
        if len(tq_syms) is 0:
            print("no items in tq_syms.")
            return

        avg_tr_content = TQZJsonOperator.tqz_load_jsonfile(jsonfile=cls.__avg_tr_path(source_type=source_type))
        per_fund = origin_balance / len(tq_syms)

        pos_map = TQZJsonOperator.tqz_load_jsonfile(jsonfile=cls.__pos_result_path(source_type=source_type))
        for tq_sym in tq_syms:
            renko_size = avg_tr_content[tq_sym]['std_avg_tr_ticks'] * 0.5
            pos = (per_fund * per_loss_percent) / (4 * renko_size * avg_tr_content[tq_sym]["min_tick_price_flow"] * avg_tr_content[tq_sym]["contract_multiple"])
            pos_map[tq_sym] = {
                "pos": pos,
                "std_pos": cls.__get_std_pos(pos),
                "renko_size": renko_size
            }

            TQZJsonOperator.tqz_write_jsonfile(content=pos_map, target_jsonfile=cls.__pos_result_path(source_type=source_type))


    # --- private part ---
    @classmethod
    def __avg_tr_path(cls, source_type: TQZDataSourceType):
        if source_type in [TQZDataSourceType.CSV]:
            return TQZFilePathOperator.father_path(source_path=__file__) + f'/result_data/avg_tr.json'
        elif source_type in [TQZDataSourceType.REAL_ATM]:
            return TQZFilePathOperator.father_path(source_path=__file__) + f'/result_data/real_avg_tr_path.json'
        else:
            assert False, f'bad source_typ: {source_type.value}'

    @classmethod
    def __pos_result_path(cls, source_type: TQZDataSourceType):
        if source_type in [TQZDataSourceType.CSV]:
            return TQZFilePathOperator.father_path(source_path=__file__) + f'/result_data/pos_result.json'
        elif source_type in [TQZDataSourceType.REAL_ATM]:
            return TQZFilePathOperator.father_path(source_path=__file__) + f'/result_data/real_atm_pos_result.json'
        else:
            assert False, f'bad source_typ: {source_type.value}'

    @classmethod
    def __source_content(cls, source_type: TQZDataSourceType):
        if source_type in [TQZDataSourceType.REAL_ATM]:
            return TQZTianQinDataManager.load_main_history_bars_map(
                tq_m_symbols=[
                    "KQ.m@SHFE.cu",
                    "KQ.m@SHFE.rb",
                    "KQ.m@CFFEX.IF",
                    "KQ.m@CFFEX.IC",
                    "KQ.m@CFFEX.T",
                    "KQ.m@SHFE.au",
                    "KQ.m@DCE.i",
                    "KQ.m@DCE.m",
                    "KQ.m@CZCE.CF",
                    "KQ.m@DCE.y",
                    "KQ.m@CZCE.TA",
                    "KQ.m@SHFE.ag",
                    "KQ.m@DCE.p",
                    "KQ.m@SHFE.hc",
                    "KQ.m@SHFE.ru",
                    "KQ.m@DCE.j",
                    "KQ.m@CZCE.MA",
                    "KQ.m@CZCE.SR",
                    "KQ.m@DCE.c",
                    "KQ.m@SHFE.al",
                    "KQ.m@SHFE.ni",
                    "KQ.m@CZCE.OI",
                    "KQ.m@CZCE.FG",
                    "KQ.m@CZCE.SA",
                    "KQ.m@INE.sc",
                    "KQ.m@DCE.v",
                    "KQ.m@CZCE.AP",
                    "KQ.m@DCE.pp",
                    "KQ.m@DCE.jm",
                    "KQ.m@DCE.l",
                    "KQ.m@CZCE.RM",
                    "KQ.m@SHFE.bu",
                    "KQ.m@DCE.eg",
                    "KQ.m@SHFE.zn",
                    "KQ.m@DCE.lh",
                    "KQ.m@SHFE.sp",
                    "KQ.m@CZCE.ZC",
                    "KQ.m@SHFE.fu",
                    "KQ.m@SHFE.sn",
                    "KQ.m@CZCE.SF",
                    "KQ.m@DCE.a",
                    "KQ.m@DCE.jd",
                    "KQ.m@CZCE.SM",
                    "KQ.m@SHFE.ss",
                    "KQ.m@DCE.eb",
                    "KQ.m@DCE.pg",
                    "KQ.m@CZCE.PF",
                    "KQ.m@CZCE.UR",
                    "KQ.m@SHFE.pb",
                    "KQ.m@DCE.cs"
                ],
                tq_duration_seconds=60 * 60,
                tq_data_length=8000
            )
        elif source_type in [TQZDataSourceType.CSV]:
            return TQZTianQinDataManager.load_main_history_bars_from_csv(
                tq_m_symbols=[
                    "KQ.m@SHFE.cu",
                    "KQ.m@SHFE.rb",
                    "KQ.m@CFFEX.IF",
                    "KQ.m@CFFEX.IC",
                    "KQ.m@CFFEX.T",
                    "KQ.m@SHFE.au",
                    "KQ.m@DCE.i",
                    "KQ.m@DCE.m",
                    "KQ.m@CZCE.CF",
                    "KQ.m@DCE.y",
                    "KQ.m@CZCE.TA",
                    "KQ.m@SHFE.ag",
                    "KQ.m@DCE.p",
                    "KQ.m@SHFE.hc",
                    "KQ.m@SHFE.ru",
                    "KQ.m@DCE.j",
                    "KQ.m@CZCE.MA",
                    "KQ.m@CZCE.SR",
                    "KQ.m@DCE.c",
                    "KQ.m@SHFE.al",
                    "KQ.m@SHFE.ni",
                    "KQ.m@CZCE.OI",
                    "KQ.m@CZCE.FG",
                    "KQ.m@CZCE.SA",
                    "KQ.m@INE.sc",
                    "KQ.m@DCE.v",
                    "KQ.m@CZCE.AP",
                    "KQ.m@DCE.pp",
                    "KQ.m@DCE.jm",
                    "KQ.m@DCE.l",
                    "KQ.m@CZCE.RM",
                    "KQ.m@SHFE.bu",
                    "KQ.m@DCE.eg",
                    "KQ.m@SHFE.zn",
                    "KQ.m@DCE.lh",
                    "KQ.m@SHFE.sp",
                    "KQ.m@CZCE.ZC",
                    "KQ.m@SHFE.fu",
                    "KQ.m@SHFE.sn",
                    "KQ.m@CZCE.SF",
                    "KQ.m@DCE.a",
                    "KQ.m@DCE.jd",
                    "KQ.m@CZCE.SM",
                    "KQ.m@SHFE.ss",
                    "KQ.m@DCE.eb",
                    "KQ.m@DCE.pg",
                    "KQ.m@CZCE.PF",
                    "KQ.m@CZCE.UR",
                    "KQ.m@SHFE.pb",
                    "KQ.m@DCE.cs"
                ]
            )
        else:
            assert False, f'bad source_type: {source_type.value}'


    @classmethod
    def __get_std_pos(cls, pos: float) -> int:

        result_std_pos = floor(pos)
        if result_std_pos is 0:  # set pos is 1 at least
            result_std_pos = 1

        return result_std_pos

    @classmethod
    def __get_std_avg_tr_ticks(cls, avg_tr_ticks: int, base_value: int = 10) -> int:
        assert avg_tr_ticks >= 0, f'avg_tr_ticks value is error.({avg_tr_ticks})'

        count = floor(avg_tr_ticks / base_value)
        if avg_tr_ticks % base_value is 0:  # 以 10 为 基准单位
            return count * base_value
        else:
            return (count + 1) * base_value


class TQZStrategyFundManage:

    @classmethod
    def refresh_pos_json(cls, per_loss_percent: float = 0.02):  # noqa
        """"""

        """
        1. 非活跃品种不做 (mean_sed_fund < 8亿);
        TQZFundManage.refresh_pos_json(origin_balance=300000, tq_syms=['CFFEX.IF'], per_loss_percent=per_loss_percent)  # 相比于 CFFEX.IC, 波动率小一点点
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CFFEX.T'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.rb', 'SHFE.au'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.cu', 'DCE.i'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.m', 'CZCE.CF'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.y', 'CZCE.TA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ag', 'DCE.p'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.hc', 'SHFE.ru'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.j', 'CZCE.MA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.SR', 'DCE.c'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.al', 'SHFE.ni'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.OI', 'CZCE.FG'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.SA', 'INE.sc'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.v', 'CZCE.AP'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.pp', 'DCE.jm'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.l', 'CZCE.RM'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.bu', 'DCE.eg'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.zn', 'DCE.lh'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.sp', 'CZCE.ZC'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.fu', 'SHFE.sn'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.SF', 'DCE.a'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.jd', 'CZCE.SM'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ss', 'DCE.eb'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.pg', 'CZCE.PF'], per_loss_percent=per_loss_percent)
        """

        """
        2. 重新设置资管 (mean_sed_fund < 8亿);
        TQZFundManage.refresh_pos_json(origin_balance=300000, tq_syms=['CFFEX.IF'], per_loss_percent=per_loss_percent)  # 相比于 CFFEX.IC, 波动率小一点点
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CFFEX.T'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.rb', 'SHFE.au'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.cu', 'DCE.i'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.m', 'CZCE.CF'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.y', 'CZCE.TA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ag', 'DCE.p'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.hc', 'SHFE.ru'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=200000, tq_syms=['DCE.j'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['CZCE.MA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.SR', 'DCE.c'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.al', 'SHFE.ni'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.OI', 'CZCE.FG'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['CZCE.SA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=250000, tq_syms=['INE.sc'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.v', 'CZCE.AP'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['DCE.pp'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=150000, tq_syms=['DCE.jm'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.l', 'CZCE.RM'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.bu', 'DCE.eg'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.zn', 'DCE.lh'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.sp', 'CZCE.ZC'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.fu', 'SHFE.sn'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.SF', 'DCE.a'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.jd', 'CZCE.SM'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ss', 'DCE.eb'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.pg', 'CZCE.PF'], per_loss_percent=per_loss_percent)
        """


        """ 165w
        3. 回测结果筛选 (TQZFutureRenkoScalpingAutoFundManageStrategy) 
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CFFEX.T'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.au', 'DCE.i'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.CF', 'DCE.y'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ag', 'DCE.p'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['SHFE.hc'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=200000, tq_syms=['DCE.j'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.MA', 'DCE.c'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.al', 'CZCE.FG'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['CZCE.SA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=250000, tq_syms=['INE.sc'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.v', 'DCE.l'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.bu', 'DCE.eg'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.lh', 'SHFE.sp'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.a', 'SHFE.ss'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.eb', 'DCE.pg'], per_loss_percent=per_loss_percent)
        """

        """ 160w
        3. 回测结果筛选 (TQZMarcoTradingStrategy);
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.rb', 'SHFE.au'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.cu', 'DCE.m'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.CF', 'DCE.y'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ag', 'DCE.p'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['SHFE.hc'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=200000, tq_syms=['DCE.j'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.c', 'SHFE.al'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ni', 'CZCE.OI'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=250000, tq_syms=['INE.sc'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.l', 'CZCE.RM'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.eg', 'SHFE.fu'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.sn', 'DCE.a'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ss', 'DCE.eb'], per_loss_percent=per_loss_percent)
        """

        """ 145w
        3. 回测结果筛选 (TQZFutureRenkoWaveAutoFundManageStrategy);
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CFFEX.T'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.rb', 'SHFE.au'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.y', 'CZCE.TA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['DCE.p'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=200000, tq_syms=['DCE.j'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.c', 'SHFE.al'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.FG', 'CZCE.SA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=250000, tq_syms=['INE.sc'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['DCE.v'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=150000, tq_syms=['DCE.jm'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.bu', 'DCE.lh'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.sp', 'DCE.a'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ss', 'DCE.eb'], per_loss_percent=per_loss_percent)
        """


        """
        4. 结构筛选 (同时适应 TQZFutureRenkoWaveAutoFundManageStrategy, TQZFutureRenkoScalpingAutoFundManageStrategy)
        
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CFFEX.T'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.au', 'DCE.y'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['DCE.p'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=200000, tq_syms=['DCE.j'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.c', 'SHFE.al'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.FG', 'CZCE.SA'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=250000, tq_syms=['INE.sc'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.v', 'SHFE.bu'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.lh', 'SHFE.sp'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.a', 'SHFE.ss'], per_loss_percent=per_loss_percent)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['DCE.eb'], per_loss_percent=per_loss_percent)
        
        """




        cls.__copy_pos_json_to_config()

    @classmethod
    def refresh_pos_json_real_atm(cls, per_loss_percent: float = 0.02):  # noqa
        TQZFundManage.refresh_pos_json(origin_balance=300000, tq_syms=['CFFEX.IF'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)  # 相比于 CFFEX.IC, 波动率小一点点
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CFFEX.T'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.rb', 'SHFE.au'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.cu', 'DCE.i'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.m', 'CZCE.CF'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.y', 'CZCE.TA'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ag', 'DCE.p'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.hc', 'SHFE.ru'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=200000, tq_syms=['DCE.j'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['CZCE.MA'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.SR', 'DCE.c'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.al', 'SHFE.ni'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.OI', 'CZCE.FG'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['CZCE.SA'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=250000, tq_syms=['INE.sc'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.v', 'CZCE.AP'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=50000, tq_syms=['DCE.pp'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=150000, tq_syms=['DCE.jm'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.l', 'CZCE.RM'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.bu', 'DCE.eg'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.zn', 'DCE.lh'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.sp', 'CZCE.ZC'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.fu', 'SHFE.sn'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['CZCE.SF', 'DCE.a'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.jd', 'CZCE.SM'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['SHFE.ss', 'DCE.eb'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)
        TQZFundManage.refresh_pos_json(origin_balance=100000, tq_syms=['DCE.pg', 'CZCE.PF'], per_loss_percent=per_loss_percent, source_type=TQZDataSourceType.REAL_ATM)

        cls.__copy_real_atm_pos_json_to_config()


    # --- private part ---
    @classmethod
    def __copy_pos_json_to_config(cls):
        pos_result_map = TQZJsonOperator.tqz_load_jsonfile(
            jsonfile=TQZFilePathOperator.father_path(source_path=__file__) + f'/result_data/pos_result.json'
        )
        target_pos_result_map = {}
        for key, value in pos_result_map.items():
            target_pos_result_map[key] = {
                "std_pos": pos_result_map[key]["std_pos"],
                "renko_size": pos_result_map[key]["renko_size"],
            }

        TQZJsonOperator.tqz_write_jsonfile(
            content=target_pos_result_map,
            target_jsonfile=TQZBackTesterFutureConfigPath.future_pos_result_path()
        )

    @classmethod
    def __copy_real_atm_pos_json_to_config(cls):
        pos_result_map = TQZJsonOperator.tqz_load_jsonfile(
            jsonfile=TQZFilePathOperator.father_path(source_path=__file__) + f'/result_data/real_atm_pos_result.json'
        )
        target_pos_result_map = {}
        for key, value in pos_result_map.items():
            target_pos_result_map[key] = {
                "std_pos": pos_result_map[key]["std_pos"],
                "renko_size": pos_result_map[key]["renko_size"],
            }

        TQZJsonOperator.tqz_write_jsonfile(
            content=target_pos_result_map,
            target_jsonfile=TQZBackTesterFutureConfigPath.future_real_atm_pos_result_path()
        )


if __name__ == '__main__':
    # TQZFundManage.refresh_avg_tr_json(source_type=TQZDataSourceType.CSV)
    # TQZStrategyFundManage.refresh_pos_json()

    # TQZFundManage.refresh_avg_tr_json(source_type=TQZDataSourceType.REAL_ATM)
    TQZStrategyFundManage.refresh_pos_json_real_atm()