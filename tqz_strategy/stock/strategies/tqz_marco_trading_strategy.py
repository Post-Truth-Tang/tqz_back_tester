
from tqz_strategy.template import CtaTemplate
from public_module.object import BarData
from public_module.utility import BarGenerator

class TQZMarcoTradingStrategy(CtaTemplate):
    author = "tqz"

    # --- param part ---
    ma_window = 250

    donchian_channel_window = 20

    clear_position_days_window = 10
    n_window = 20

    strategy_fund = 0

    parameters = [
        "ma_window",
        "donchian_channel_window",
        "clear_position_days_window",
        "n_window",
        "strategy_fund"
    ]

    # --- var part ---
    ma_value = 0.0

    donchian_channel_up = 0.0
    donchian_channel_down = 0.0

    clear_position_level_price = 0  # profit
    stop_loss_level_price = 0  # loss

    variables = [
        "ma_value",
        "donchian_channel_up",
        "donchian_channel_down",
        "stop_loss_level_price",
        "clear_position_level_price",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.history_bars = []


    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        if self.__update_params_ok(new_bar=bar) is False:
            return

        long_market = bar.close_price > self.ma_value
        short_market = bar.close_price < self.ma_value

        if long_market:
            if self.pos is 0:
                if bar.high_price > self.donchian_channel_up:
                    self.set_position(position=self.get_current_pos(bar_close_price=bar.close_price), position_change_price=self.donchian_channel_up)
            elif self.pos > 0:
                if bar.low_price < self.clear_position_level_price:
                    self.set_position(position=0, position_change_price=self.clear_position_level_price)
                elif bar.low_price < self.stop_loss_level_price and self.stop_loss_level_price is not 0:
                    self.set_position(position=0, position_change_price=self.stop_loss_level_price)

        elif short_market:
            self.set_position(position=0, position_change_price=bar.close_price)

        # print(f'TQZTurtleTradingStrategy, bar.close_price: {bar.close_price}, self.ma_value: {round(self.ma_value, 3)}, self.donchian_channel_up: {round(self.donchian_channel_up, 3)}, self.donchian_channel_down: {round(self.donchian_channel_down, 3)}, self.stop_loss_level_price: {round(self.stop_loss_level_price, 3)}, self.clear_position_level_price: {round(self.clear_position_level_price, 3)}, pos: {self.pos}')


    def __update_params_ok(self, new_bar: BarData) -> bool:
        if len(self.history_bars) < self.ma_window:
            self.history_bars.append(new_bar)
            return False

        self.history_bars.remove(self.history_bars[0])
        self.history_bars.append(new_bar)

        # ma value
        tmp_ma_value = 0
        for bar in self.history_bars:
            tmp_ma_value += bar.close_price

        self.ma_value = tmp_ma_value / self.ma_window

        # donchian up & down value
        self.donchian_channel_up, self.donchian_channel_down = self.__get_new_donchian_value()

        # clear_position_level_price
        self.clear_position_level_price = self.__get_clear_position_level_price()

        # stop_loss_level_price
        if self.pos > 0:
            self.stop_loss_level_price = self.position_change_price - self.__get_n_value() * 2
        elif self.pos < 0:
            self.stop_loss_level_price = self.position_change_price + self.__get_n_value() * 2

        return True

    def set_position(self, position: int, position_change_price: float):
        self.pos = position

        if self.pos > 0:
            self.position_change_price, self.clear_position_level_price = position_change_price, self.__get_clear_position_level_price()
            self.stop_loss_level_price = position_change_price - 2 * self.__get_n_value()
        elif self.pos < 0:
            self.position_change_price, self.clear_position_level_price = position_change_price, self.__get_clear_position_level_price()
            self.stop_loss_level_price = position_change_price + 2 * self.__get_n_value()
        else:
            self.stop_loss_level_price, self.clear_position_level_price = 0, 0

    def __get_n_value(self):
        n_value = 0
        if self.pos is not 0:
            n_values = []
            for index, bar in enumerate(self.history_bars):
                if index > len(self.history_bars) - self.n_window - 1:
                    pre_bar = self.history_bars[index - 1]
                    tr = max(bar.high_price - bar.close_price, bar.high_price - pre_bar.close_price, pre_bar.close_price - bar.low_price)
                    if len(n_values) is 0:
                        n_values.append(tr)
                    else:
                        n_values.append((n_values[-1] * (self.n_window - 1) + tr) / self.n_window)

            n_value = n_values[-1]

        return n_value

    def __get_clear_position_level_price(self):
        tmp_clear_position_level_price = 0
        if self.pos is not 0:
            for bar in self.history_bars[-self.clear_position_days_window:]:
                if self.pos > 0:
                    if bar.low_price < tmp_clear_position_level_price or tmp_clear_position_level_price is 0:
                        tmp_clear_position_level_price = bar.low_price
                elif self.pos < 0:
                    if bar.high_price > tmp_clear_position_level_price or tmp_clear_position_level_price is 0:
                        tmp_clear_position_level_price = bar.high_price

        return tmp_clear_position_level_price

    def __get_new_donchian_value(self):
        tmp_donchian_channel_up = 0
        tmp_donchian_channel_down = 0

        for bar in self.history_bars[-self.donchian_channel_window:]:
            if bar.high_price > self.donchian_channel_up or tmp_donchian_channel_up is 0:
                tmp_donchian_channel_up = bar.high_price
            if bar.low_price < self.donchian_channel_down or tmp_donchian_channel_down is 0:
                tmp_donchian_channel_down = bar.low_price

        return tmp_donchian_channel_up, tmp_donchian_channel_down



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

    def get_current_pos(self, bar_close_price: float):
        return int((self.strategy_fund / bar_close_price) / self.get_min_stock_lots()) * self.get_min_stock_lots()