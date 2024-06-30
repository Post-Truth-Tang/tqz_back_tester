from math import ceil, floor

from tqz_strategy.template import CtaTemplate
from public_module.object import BarData, RenkoData
from public_module.constant import RenkoDirection
from public_module.utility import BarGenerator


"""
背驰 or 转势 离场
"""
class TQZStockRenkoWaveStrategy(CtaTemplate):
    """
    stock strategy(1d period).
    """
    author = "tqz"

    # --- param part ---
    fast_window = 30
    slow_window = 250

    strategy_fund = 0
    renko_size = 0

    min_tick_price_flow = 0

    parameters = ["fast_window", "slow_window", "strategy_fund", "renko_size", "min_tick_price_flow"]

    # --- var part ---
    fast_ma_value = 0.0
    # fast_ma1 = 0.0

    slow_ma_value = 0.0
    # slow_ma1 = 0.0

    variables = ["fast_ma_value", "slow_ma_value"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)

        self.bar_close_prices = []
        self.renko_list = []

        self.high_renko_prices = []
        self.low_renko_prices = []

        self.first_bar_close_price = 0


    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        # 1. update self.bars_close_prices & update params.
        if self.__update_params_ok(new_bar=bar) is False:
            return
        if len(self.renko_list) < 2:
            return

        # 2. trend direction.
        long_direction = self.fast_ma_value > self.slow_ma_value
        short_direction = self.fast_ma_value < self.slow_ma_value

        # 3. modify postion.
        last_renko0 = self.renko_list[-1]
        last_renko1 = self.renko_list[-2]
        if long_direction:
            if self.pos == 0:
                if last_renko1.renko_direction == RenkoDirection.SHORT and last_renko0.renko_direction == RenkoDirection.LONG:
                    self.set_position(pos=self.get_current_pos(bar_close_price=bar.close_price))

            elif self.pos > 0:
                if last_renko1.renko_direction == RenkoDirection.LONG and last_renko0.renko_direction == RenkoDirection.SHORT:
                    if len(self.high_renko_prices) >= 2:
                        if self.high_renko_prices[-1] < self.high_renko_prices[-2]:
                            self.set_position(pos=0)

        elif short_direction:
            self.set_position(pos=0)

    def __update_params_ok(self, new_bar: BarData) -> bool:
        if len(self.bar_close_prices) < self.slow_window:
            self.bar_close_prices.append(new_bar.close_price)
            self.__update_renko_list(new_bar=new_bar)
            return False

        # update self.bar_close_prices
        self.bar_close_prices.remove(self.bar_close_prices[0])
        self.bar_close_prices.append(new_bar.close_price)

        # update fast_ma & slow_ma
        self.fast_ma_value = sum(self.bar_close_prices[-self.fast_window:]) / self.fast_window
        self.slow_ma_value = sum(self.bar_close_prices[-self.slow_window:]) / self.slow_window

        # update renko_list
        self.__update_renko_list(new_bar=new_bar)

        return True

    def __update_renko_list(self, new_bar: BarData):
        if len(self.renko_list) is 0:
            if self.first_bar_close_price is 0:  # init strategy.
                self.first_bar_close_price = new_bar.close_price
            else:
                """ 判断是否满足生成第一个renko的条件 """
                ticks_diff = (new_bar.close_price - self.first_bar_close_price) / self.min_tick_price_flow
                if ticks_diff > self.renko_size:
                    """ 更新第一个renko为红色 """
                    renko_counts = floor(ticks_diff / self.renko_size)
                    renko_price = self.first_bar_close_price + renko_counts * self.renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.LONG, renko_value=renko_counts))

                elif ticks_diff < -1 * self.renko_size:
                    """ 更新第一个renko为绿色 """
                    renko_counts = ceil(ticks_diff / self.renko_size)
                    renko_price = self.first_bar_close_price + renko_counts * self.renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.SHORT, renko_value=renko_counts))

        else:
            last_renko = self.renko_list[-1]
            ticks_diff = (new_bar.close_price - last_renko.renko_price) / self.min_tick_price_flow
            if last_renko.renko_direction == RenkoDirection.LONG:  # 当前为红砖
                if ticks_diff > self.renko_size:
                    """ 新增红砖 """
                    renko_counts = floor(ticks_diff / self.renko_size)
                    renko_price = last_renko.renko_price + renko_counts * self.renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.LONG, renko_value=last_renko.renko_value+renko_counts))

                elif ticks_diff < -2 * self.renko_size:
                    """ 新增绿砖 """
                    renko_counts = ceil(ticks_diff / self.renko_size)
                    renko_price = last_renko.renko_price + renko_counts * self.renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.SHORT, renko_value=renko_counts+1))

                    if self.pos > 0:
                        self.high_renko_prices.append(renko_price)

            elif last_renko.renko_direction == RenkoDirection.SHORT:   # 当前为绿砖
                if ticks_diff < -1 * self.renko_size:
                    """ 新增绿砖 """
                    renko_counts = ceil(ticks_diff / self.renko_size)
                    renko_price = last_renko.renko_price + renko_counts * self.renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.SHORT, renko_value=last_renko.renko_value+renko_counts))

                elif ticks_diff > 2 * self.renko_size:
                    """ 新增红砖 """
                    renko_counts = floor(ticks_diff / self.renko_size)
                    renko_price = last_renko.renko_price + renko_counts * self.renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.LONG, renko_value=renko_counts-1))

                    if self.pos < 0:
                        self.low_renko_prices.append(renko_price)

    def set_position(self, pos: int):
        if (self.pos > 0 and pos < 0) or (self.pos < 0 and pos > 0) or (pos is 0):
            self.high_renko_prices = []
            self.low_renko_prices = []

        self.pos = pos

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log(msg=f'strategy_name: {self.strategy_name}, fast_window: {self.fast_window}, slow_window: {self.slow_window}, strategy_fund: {self.strategy_fund}, renko_size: {self.renko_size}, min_tick_price_flow: {self.min_tick_price_flow} on_init.')
        pass

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log(msg=f'strategy_name: {self.strategy_name} on_start.')
        pass

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log(msg=f'strategy_name: {self.strategy_name} on_stop.')

    def get_current_pos(self, bar_close_price: float):
        return int((self.strategy_fund / bar_close_price) / self.get_min_stock_lots()) * self.get_min_stock_lots()