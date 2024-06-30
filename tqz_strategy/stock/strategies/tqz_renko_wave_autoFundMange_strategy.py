from math import ceil, floor

from tqz_strategy.template import CtaTemplate
from public_module.object import BarData, RenkoData
from public_module.constant import RenkoDirection
from public_module.utility import BarGenerator

"""
背驰 or 转势 离场
"""
class TQZStockRenkoWaveAutoFundManageStrategy(CtaTemplate):
    """
    future strategy(1h period).
    """
    author = "tqz"

    # --- param part ---
    fast_window = 30
    slow_window = 250

    min_tick_price_flow = 0
    strategy_fund = 0

    parameters = ["fast_window", "slow_window", "strategy_fund", "min_tick_price_flow"]

    # --- var part ---
    pre_ma_direction = RenkoDirection.NO
    current_ma_direction = RenkoDirection.NO

    variables = ["pre_ma_direction", "current_ma_direction"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.renko_size = 0

        self.bg = BarGenerator(self.on_bar)

        self.history_bars = []  # slow_window bars
        self.bar_close_prices = []  # all bars
        self.renko_list = []

        self.high_renko_prices = []
        self.low_renko_prices = []

        self.first_bar_close_price = 0


    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        # 1. update params.
        if self.__update_params_ok(new_bar=bar) is False:
            return
        if len(self.renko_list) < 2:
            return

        # 2. modify postion.
        last_renko0 = self.renko_list[-1]
        last_renko1 = self.renko_list[-2]
        if self.current_ma_direction == RenkoDirection.LONG:
            if self.pos == 0:
                if last_renko1.renko_direction == RenkoDirection.SHORT and last_renko0.renko_direction == RenkoDirection.LONG:
                    self.set_position(pos=self.get_current_pos(bar_close_price=bar.close_price))

            elif self.pos > 0:
                if last_renko1.renko_direction == RenkoDirection.LONG and last_renko0.renko_direction == RenkoDirection.SHORT:
                    if len(self.high_renko_prices) >= 2:
                        if self.high_renko_prices[-1] < self.high_renko_prices[-2]:
                            self.set_position(pos=0)

        elif self.current_ma_direction == RenkoDirection.SHORT:
            self.set_position(pos=0)


    def __update_params_ok(self, new_bar: BarData) -> bool:
        if len(self.history_bars) < self.slow_window:
            self.history_bars.append(new_bar)
            self.bar_close_prices.append(new_bar.close_price)
            return False

        # update self.history_bars & self.bar_close_prices
        self.history_bars.remove(self.history_bars[0])
        self.history_bars.append(new_bar)

        self.bar_close_prices.append(new_bar.close_price)


        # update current_ma_direction & pre_ma_direction
        self.__update_ma_direction()


        # update renko_list | (renko_list & renko_size & lots_size)
        if self.current_ma_direction != self.pre_ma_direction:
            # reset renko_size
            self.__reset_renko_size()

            # reset renko_list
            self.renko_list, self.first_bar_close_price = [], 0
            for new_bar_close_price in self.bar_close_prices:
                self.__update_renko_list(new_bar_close_price=new_bar_close_price, renko_size=self.renko_size)
        else:
            # update renko_list
            self.__update_renko_list(new_bar_close_price=new_bar.close_price, renko_size=self.renko_size)

        return True


    def __update_renko_list(self, new_bar_close_price: float, renko_size: int):
        if len(self.renko_list) is 0:
            if self.first_bar_close_price is 0:  # init strategy.
                self.first_bar_close_price = new_bar_close_price
            else:
                """ 判断是否满足生成第一个renko的条件 """
                ticks_diff = (new_bar_close_price - self.first_bar_close_price) / self.min_tick_price_flow
                if ticks_diff > renko_size:
                    """ 更新第一个renko为红色 """
                    renko_counts = floor(ticks_diff / renko_size)
                    renko_price = self.first_bar_close_price + renko_counts * renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.LONG, renko_value=renko_counts))

                elif ticks_diff < -1 * renko_size:
                    """ 更新第一个renko为绿色 """
                    renko_counts = ceil(ticks_diff / renko_size)
                    renko_price = self.first_bar_close_price + renko_counts * renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.SHORT, renko_value=renko_counts))

        else:
            last_renko = self.renko_list[-1]
            ticks_diff = (new_bar_close_price - last_renko.renko_price) / self.min_tick_price_flow
            if last_renko.renko_direction == RenkoDirection.LONG:  # 当前为红砖
                if ticks_diff > renko_size:
                    """ 新增红砖 """
                    renko_counts = floor(ticks_diff / renko_size)
                    renko_price = last_renko.renko_price + renko_counts * renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.LONG, renko_value=last_renko.renko_value+renko_counts))

                elif ticks_diff < -2 * renko_size:
                    """ 新增绿砖 """
                    renko_counts = ceil(ticks_diff / renko_size)
                    renko_price = last_renko.renko_price + renko_counts * renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.SHORT, renko_value=renko_counts+1))

                    if self.pos > 0:
                        self.high_renko_prices.append(renko_price)

            elif last_renko.renko_direction == RenkoDirection.SHORT:  # 当前为绿砖
                if ticks_diff < -1 * renko_size:
                    """ 新增绿砖 """
                    renko_counts = ceil(ticks_diff / renko_size)
                    renko_price = last_renko.renko_price + renko_counts * renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.SHORT, renko_value=last_renko.renko_value+renko_counts))

                elif ticks_diff > 2 * renko_size:
                    """ 新增红砖 """
                    renko_counts = floor(ticks_diff / renko_size)
                    renko_price = last_renko.renko_price + renko_counts * renko_size * self.min_tick_price_flow
                    self.renko_list.append(RenkoData(renko_price=renko_price, renko_direction=RenkoDirection.LONG, renko_value=renko_counts-1))

                    if self.pos < 0:
                        self.low_renko_prices.append(renko_price)


    def __update_ma_direction(self):
        # calculate fast ma value & slow ma value
        fast_ma_value = sum(self.bar_close_prices[-self.fast_window:]) / self.fast_window
        slow_ma_value = sum(self.bar_close_prices[-self.slow_window:]) / self.slow_window

        # update self.pre_ma_direction & self.current_ma_direction
        if fast_ma_value > slow_ma_value:
            self.pre_ma_direction = self.current_ma_direction
            self.current_ma_direction = RenkoDirection.LONG
        elif fast_ma_value < slow_ma_value:
            self.pre_ma_direction = self.current_ma_direction
            self.current_ma_direction = RenkoDirection.SHORT

    def __reset_renko_size(self):
        trs = []
        for bar in self.history_bars:
            trs.append(bar.high_price - bar.low_price)

        begin_index = floor(len(self.history_bars) * 0.1)
        end_index = len(self.history_bars) - begin_index
        avg_tr = sum(trs[begin_index:end_index]) / len(trs[begin_index:end_index])

        self.renko_size = 0.5 * self.__get_std_avg_tr_ticks(avg_tr_ticks=int(avg_tr / self.min_tick_price_flow))


    @staticmethod
    def __get_std_avg_tr_ticks(avg_tr_ticks: int, base_value: int = 10) -> int:
        count = floor(avg_tr_ticks / base_value)
        if avg_tr_ticks % base_value is 0:
            return count * base_value
        else:
            return (count + 1) * base_value

    def set_position(self, pos: int):
        if (self.pos > 0 and pos < 0) or (self.pos < 0 and pos > 0) or (pos is 0):
            self.high_renko_prices = []
            self.low_renko_prices = []

        self.pos = pos


    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log(msg=f'strategy_name: {self.strategy_name}, fast_window: {self.fast_window}, slow_window: {self.slow_window}, min_tick_price_flow: {self.min_tick_price_flow}, strategy_fund: {self.strategy_fund}, renko_size: {self.renko_size}  on_init.')
        pass

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log(msg=f'strategy_name: {self.strategy_name} on_start.')
        pass

    def on_stop(self):
        self.write_log(msg=f'strategy_name: {self.strategy_name} on_stop.')

    def get_current_pos(self, bar_close_price: float):
        return int((self.strategy_fund / bar_close_price) / self.get_min_stock_lots()) * self.get_min_stock_lots()
