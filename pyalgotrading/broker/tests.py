from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd

from pyalgotrading.broker.broker_connection_zerodha import BrokerConnectionZerodha
from pyalgotrading.constants import BrokerOrderTypeConstants, BrokerOrderTransactionTypeConstants, BrokerOrderCodeConstants, BrokerOrderVarietyConstants
from pyalgotrading.instrument.instrument import Instrument


class TestBrokerConnectionZerodha(TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.api_secret = "test_api_secret"
        self.broker = BrokerConnectionZerodha(self.api_key, self.api_secret)
        self.api = MagicMock(name='mock_broker_api')
        self.broker.api = self.api
        # Creating an Instrument instance
        self.instrument = Instrument('NSE_FO',
                                     'NSE',
                                     'MRF25NOV2177500CE',
                                     107320,
                                     0.0500,
                                     10,
                                     2021 - 11 - 25,
                                     77500.0000)
        self.broker.api.instruments.return_value = {
            'segment': ['NSE_FO', 'BSE'],
            'exchange': ["NSE", "BSE"],
            'tradingsymbol': ["MRF25NOV2177500CE", "BSE:ADANI"],
            'instrument_token': [107320, 107321],
            'tick_size': [0.0500, 0.1],
            'lot_size': [10, 20],
            'expiry': [2021 - 11 - 25, 2021 - 11 - 26],
            'strike': [77500.0000, 87500.0000]
        }
        self.datetime = datetime.now()
        self.broker.api.quote.return_value = {
            'NSE_FO:MRF25NOV2177500CE': {
                'depth': {
                    'buy': [{'price': 100, 'quantity': 10}],
                    'sell': [{'price': 200, 'quantity': 5}]
                },
                'lower_circuit_limit': 100,
                'upper_circuit_limit': 200,
                'last_price': 150,
                'last_trade_time': self.datetime,
                'last_quantity': 20,
                'buy_quantity': 30,
                'sell_quantity': 40,
                'volume': 1000,
                'ohlc': {
                    'open': 120,
                    'high': 160,
                    'low': 110,
                    'close': 140
                }
            }
        }
        self.broker.api.historical_data.return_value = [
            {"date": "2022-01-02", "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
            {"date": "2022-01-03", "open": 105, "high": 115, "low": 95, "close": 110, "volume": 1200},
            {"date": "2022-01-04", "open": 110, "high": 120, "low": 100, "close": 115, "volume": 1500}
        ]
        self.broker.api.margins.return_value = {'net': 1000, 'utilised': 500}

    def test_get_name(self):
        result = self.broker.get_name()
        self.assertEqual(result, 'ZERODHA')

    def test_set_access_token(self):
        self.broker.set_access_token('request_token')
        self.broker.api.generate_session.assert_called_once()
        self.assertEqual(self.broker.api.get_access_token, self.api.get_access_token)

    @patch("pandas.DataFrame", MagicMock(return_value="Mock DataFrame"))
    def test_get_all_instruments(self):
        result = self.broker.get_all_instruments()
        self.assertEqual(result, "Mock DataFrame")

    @patch('builtins.print')
    def test_get_instrument(self, mock_print):
        result = self.broker.get_instrument("NSE_FO", "MRF25NOV2177500CE")
        self.assertIsNotNone(result)
        self.broker.api.instruments.assert_called_once()

        # When expired and not available Instrument
        result = self.broker.get_instrument("NYE", "MRF25NOV2177500CE")
        self.assertIsNone(result)
        mock_print.assert_called_with('ERROR: Instrument not found. Either it is expired and hence not available, or you have misspelled the "segment" and "tradingsymbol" parameters.')
        self.broker.api.instruments.assert_called_once()

    def test_get_market_depth(self):
        result = self.broker.get_market_depth(self.instrument)
        buy_market_depth, sell_market_depth = result
        self.assertTrue(buy_market_depth.equals(pd.DataFrame({'price': 100, 'quantity': 10}, index=[0])))
        self.assertTrue(sell_market_depth.equals(pd.DataFrame({'price': 200, 'quantity': 5}, index=[0])))

    def test_get_circuit_limits(self):
        result = self.broker.get_circuit_limits(self.instrument)
        self.assertEqual(result, (100, 200))

    def test_get_ltp(self):
        result = self.broker.get_ltp(self.instrument)
        self.assertEqual(result, 150)

    def test_get_ltt(self):
        result = self.broker.get_ltt(self.instrument)
        self.assertEqual(result, self.datetime)

    def test_get_ltq(self):
        result = self.broker.get_ltq(self.instrument)
        self.assertEqual(result, 20)

    def test_get_total_pending_buy_quantity(self):
        result = self.broker.get_total_pending_buy_quantity(self.instrument)
        self.assertEqual(result, 30)

    def test_get_total_pending_sell_quantity(self):
        result = self.broker.get_total_pending_sell_quantity(self.instrument)
        self.assertEqual(result, 40)

    def test_get_total_volume_day(self):
        result = self.broker.get_total_volume_day(self.instrument)
        self.assertEqual(result, 1000)

    def test_get_open_price_day(self):
        result = self.broker.get_open_price_day(self.instrument)
        self.assertEqual(result, 120)

    def test_get_high_price_day(self):
        result = self.broker.get_high_price_day(self.instrument)
        self.assertEqual(result, 160)

    def test_get_low_price_day(self):
        result = self.broker.get_low_price_day(self.instrument)
        self.assertEqual(result, 110)

    def test_get_close_price_last_day(self):
        result = self.broker.get_close_price_last_day(self.instrument)
        self.assertEqual(result, 140)

    def test_get_margins(self):
        result = self.broker.get_margins("equity")
        self.assertEqual(result, {'net': 1000, 'utilised': 500})

    def test_get_funds(self):
        result = self.broker.get_funds("equity")
        self.assertEqual(result, 1000)

    def test_place_order(self):
        self.broker.api.place_order.return_value = "Order placed successfully"
        result = self.broker.place_order(
            self.instrument,
            BrokerOrderTransactionTypeConstants.BUY,
            BrokerOrderTypeConstants.REGULAR,
            BrokerOrderCodeConstants.INTRADAY,
            BrokerOrderVarietyConstants.MARKET,
            100,
            1500,
        )
        self.assertEqual(result, "Order placed successfully")

    def test_cancel_order(self):
        self.broker.api.cancel_order.return_value = "Order cancelled successfully"
        result = self.broker.cancel_order(25, BrokerOrderTypeConstants.REGULAR)
        self.assertEqual(result, "Order cancelled successfully")
