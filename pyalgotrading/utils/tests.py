from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch

import pandas as pd

from pyalgotrading.constants import TradingType, PlotType
from .candlesticks.heikinashi import HeikinAshi
from .candlesticks.linebreak import Linebreak
from .candlesticks.renko import Renko
from .func import import_with_install, get_datetime_with_tz, calculate_slippage, slippage, calculate_brokerage, plot_candlestick_chart


class TestFunctions(TestCase):
    def setUp(self):
        pass

    # @patch("subprocess.check_call")
    def test_import_with_install(self):
        package_import_name = "pandas"
        result = import_with_install(package_import_name)
        self.assertEqual(result.__name__, package_import_name)

        # package_import_name = "pillow"
        # result = import_with_install(package_import_name)
        # print(result)
        # # Test for package not installed (Fix: Throwing StopIteration error)
        # with patch('builtins.__import__', side_effect=[ImportError("error message"), "mock_result"]):
        #     result = import_with_install(package_import_name, dependancies=["invalid_dependency"])
        #     self.assertEqual(result, "mock_result")
        #
        # mock_check_call.assert_called_once()

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

    @patch('plotly.subplots.make_subplots')
    @patch('plotly.graph_objects.Figure')
    @patch('builtins.print')  # Patch the 'print' function to capture its output
    def test_plot_candlestick_chart(self, mock_print, mock_figure, mock_make_subplots):
        data = {
            'timestamp': pd.date_range(start='2024-01-01', end='2024-01-05', freq='D'),
            'open': [100, 110, 120, 130, 140],
            'high': [120, 130, 140, 150, 160],
            'low': [90, 100, 110, 120, 130],
            'close': [110, 120, 130, 140, 150]
        }
        df = pd.DataFrame(data)
        # When plot_type is not an instance of {PlotType.__class__}'
        plot_type = "JAPANESE"
        plot_candlestick_chart(df, plot_type)
        mock_print.assert_called_with(f'Error: plot_type should be an instance of {PlotType.__class__}')

        # When plot_type is JAPANESE
        plot_type = PlotType.JAPANESE
        result = plot_candlestick_chart(df, plot_type)
        self.assertIsNone(result)
        mock_make_subplots.assert_called_once_with(rows=1, cols=1, vertical_spacing=0.05, shared_xaxes=True)

        # When : plot_type is LINEBREAK; hide_missing_dates is True; show is False; indicators is provided; plot_indicators_separately is True
        plot_type = PlotType.LINEBREAK
        indicators = (
            {
                'name': 'SMA',
                'data': [105, 115, 125]  # Sample SMA values
            },
            {
                'name': 'EMA',
                'data': [108, 118, 128]  # Sample EMA values
            }
        )
        result = plot_candlestick_chart(df, plot_type, hide_missing_dates=True, show=False, indicators=indicators, plot_indicators_separately=True)
        self.assertIsNone(result)
        mock_figure.assert_called_once()

        # When plot_type is RENKO
        plot_type = PlotType.RENKO
        result = plot_candlestick_chart(df, plot_type, show=False)
        self.assertIsNone(result)

        # # When plot_type is QUANDL_JAPANESE
        # plot_type = PlotType.QUANDL_JAPANESE
        # result = plot_candlestick_chart(df, plot_type, show=False)
        # print(result)
        # self.assertIsNone(result)


class TestCandlesticks(TestCase):

    def test_heikinAshi(self):
        # Mock Japanese candlesticks pattern data
        japanese_candles = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5),
            'open': [100, 110, 105, 120, 115],
            'high': [120, 130, 125, 140, 135],
            'low': [90, 100, 95, 110, 105],
            'close': [110, 120, 115, 130, 125]
        })
        heikin_ashi_data = HeikinAshi(japanese_candles)
        expected_output = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5),
            'open': [105.0, 105.0, 110.0, 110.0, 117.5],
            'high': [120.0, 130.0, 125.0, 140.0, 135.0],
            'low': [90.0, 100.0, 95.0, 110.0, 105.0],
            'close': [105.0, 115.0, 110.0, 125.0, 120.0]
        })
        pd.testing.assert_frame_equal(heikin_ashi_data, expected_output)
        self.assertTrue(heikin_ashi_data.equals(expected_output))

    def test_linebreak(self):
        # When all_greater is True
        japanese_candles = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=6),
            'open': [100, 110, 105, 120, 115, 125],
            'close': [110, 120, 115, 130, 125, 135]
        })
        linebreak_candles = Linebreak(japanese_candles)
        expected_output = pd.DataFrame({
            'close': [110, 120, 115, 130, 125, 135],
            'open': [100, 110, 105, 115, 115, 130],
            'timestamp': pd.date_range('2024-01-01', periods=6)
        })
        expected_output = expected_output.drop(index=4)
        expected_output = expected_output.reset_index(drop=True)
        self.assertTrue(linebreak_candles.equals(expected_output))

        # When all_lesser is True
        linebreak_candles = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=4),
            'close': [70, 65, 60, 55],
            'open': [100, 110, 105, 115],
        })
        linebreak_candles = Linebreak(linebreak_candles)
        expected_output = pd.DataFrame({
            'close': [70, 65, 60, 55],
            'open': [100, 110, 105, 60],
            'timestamp': pd.date_range('2024-01-01', periods=4)
        })
        self.assertTrue(linebreak_candles.equals(expected_output))

    def test_renko(self):
        # When candle['close'] > max_open_close
        japanese_candles = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=6),
            'open': [100, 110, 120, 120, 115, 125],
            'close': [110, 120, 115, 130, 125, 135]
        })
        renko_candles = Renko(japanese_candles, brick_count=5)
        expected_output = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02', '2024-01-02', '2024-01-04', '2024-01-04', '2024-01-06'],
            'open': [100, 110, 115, 120, 125, 130],
            'close': [110, 115, 120, 125, 130, 135]
        })
        expected_output['timestamp'] = pd.to_datetime(expected_output['timestamp'])
        pd.testing.assert_frame_equal(renko_candles, expected_output)
        self.assertTrue(renko_candles.equals(expected_output))

        # When : candle['close'] < min_open_close; initial_close is not None
        japanese_candles['close'] = [90, 85, 80, 75, 70, 65]  # Modify close prices to be less than min_open_close
        renko_candles = Renko(japanese_candles, brick_count=5, initial_open=15, initial_close=10)
        expected_output = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', '2024-01-06'],
            'open': [105, 95, 90, 85, 80, 75, 70],
            'close': [95, 90, 85, 80, 75, 70, 65]
        })
        expected_output['timestamp'] = pd.to_datetime(expected_output['timestamp'])
        self.assertTrue(renko_candles.equals(expected_output))
