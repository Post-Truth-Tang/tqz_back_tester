import re
from abc import ABC
from copy import copy
from typing import Any, Callable

from public_module.constant import Interval, Direction, Offset
from public_module.object import BarData, TickData, OrderData, TradeData
from public_module.utility import virtual

from public_module.base import StopOrder


class CtaTemplate(ABC):
    """"""

    author = ""
    parameters = []
    variables = []

    back_tester_type = True

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        """"""
        self.cta_engine = cta_engine
        self.strategy_name = strategy_name
        self.vt_symbol = vt_symbol

        self.inited = False
        self.trading = False
        self.pos = 0
        self.position_change_price = 0

        # Copy a new variables list here to avoid duplicate insert when multiple
        # strategy instances are created with the same strategy class.
        self.variables = copy(self.variables)
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")

        self.update_setting(setting)

    def update_setting(self, setting: dict):
        """
        Update strategy parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls):
        """
        Get default parameters dict of strategy class.
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        strategy_parameters = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    def get_variables(self):
        """
        Get strategy variables dict.
        """
        strategy_variables = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    def get_data(self):
        """
        Get strategy data.
        """
        strategy_data = {
            "strategy_name": self.strategy_name,
            "vt_symbol": self.vt_symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    @virtual
    def on_init(self):
        """
        Callback when strategy is inited.
        """
        pass

    @virtual
    def on_start(self):
        """
        Callback when strategy is started.
        """
        pass

    @virtual
    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        pass

    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass

    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    @virtual
    def on_daily_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    @virtual
    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass

    @virtual
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass


    @virtual
    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def buy(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send buy order to open a long position.
        """

        if self.back_tester_type:
            self.pos += volume

        return self.send_order(Direction.LONG, Offset.OPEN, price, volume, stop, lock)

    def sell(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send sell order to close a long position.
        """

        if self.back_tester_type:
            self.pos -= volume

        return self.send_order(Direction.SHORT, Offset.CLOSE, price, volume, stop, lock)

    def short(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send short order to open as short position.
        """

        if self.back_tester_type:
            self.pos -= volume

        return self.send_order(Direction.SHORT, Offset.OPEN, price, volume, stop, lock)

    def cover(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send cover order to close a short position.
        """

        if self.back_tester_type:
            self.pos += volume

        return self.send_order(Direction.LONG, Offset.CLOSE, price, volume, stop, lock)


    def send_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False
    ):
        """
        Send a new order.
        """
        pass

    def cancel_order(self, vt_orderid: str):
        """
        Cancel an existing order.
        """
        pass

    def cancel_all(self):
        """
        Cancel all orders sent by strategy.
        """
        pass

    def write_log(self, msg: str):  # noqa
        """
        Write a log message.
        """
        print(f'{msg}')


    def get_engine_type(self):
        """
        Return whether the cta_engine is backtesting or live trading.
        """
        pass


    def get_pricetick(self):
        """
        Return pricetick data of trading contract.
        """
        pass

    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable = None,
        use_database: bool = False
    ):
        """
        Load historical bar data for initializing strategy.
        """
        pass

    def load_tick(self, days: int):
        """
        Load historical tick data for initializing strategy.
        """
        pass

    def put_event(self):
        """
        Put an strategy data event for ui update.
        """
        pass

    def send_email(self, msg):
        """
        Send email to default receiver.
        """
        pass

    def sync_data(self):
        """
        Sync strategy variables value into disk storage.
        """
        pass


    def get_min_stock_lots(self) -> int:
        """
        Judge limit up of vt_symbol is twenty percent or not
        """

        stock_start_3_alpha = re.match(r"^[0-9]{3}", self.vt_symbol).group()
        if stock_start_3_alpha in ["688", "300"]:
            min_lots = 200
        else:
            min_lots = 100

        return min_lots
