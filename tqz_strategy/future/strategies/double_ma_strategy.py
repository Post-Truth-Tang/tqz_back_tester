
from tqz_strategy.template import CtaTemplate
from public_module.object import BarData


class TQZFutureDoubleMaStrategy(CtaTemplate):
    """
    re write.
    """
    author = "tqz"

    fast_window = 30
    slow_window = 250

    lots_size = 0
    parameters = ["fast_window", "slow_window", "lots_size"]

    fast_ma0 = 0
    fast_ma1 = 0

    slow_ma0 = 0
    slow_ma1 = 0
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bar_close_prices = []


    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log(msg=f'strategy_name: {self.strategy_name} on_init.')
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
        pass


    def __update_bars_close_prices(self, new_bar: BarData) -> bool:
        self.bar_close_prices.append(new_bar.close_price)
        if len(self.bar_close_prices) > self.slow_window:
            # update params
            self.slow_ma0 = sum(self.bar_close_prices[-self.slow_window:]) / self.slow_window
            self.slow_ma1 = sum(self.bar_close_prices[-self.slow_window-1:-1]) / self.slow_window
            self.fast_ma0 = sum(self.bar_close_prices[-self.fast_window:]) / self.fast_window
            self.fast_ma1 = sum(self.bar_close_prices[-self.fast_window-1:-1]) / self.fast_window

            bars_is_enough = True
        else:
            bars_is_enough = False

        return bars_is_enough


    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        # 1. update self.bars_close_prices & update params.
        if self.__update_bars_close_prices(new_bar=bar) is False:
            return

        # 2. trend direction.
        cross_over = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 < self.slow_ma1
        cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 > self.slow_ma1

        # 3. modify postion.
        if cross_over:
            if self.pos == 0:
                self.buy(bar.close_price, self.lots_size)
            elif self.pos < 0:
                self.cover(bar.close_price, self.lots_size)
                self.buy(bar.close_price, self.lots_size)
        elif cross_below:
            if self.pos == 0:
                self.short(bar.close_price, self.lots_size)
            elif self.pos > 0:
                self.sell(bar.close_price, self.lots_size)
                self.short(bar.close_price, self.lots_size)

        print(f'DoubleMaStrategy, bar.datetime: {bar.datetime}, bar.close_price: {bar.close_price}, self.fast_ma0: {round(self.fast_ma0, 3)}, self.fast_ma1: {round(self.fast_ma1, 3)}, self.slow_ma0: {round(self.slow_ma0, 3)}, self.slow_ma1: {round(self.slow_ma1, 3)}, pos: {self.pos}')

        self.put_event()
