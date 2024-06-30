import os
import importlib
import traceback
from pathlib import Path

from public_module.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator
from public_module.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator

from server_api.api.tqz_tianqin_api import TQZTianQinDataManager

from tqz_strategy.template import CtaTemplate

"""
stock part
"""
class TQZBackTesterStockConfigPath:
    @classmethod
    def stock_back_tester_setting_path(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_config/stock/back_tester_setting.json'

    @classmethod
    def stock_pool_setting_path(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_config/stock/if300_ic500_stock_pool.xlsx'


class TQZBackTesterStockSourceData:
    __stock_back_tester_setting = TQZJsonOperator.tqz_load_jsonfile(
        jsonfile=TQZBackTesterStockConfigPath.stock_back_tester_setting_path()
    )

    @classmethod
    def load_stock_strategy_templates(cls) -> dict:
        all_strategies_classes = TQZStrategyTemplate.get_all_strategy_classes(type_str='stock')

        stock_strategy_templates = {}
        for stock_strategy_template in cls.__stock_back_tester_setting['stock_strategy_templates']:
            assert stock_strategy_template in all_strategies_classes.keys(), f'bad stock_strategy_template: {stock_strategy_template}'

            stock_strategy_templates[stock_strategy_template] = {
                "start_date": cls.__stock_back_tester_setting['start_date'],
                "end_date": cls.__stock_back_tester_setting['end_date'],
                "interval": cls.__stock_back_tester_setting['interval'],
                "tick_value": cls.__stock_back_tester_setting['tick_value'],
                "strategy_fund": cls.__stock_back_tester_setting['strategy_fund'],
                "stock_strategy_template": all_strategies_classes[stock_strategy_template]
            }

        return stock_strategy_templates


"""
future part
"""
class TQZBackTesterFutureConfigPath:

    @classmethod
    def future_back_tester_setting_path(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_config/future/back_tester_setting.json'

    @classmethod
    def future_strategies_setting_path(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_config/future/strategies_setting.json'


    @classmethod
    def future_contracts_setting_path(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_config/future/future_contracts_setting.json'

    @classmethod
    def future_pos_result_path(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_config/future/pos_result.json'

    @classmethod
    def future_real_atm_pos_result_path(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_config/future/real_atm_pos_result.json'


class TQZBackTesterFutureSourceData:
    __future_back_tester_setting = TQZJsonOperator.tqz_load_jsonfile(
        jsonfile=TQZBackTesterFutureConfigPath.future_back_tester_setting_path()
    )

    @classmethod
    def load_future_strategies(cls) -> dict:
        """ """
        all_strategies_classes = TQZStrategyTemplate.get_all_strategy_classes(type_str='future')

        assert cls.__future_back_tester_setting['future_strategy_template'] in all_strategies_classes.keys(), f'bad future_strategy_template: {cls.__future_back_tester_setting["future_strategy_template"]}'

        strategies_setting = TQZJsonOperator.tqz_load_jsonfile(jsonfile=TQZBackTesterFutureConfigPath.future_strategies_setting_path())

        strategy_template = all_strategies_classes[cls.__future_back_tester_setting['future_strategy_template']]
        strategies = {}
        for strategy_name, data in strategies_setting.items():
            for tq_m_symbol in cls.__load_future_history_bars_map().keys():
                if tq_m_symbol.split('@')[1] == data['vt_symbol']:
                    strategies[strategy_name] = {
                        "strategy": strategy_template(None, strategy_name, data['vt_symbol'], data['setting']),
                        "bars": cls.__load_future_history_bars_map()[tq_m_symbol]
                    }

        return strategies


    # --- private part ---
    @classmethod
    def __load_future_history_bars_map(cls):
        return TQZTianQinDataManager.load_main_history_bars_from_csv(
            tq_m_symbols=cls.__future_back_tester_setting['tq_main_contracts']
        )


"""
public part
"""
class TQZBackTesterResultPath:
    @classmethod
    def future_fold(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_result/future'

    @classmethod
    def stock_fold(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_result/stock'

    @classmethod
    def stock_ic500_fold(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_result/stock/ic500'

    @classmethod
    def stock_if300_fold(cls) -> str:
        return TQZFilePathOperator.grandfather_path(
            source_path=__file__
        ) + f'/back_tester_result/stock/if300'


class TQZStrategyTemplate:

    @classmethod
    def get_all_strategy_classes(cls, type_str: str) -> dict:
        """ """
        root = Path(__file__).parent.parent
        stock_strategies_path = root.joinpath("tqz_strategy", type_str, "strategies")
        module_name = f'tqz_strategy.{type_str}.strategies'

        strategies_classes = {}

        for dirpath, dirnames, filenames in os.walk(stock_strategies_path):
            for filename in filenames:
                if filename.endswith(".py"):
                    strategy_module_name = ".".join(
                        [module_name, filename.replace(".py", "")])

                    try:
                        module = importlib.import_module(strategy_module_name)
                        importlib.reload(module)

                        for name in dir(module):
                            value = getattr(module, name)
                            if isinstance(value, type) and issubclass(value, CtaTemplate) and value is not CtaTemplate:
                                strategies_classes[value.__name__] = value
                    except:  # noqa
                        assert False, f"策略文件{module_name}加载失败，触发异常：\n{traceback.format_exc()}"

        return strategies_classes


if __name__ == '__main__':
    """ future part
    _strategies = TQZBackTesterFutureSourceData.load_future_strategies()
    for _strategy_name, _data in _strategies.items():
        print("strategy_name: " + str(_strategy_name))
        print("strategy: " + str(_data['strategy']))
        print("bars[:10]: " + str(_data['bars'][:10]))

        exit()
    """

    TQZBackTesterStockSourceData.load_stock_strategy_templates()
