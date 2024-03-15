from unittest import TestCase
from unittest.mock import patch, Mock

import pandas as pd

from .func import import_with_install, get_datetime_with_tz, calculate_slippage, slippage, calculate_brokerage, plot_candlestick_chart
from pyalgotrading.constants import TradingType, PlotType
from datetime import datetime, timezone
import random


class TestFunctions(TestCase):
    def setUp(self):
        pass

    @patch("pyalgotrading.utils.func.subprocess.check_call")
    def test_import_with_install(self, mock_check_call):
        package_import_name = "pandas"
        result = import_with_install(package_import_name)
        self.assertEqual(result.__name__, package_import_name)

        with patch('builtins.__import__', side_effect=[ImportError("error message"), "mock_result"]):
            result = import_with_install(package_import_name, dependancies=["invalid_dependency"])
            self.assertEqual(result, "mock_result")

        mock_check_call.assert_called_once()

    def test_get_datetime_with_tz(self):
        # try
        timestamp_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M %z')
        trading_type = TradingType.BACKTESTING
        result = get_datetime_with_tz(timestamp_str, trading_type)
        self.assertEqual(result, datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M %z'))

        # except ValueError:
        #   try:
        timestamp_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
        trading_type = TradingType.BACKTESTING
        result = get_datetime_with_tz(timestamp_str, trading_type)
        self.assertEqual(result, datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc))

        # except ValueError:
        #    except ValueError:
        timestamp_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        trading_type = TradingType.BACKTESTING
        with self.assertRaises(ValueError):
            get_datetime_with_tz(timestamp_str, trading_type)

    @patch('random.choice', side_effect=lambda x: 1)
    def test_slippage(self, mock_choice):
        # if variety in ['MARKET', 'STOPLOSS_MARKET']:
        price = 245
        variety = 'MARKET'
        transaction_type = 'BUY'

        slip_percent = abs(1) / 100
        expected_result = price * (1 + 1 * slip_percent)
        result = slippage(price, variety, transaction_type)
        self.assertEqual(result, expected_result)

        # else:
        #   if transaction_type == 'BUY':
        mock_choice.reset_mock()
        mock_choice.side_effect = lambda x: 0
        variety = 'LIMIT'
        expected_result = round(price * (1 + 0 * slip_percent), 2)
        result = slippage(price, variety, transaction_type)
        self.assertEqual(result, expected_result)

        # else:
        #   else:
        mock_choice.reset_mock()
        mock_choice.side_effect = lambda x: 1
        transaction_type = 'SELL'
        expected_result = round(price * (1 + 1 * slip_percent), 2)
        result = slippage(price, variety, transaction_type)
        self.assertEqual(result, expected_result)

    @patch('random.choice', side_effect=lambda x: 1)
    def test_calculate_slippage(self, mock_choice):
        pnl_dict = {
            "entry_price": [245, 261],
            "entry_transaction_type": ["BUY", "SELL"],
            "exit_price": [465, 324],
            "exit_transaction_type": ["SELL", "BUY"]
        }
        pnl_df = pd.DataFrame(pnl_dict)
        slippage_percent = 2

        result = calculate_slippage(pnl_df, slippage_percent)

        for index in range(2):
            self.assertEqual(result.iloc[index]["entry_price"], slippage(pnl_dict["entry_price"][index], "MARKET", pnl_dict["entry_transaction_type"][index], slippage_percent))
            self.assertEqual(result.iloc[index]["exit_price"], slippage(pnl_dict["exit_price"][index], "MARKET", pnl_dict["exit_transaction_type"][index], slippage_percent))
            self.assertEqual(result.iloc[index]["exit_price"] - result.iloc[index]["entry_price"], result.iloc[index]["pnl_absolute"])

    def test_calculate_brokerage(self):
        # if brokerage_percentage is not None:
        # if brokerage_generated:
        pnl_dict = {
            "entry_price": [245, 261],
            "entry_quantity": [10, 10],
            "entry_transaction_type": ["BUY", "SELL"],
            "exit_price": [465, 324],
            "exit_quantity": [10, 10],
            "exit_transaction_type": ["SELL", "BUY"]
        }
        pnl_df = pd.DataFrame(pnl_dict)
        pnl_df['pnl_absolute'] = pnl_df['exit_price'] - pnl_df['entry_price']

        brokerage_percentage = 5
        brokerage_flat_price = None
        result = calculate_brokerage(pnl_df, brokerage_percentage, brokerage_flat_price)

        for i in range(2):
            expected_brokerage = ((pnl_dict['entry_price'][i] * pnl_dict['entry_quantity'][i]) + (pnl_dict['exit_price'][i] * pnl_dict['exit_quantity'][i])) * (brokerage_percentage / 100)
            self.assertEqual(result.iloc[i]['brokerage'], expected_brokerage)
            self.assertEqual(result.iloc[i]['net_pnl'], pnl_df.iloc[i]['pnl_absolute'] - expected_brokerage)

        # elif brokerage_flat_price is not None:
        # if brokerage_generated:
        brokerage_percentage = None
        brokerage_flat_price = 50
        result = calculate_brokerage(pnl_df, brokerage_percentage, brokerage_flat_price)

        for i in range(2):
            self.assertEqual(result.iloc[i]['brokerage'], brokerage_flat_price)
            self.assertEqual(result.iloc[i]['net_pnl'], pnl_df.iloc[i]['pnl_absolute'] - brokerage_flat_price)

        # else:
        # else:
        brokerage_flat_price = None
        result = calculate_brokerage(pnl_df, brokerage_percentage, brokerage_flat_price)

        for i in range(2):
            self.assertEqual(result.iloc[i]['brokerage'], 0)
            self.assertEqual(result.iloc[i]['net_pnl'], pnl_df.iloc[i]['pnl_absolute'])

        # if brokerage_percentage is not None:
        # if brokerage_percentage is not None and brokerage_flat_price is not None:
        # if brokerage_generated:
        brokerage_flat_price = 50
        brokerage_percentage = 5
        result = calculate_brokerage(pnl_df, brokerage_percentage, brokerage_flat_price)

        for i in range(2):
            self.assertEqual(result.iloc[i]['brokerage'], brokerage_flat_price)
            self.assertEqual(result.iloc[i]['net_pnl'], pnl_df.iloc[i]['pnl_absolute'] - brokerage_flat_price)

    # @patch('pyalgotrading.utils.func.make_subplots')
    # @patch('pyalgotrading.utils.func.graph_objects.Candlestick')
    # def test_plot_candlestick_chart(self, mock_candlestick, mock_make_subplots):
    #     nrows = 5
    #     timestamps = pd.date_range(start="2024-01-01", periods=nrows, freq="D")
    #     open_prices = [random.uniform(100, 200) for _ in range(nrows)]
    #     high_prices = [price + random.uniform(0, 10) for price in open_prices]
    #     low_prices = [price - random.uniform(0, 10) for price in open_prices]
    #     close_prices = [random.uniform(100, 200) for _ in range(nrows)]
    #
    #     data = pd.DataFrame({
    #         'timestamp': timestamps,
    #         'open': open_prices,
    #         'high': high_prices,
    #         'low': low_prices,
    #         'close': close_prices
    #     })
    #     plot_type = PlotType.JAPANESE
    #     show = False
    #
    #     mock_fig = Mock()
    #     mock_make_subplots.return_value = mock_fig
    #
    #     plot_candlestick_chart(data=data, plot_type=plot_type, show=show)
    #
    #     mock_make_subplots.assert_called_once_with(rows=1, cols=1, vertical_spacing=0.5, shared_xaxes=True)


