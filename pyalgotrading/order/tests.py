import unittest
from unittest import TestCase

from pyalgotrading.constants import BrokerOrderTransactionTypeConstants, BrokerOrderTypeConstants
from pyalgotrading.order.order_base import OrderBase
from pyalgotrading.order.order_bracket_base import BuyOrderBracket, SellOrderBracket
from pyalgotrading.order.order_regular_base import BuyOrderRegular, SellOrderRegular

class TestOrderBase(TestCase):
    def test(self):
        order = OrderBase()
        order.place_order()
        order.get_order_status()
        order.exit_position()
        order.cancel_order()

class TestOrderBracket(TestCase):
    def setUp(self):
        self.instrument = 'TATASTEEL'
        self.order_code = '123'
        self.order_variety = 'market'
        self.quantity = 100
        self.price = 150
        self.trigger_price = 160
        self.stoploss_trigger = 140
        self.target_trigger = 170
        self.trailing_stoploss_trigger = 5

    def test_BuyOrderBracket(self):
        order = BuyOrderBracket(
            instrument=self.instrument,
            order_code=self.order_code,
            order_variety=self.order_variety,
            quantity=self.quantity,
            price=self.price,
            trigger_price=self.trigger_price,
            stoploss_trigger=self.stoploss_trigger,
            target_trigger=self.target_trigger,
            trailing_stoploss_trigger=self.trailing_stoploss_trigger
        )
        order.is_closed()
        self.assertEqual(order.instrument, self.instrument)
        self.assertEqual(order.order_transaction_type, BrokerOrderTransactionTypeConstants.BUY)
        self.assertEqual(order.order_code, self.order_code)
        self.assertEqual(order.order_variety, self.order_variety)

    def test_SellOrderBracket(self):
        order = SellOrderBracket(
            instrument=self.instrument,
            order_code=self.order_code,
            order_variety=self.order_variety,
            quantity=self.quantity,
            price=self.price,
            trigger_price=self.trigger_price,
            stoploss_trigger=self.stoploss_trigger,
            target_trigger=self.target_trigger,
            trailing_stoploss_trigger=self.trailing_stoploss_trigger
        )
        self.assertEqual(order.instrument, self.instrument)
        self.assertEqual(order.order_transaction_type, BrokerOrderTransactionTypeConstants.SELL)
        self.assertEqual(order.order_code, self.order_code)
        self.assertEqual(order.order_variety, self.order_variety)

class TestOrderRegular(TestCase):
    def setUp(self):
        self.instrument = 'TATASTEEL'
        self.order_code = '123'
        self.order_variety = 'market'
        self.quantity = 100
        self.price = 150
        self.trigger_price = 160

    def test_BuyOrderRegular(self):
        order = BuyOrderRegular(
            instrument=self.instrument,
            order_code=self.order_code,
            order_variety=self.order_variety,
            quantity=self.quantity,
            price=self.price,
            trigger_price=self.trigger_price,
        )
        self.assertEqual(order.instrument, self.instrument)
        self.assertEqual(order.order_transaction_type, BrokerOrderTransactionTypeConstants.BUY)
        self.assertEqual(order.order_code, self.order_code)
        self.assertEqual(order.order_variety, self.order_variety)
        self.assertEqual(order.quantity, self.quantity)
        self.assertEqual(order.price, self.price)
        self.assertEqual(order.trigger_price, self.trigger_price)


    def test_SellOrderRegular(self):
        order = SellOrderRegular(
            instrument=self.instrument,
            order_code=self.order_code,
            order_variety=self.order_variety,
            quantity=self.quantity,
            price=self.price,
            trigger_price=self.trigger_price,
        )
        self.assertEqual(order.instrument, self.instrument)
        self.assertEqual(order.order_transaction_type, BrokerOrderTransactionTypeConstants.SELL)
        self.assertEqual(order.order_code, self.order_code)
        self.assertEqual(order.order_variety, self.order_variety)
        self.assertEqual(order.quantity, self.quantity)
        self.assertEqual(order.price, self.price)
        self.assertEqual(order.trigger_price, self.trigger_price)

if __name__ == '__main__':
    unittest.main()
