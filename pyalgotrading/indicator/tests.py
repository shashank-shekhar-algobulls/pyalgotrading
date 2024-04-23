import unittest
from datetime import datetime
from unittest import TestCase

import pandas as pd

from pyalgotrading.indicator.vwap import VWAP


class TestVWAP(TestCase):

    def test_VWAP(self):
        data = {
            'timestamp': [datetime(2024, 4, 20, 9, 0), datetime(2024, 4, 20, 10, 0), datetime(2024, 4, 20, 11, 0)],
            'high': [100, 110, 105],
            'low': [90, 100, 95],
            'close': [95, 105, 100],
            'volume': [1000, 2000, 1500]
        }
        hist_data_df = pd.DataFrame(data)
        calculated_vwap = VWAP(hist_data_df)
        expected_vwap = pd.Series([95.000000 , 101.66666666666667, 101.11111111111111])
        self.assertTrue(calculated_vwap.equals(expected_vwap))


if __name__ == '__main__':
    unittest.main()
