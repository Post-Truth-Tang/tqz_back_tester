
from public_module.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator
from back_tester_branch.back_tester_source_data import TQZBackTesterFutureConfigPath

class TQZFutureStrategiesSetting:

    __back_tester_setting = TQZJsonOperator.tqz_load_jsonfile(jsonfile=TQZBackTesterFutureConfigPath.future_back_tester_setting_path())
    __pos_result = TQZJsonOperator.tqz_load_jsonfile(jsonfile=TQZBackTesterFutureConfigPath.future_pos_result_path())
    __future_contracts_setting = TQZJsonOperator.tqz_load_jsonfile(jsonfile=TQZBackTesterFutureConfigPath.future_contracts_setting_path())

    @classmethod
    def refresh(cls):
        strategy_template_name = cls.__back_tester_setting['future_strategy_template']
        tq_main_contracts = cls.__back_tester_setting['tq_main_contracts']

        if strategy_template_name == "TQZFutureDoubleMaStrategy":
            cls.__refresh_future_ma_strategies(tq_main_contracts=tq_main_contracts, strategy_template_name=strategy_template_name)
        elif strategy_template_name == "TQZMarcoTradingStrategy":
            cls.__refresh_future_marcoTrading_strategies(tq_main_contracts=tq_main_contracts, strategy_template_name=strategy_template_name)
        elif strategy_template_name in ["TQZFutureRenkoWaveStrategy", "TQZFutureRenkoScalpingStrategy"]:
            cls.__refresh_future_renko_strategies(tq_main_contracts=tq_main_contracts, strategy_template_name=strategy_template_name)
        elif strategy_template_name in ["TQZFutureRenkoScalpingAutoFundManageStrategy", "TQZFutureRenkoWaveAutoFundManageStrategy"]:
            cls.__refresh_future_renko_autoFundManage_strategies(tq_main_contracts=tq_main_contracts, strategy_template_name=strategy_template_name)
        else:
            assert False, f'bad strategy_template_name: {strategy_template_name}'

        print("refresh future strategies_setting.json is over.")


    # --- private part ---
    @classmethod
    def __refresh_future_ma_strategies(cls, tq_main_contracts: list, strategy_template_name: str, fast_ma: int = 30, slow_ma: int = 250):
        strategies_setting = {}
        for tq_m_symbol in tq_main_contracts:
            tq_sym = tq_m_symbol.split('@')[1]
            strategy_name = f'{tq_sym}.{strategy_template_name}'

            assert tq_sym in cls.__pos_result.keys(), f'bad tq_sym({tq_sym})'

            strategies_setting[strategy_name] = {
                "class_name": strategy_template_name,
                "vt_symbol": tq_sym,
                "setting": {
                    "class_name": strategy_template_name,
                    "fast_window": fast_ma,
                    "slow_window": slow_ma,
                    "lots_size": cls.__pos_result[tq_sym]["std_pos"]
                }
            }

        TQZJsonOperator.tqz_write_jsonfile(content=strategies_setting, target_jsonfile=TQZBackTesterFutureConfigPath.future_strategies_setting_path())


    @classmethod
    def __refresh_future_renko_autoFundManage_strategies(cls, tq_main_contracts: list, strategy_template_name: str, fast_ma: int = 35, slow_ma: int = 250):
        strategies_setting = {}
        for tq_m_symbol in tq_main_contracts:
            tq_sym = tq_m_symbol.split('@')[1]
            strategy_name = f'{tq_sym}.{strategy_template_name}'

            assert tq_sym in cls.__pos_result.keys(), f'bad tq_sym({tq_sym})'
            strategies_setting[strategy_name] = {
                "class_name": strategy_template_name,
                "vt_symbol": tq_sym,
                "setting": {
                    "class_name": strategy_template_name,
                    "fast_window": fast_ma,
                    "slow_window": slow_ma,
                    "strategy_fund": TQZFutureContractFund.get_contract_fund(tq_sym=tq_sym),
                    "min_tick_price_flow": cls.__future_contracts_setting[tq_sym]['min_tick_price_flow'],
                    "contract_multiple": cls.__future_contracts_setting[tq_sym]['contract_multiple']
                }
            }


        TQZJsonOperator.tqz_write_jsonfile(
            content=strategies_setting,
            target_jsonfile=TQZBackTesterFutureConfigPath.future_strategies_setting_path()
        )

    @classmethod
    def __refresh_future_marcoTrading_strategies(cls, tq_main_contracts: list, strategy_template_name: str, ma_window: int = 250):
        strategies_setting = {}
        for tq_m_symbol in tq_main_contracts:
            tq_sym = tq_m_symbol.split('@')[1]
            strategy_name = f'{tq_sym}.{strategy_template_name}'

            assert tq_sym in cls.__pos_result.keys(), f'bad tq_sym({tq_sym})'

            strategies_setting[strategy_name] = {
                "class_name": strategy_template_name,
                "vt_symbol": tq_sym,
                "setting": {
                    "class_name": strategy_template_name,
                    "ma_window": ma_window,
                    "donchian_channel_window": 20,
                    "clear_position_days_window": 10,
                    "n_window": 20,
                    "lots_size": cls.__pos_result[tq_sym]["std_pos"],
                }
            }

        TQZJsonOperator.tqz_write_jsonfile(
            content=strategies_setting,
            target_jsonfile=TQZBackTesterFutureConfigPath.future_strategies_setting_path()
        )

    @classmethod
    def __refresh_future_renko_strategies(cls, tq_main_contracts: list, strategy_template_name: str, fast_ma: int = 30, slow_ma: int = 250):
        strategies_setting = {}

        for tq_m_symbol in tq_main_contracts:
            tq_sym = tq_m_symbol.split('@')[1]
            strategy_name = f'{tq_sym}.{strategy_template_name}'

            assert tq_sym in cls.__pos_result.keys(), f'bad tq_sym({tq_sym})'

            strategies_setting[strategy_name] = {
                "class_name": strategy_template_name,
                "vt_symbol": tq_sym,
                "setting": {
                    "class_name": strategy_template_name,
                    "fast_window": fast_ma,
                    "slow_window": slow_ma,
                    "lots_size": cls.__pos_result[tq_sym]["std_pos"],
                    "renko_size": cls.__pos_result[tq_sym]["renko_size"],
                    "min_tick_price_flow": cls.__future_contracts_setting[tq_sym]['min_tick_price_flow']
                }
            }

        TQZJsonOperator.tqz_write_jsonfile(
            content=strategies_setting,
            target_jsonfile=TQZBackTesterFutureConfigPath.future_strategies_setting_path()
        )

class TQZFutureContractFund:

    @classmethod
    def get_contract_fund(cls, tq_sym: str) -> float:
        future_contracts_fund = {
            "CFFEX.T": 100000,
            "DCE.jm": 150000,
            "DCE.j": 200000,
            "INE.sc": 250000,

            "CFFEX.IF": 300000,
            "CFFEX.IC": 300000,
            "CFFEX.IH": 300000
        }

        if tq_sym in future_contracts_fund.keys():
            return future_contracts_fund[tq_sym]
        else:
            return 50000


if __name__ == '__main__':
    TQZFutureStrategiesSetting.refresh()