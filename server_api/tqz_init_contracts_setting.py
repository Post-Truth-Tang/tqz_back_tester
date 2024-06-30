import re
import os

from server_api.api.tqz_tianqin_api import TQZTianQinClient
from back_tester_branch.back_tester_source_data import TQZBackTesterFutureConfigPath
from public_module.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator

class TQZFutureContractSetting:

    @classmethod
    def reset_future_contract_setting(cls):
        if os.path.exists(path=TQZBackTesterFutureConfigPath.future_contracts_setting_path()) is True:
            return

        result = {}
        all_tq_symbols = TQZTianQinClient().load_all_tq_symbols()
        for tq_symbol in all_tq_symbols:
            exchange_str, symbol = tq_symbol.split('.')[0], tq_symbol.split('.')[1]
            tq_sym = f'{exchange_str}.{cls.get_sym(symbol=symbol)}'
            if tq_sym not in result.keys():
                tq_result = TQZTianQinClient().query_quote(tq_symbol=tq_symbol)
                result[tq_sym] = {
                    "min_tick_price_flow": tq_result['price_tick'],
                    "contract_multiple": tq_result['volume_multiple']
                }

        TQZJsonOperator.tqz_write_jsonfile(content=result, target_jsonfile=TQZBackTesterFutureConfigPath.future_contracts_setting_path())


    @classmethod
    def get_sym(cls, symbol: str):
        return re.match(r"^[a-zA-Z]{1,3}", symbol).group()


if __name__ == '__main__':
    TQZFutureContractSetting.reset_future_contract_setting()
