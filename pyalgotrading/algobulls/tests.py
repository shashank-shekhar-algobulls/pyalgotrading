import inspect
import json
import os
import pprint
import unittest
from datetime import datetime as dt, timezone, timedelta, time
from io import StringIO
from json import JSONDecodeError
from unittest import TestCase
from unittest.mock import patch, Mock, MagicMock

import pandas as pd
from tabulate import tabulate

from pyalgotrading.constants import TradingType, TradingReportType, StrategyMode, CandleInterval, EXCHANGE_LOCALE_MAP
from pyalgotrading.utils.func import get_raw_response, get_datetime_with_tz
from .api import AlgoBullsAPI
from .connection import AlgoBullsConnection
from .exceptions import AlgoBullsAPIBaseException, AlgoBullsAPIUnauthorizedErrorException, AlgoBullsAPIInsufficientBalanceErrorException, AlgoBullsAPIResourceNotFoundErrorException, AlgoBullsAPIBadRequestException, \
    AlgoBullsAPIInternalServerErrorException, AlgoBullsAPIForbiddenErrorException, AlgoBullsAPIGatewayTimeoutErrorException


class TestAlgoBullsAPI(TestCase):
    def setUp(self):
        self.connection = AlgoBullsConnection()
        self.api = AlgoBullsAPI(self.connection)

    def test___convert(self):
        camel_case_key = "TestKey"
        snake_case_key = "test_key"
        value = "TestValue"
        _dict = {camel_case_key: value}
        result = self.api._AlgoBullsAPI__convert(_dict)
        self.assertEqual(result, {snake_case_key: value})

    def test_set_access_token(self):
        access_token = "randomtoken123"
        self.api.set_access_token(access_token)
        self.assertIsInstance(self.api.headers, dict)
        self.assertEqual(self.api.headers["Authorization"], access_token)

    @patch("pyalgotrading.algobulls.api.requests.request")
    def test__send_request(self, mock_request):
        """
        Tests for _send_request method
        """

        '''
        Testcase for blocks:
            - if r.status_code == 200:
                - try:
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        method = "get"
        endpoint = 'v2/portfolio/strategy'
        base_url = self.api.SERVER_ENDPOINT
        params = None
        json_data = None
        requires_authorization = True
        raise_exception_unknown_status_code = True

        result = self.api._send_request(
            method=method,
            endpoint=endpoint,
            base_url=base_url,
            params=params,
            json_data=json_data,
            requires_authorization=requires_authorization,
            raise_exception_unknown_status_code=raise_exception_unknown_status_code
        )

        headers = self.api.headers
        url = f'{base_url}{endpoint}'
        mock_request.assert_called_once_with(method=method, headers=headers, url=url, params=params, json=json_data)
        self.assertEqual(result, mock_response.json.return_value)

        '''
        Testcase for blocks:
            - if r.status_code == 200:
                - except JSONDecodeError:
        '''
        mock_request.reset_mock()
        mock_response.reset_mock()

        mock_response.json.side_effect = JSONDecodeError("JSONDecodeError Message", "", 0)
        mock_response.raw.decode_content = False
        mock_response.content = "{'result': 'success'}"
        mock_response.raw.data = "raw_data"

        result = self.api._send_request(
            method=method,
            endpoint=endpoint,
            base_url=base_url,
            params=params,
            json_data=json_data,
            requires_authorization=requires_authorization,
            raise_exception_unknown_status_code=raise_exception_unknown_status_code
        )
        self.assertEqual(result, {'response': get_raw_response(mock_response)})
        self.assertTrue(mock_response.raw.decode_content)

        '''
        Testcase for blocks:
            - elif r.status_code == 400:
            - elif r.status_code == 401:
            - elif r.status_code == 402:
            - elif r.status_code == 403:
            - elif r.status_code == 404:
            - elif r.status_code == 500:
            - elif r.status_code == 504:
            - else:
                - if raise_exception_unknown_status_code:
        '''
        status_codes_and_exceptions = [
            (400, AlgoBullsAPIBadRequestException),
            (401, AlgoBullsAPIUnauthorizedErrorException),
            (402, AlgoBullsAPIInsufficientBalanceErrorException),
            (403, AlgoBullsAPIForbiddenErrorException),
            (404, AlgoBullsAPIResourceNotFoundErrorException),
            (500, AlgoBullsAPIInternalServerErrorException),
            (504, AlgoBullsAPIGatewayTimeoutErrorException),
            (502, AlgoBullsAPIBaseException)  # 502 will be handled in else block
        ]

        for status_code, exception in status_codes_and_exceptions:
            mock_request.reset_mock()
            mock_response.reset_mock()

            mock_response.status_code = status_code
            mock_response.raw.decode_content = False

            with self.assertRaises(exception) as context:
                self.api._send_request(
                    method=method,
                    endpoint=endpoint,
                    base_url=base_url,
                    params=params,
                    json_data=json_data,
                    requires_authorization=requires_authorization,
                    raise_exception_unknown_status_code=raise_exception_unknown_status_code
                )

            raised_exception = context.exception
            self.assertEqual(raised_exception.method, method)
            self.assertEqual(raised_exception.url, url)
            self.assertEqual(raised_exception.response, get_raw_response(mock_response))

            self.assertTrue(mock_response.raw.decode_content)

        '''
        Testcase for blocks:
            - else:
                - else:
        '''
        mock_request.reset_mock()
        mock_response.reset_mock()

        mock_response.status_code = 502
        mock_response.raw.decode_content = False
        mock_response.json.side_effect = None

        raise_exception_unknown_status_code = False

        result = self.api._send_request(
            method=method,
            endpoint=endpoint,
            base_url=base_url,
            params=params,
            json_data=json_data,
            requires_authorization=requires_authorization,
            raise_exception_unknown_status_code=raise_exception_unknown_status_code
        )

        self.assertEqual(result, mock_response.json.return_value)
        self.assertFalse(mock_response.raw.decode_content)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test___fetch_key(self, mock__send_request):
        """
        Tests for __fetch_key method
        """
        '''
        Testcase for block: if trading_type is TradingType.REALTRADING:
        '''
        key = "TestKey"
        mock__send_request.return_value = {"result": "success", "key": key}
        strategy_code = "TestStrategyCode"
        trading_type = TradingType.REALTRADING

        result = self.api._AlgoBullsAPI__fetch_key(strategy_code, trading_type)

        method = 'post'
        endpoint = f'v2/portfolio/strategy'
        json_data = {'strategyId': strategy_code, 'tradingType': trading_type.value}

        mock__send_request.assert_called_once_with(method=method, endpoint=endpoint, json_data=json_data)
        self.assertEqual(result, key)

        '''
        Testcase for block: elif trading_type is TradingType.PAPERTRADING:
        '''
        mock__send_request.reset_mock()
        trading_type = TradingType.PAPERTRADING

        result = self.api._AlgoBullsAPI__fetch_key(strategy_code, trading_type)
        method = 'put'
        json_data['tradingType'] = trading_type.value
        mock__send_request.assert_called_once_with(method=method, endpoint=endpoint, json_data=json_data)
        self.assertEqual(result, key)

        '''
        Testcase for block: elif trading_type is TradingType.BACKTESTING:
        '''
        mock__send_request.reset_mock()
        trading_type = TradingType.BACKTESTING

        result = self.api._AlgoBullsAPI__fetch_key(strategy_code, trading_type)
        method = 'patch'
        json_data['tradingType'] = trading_type.value
        mock__send_request.assert_called_once_with(method=method, endpoint=endpoint, json_data=json_data)
        self.assertEqual(result, key)

        '''
        Testcase for else block
        '''
        mock__send_request.reset_mock()
        trading_type = TradingReportType.ORDER_HISTORY

        with self.assertRaises(NotImplementedError):
            self.api._AlgoBullsAPI__fetch_key(strategy_code, trading_type)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._AlgoBullsAPI__fetch_key")
    def test___get_key(self, mock___fetch_key):
        """
        Test for __get_key method
        """
        '''
        Testcase for blocks:
            - if trading_type is TradingType.BACKTESTING:
                - if self.__key_backtesting.get(strategy_code) is None:
        '''
        backtesting_key = "BacktestingKey"
        mock___fetch_key.return_value = backtesting_key
        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING

        result = self.api._AlgoBullsAPI__get_key(strategy_code, trading_type)

        mock___fetch_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        self.assertEqual(result, backtesting_key)

        '''
        Testcase for blocks:
            - elif trading_type is TradingType.PAPERTRADING:
                - if self.__key_papertrading.get(strategy_code) is None:
        '''
        mock___fetch_key.reset_mock()

        papertrading_key = "PapertradingKey"
        mock___fetch_key.return_value = papertrading_key
        trading_type = TradingType.PAPERTRADING

        result = self.api._AlgoBullsAPI__get_key(strategy_code, trading_type)

        mock___fetch_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        self.assertEqual(result, papertrading_key)

        '''
        Testcase for blocks:
            - elif trading_type is TradingType.REALTRADING:
                - if self.__key_realtrading.get(strategy_code) is None:
        '''
        mock___fetch_key.reset_mock()

        realtrading_key = "RealtradingKey"
        mock___fetch_key.return_value = realtrading_key
        trading_type = TradingType.REALTRADING

        result = self.api._AlgoBullsAPI__get_key(strategy_code, trading_type)

        mock___fetch_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        self.assertEqual(result, realtrading_key)

        '''
        Testcase for else block
        '''
        mock___fetch_key.reset_mock()
        trading_type = TradingReportType.ORDER_HISTORY
        with self.assertRaises(NotImplementedError):
            self.api._AlgoBullsAPI__get_key(strategy_code, trading_type)

    @patch("sys.stdout", new_callable=StringIO)
    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_create_strategy(self, mock__send_request, mock_stdout):
        """
        Tests for create_strategy method
        """

        '''
        Testcase for try block
        '''
        mock_response = Mock()
        mock__send_request.return_value = mock_response

        strategy_name = "TestStrategyName"
        strategy_details = "TestStrategyDetails"
        abc_version = "3.1.0"
        json_data = {'strategyName': strategy_name, 'strategyDetails': strategy_details, 'abcVersion': abc_version}
        endpoint = 'v3/build/python/user/strategy/code'
        method = 'post'
        base_url = self.api.SERVER_ENDPOINT
        url = f'{base_url}{endpoint}'
        status_code = 200

        result = self.api.create_strategy(strategy_name, strategy_details, abc_version)
        mock__send_request.assert_called_once_with(endpoint=endpoint, method=method, json_data=json_data)
        self.assertEqual(result, mock_response)

        '''
        Testcase for except block: AlgoBullsAPIForbiddenErrorException
        '''
        mock__send_request.reset_mock()
        mock_response.reset_mock()

        mock__send_request.side_effect = AlgoBullsAPIForbiddenErrorException(method=method, url=url, response=mock_response, status_code=status_code)
        self.api.create_strategy(strategy_name, strategy_details, abc_version)
        self.assertIn(f'{mock__send_request.side_effect.get_error_type()}: {mock__send_request.side_effect.response}', mock_stdout.getvalue())

        '''
        Testcase for except block: AlgoBullsAPIInsufficientBalanceErrorException
        '''
        mock__send_request.reset_mock()
        mock_response.reset_mock()

        mock__send_request.side_effect = AlgoBullsAPIInsufficientBalanceErrorException(method=method, url=url, response=mock_response, status_code=status_code)
        self.api.create_strategy(strategy_name, strategy_details, abc_version)
        self.assertIn(f'{mock__send_request.side_effect.get_error_type()}: {mock__send_request.side_effect.response}', mock_stdout.getvalue())

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_update_strategy(self, mock__send_request):
        """
        Test for update_strategy method
        """
        mock__send_request.return_value = {"mock result": "mock success"}

        strategy_code = "TestStrategyCode"
        strategy_name = "TestStrategyName"
        strategy_details = "TestStrategyDetails"
        abc_version = "3.1.0"
        json_data = {'strategyId': strategy_code, 'strategyName': strategy_name, 'strategyDetails': strategy_details, 'abcVersion': abc_version}
        endpoint = f'v3/build/python/user/strategy/code'
        method = 'put'

        result = self.api.update_strategy(strategy_code, strategy_name, strategy_details, abc_version)
        mock__send_request.assert_called_once_with(endpoint=endpoint, method=method, json_data=json_data)
        self.assertEqual(result, mock__send_request.return_value)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_get_all_strategies(self, mock__send_request):
        """
        Test for get_all_strategies method
        """
        mock__send_request.return_value = {"mock result": "mock success"}
        endpoint = f'v3/build/python/user/strategy/code'
        method = 'options'
        result = self.api.get_all_strategies()
        mock__send_request.asssert_called_once_with(endpoint=endpoint, method=method)
        self.assertEqual(result, mock__send_request.return_value)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_get_strategy_details(self, mock__send_request):
        """
        Test for get_strategy_details method
        """
        mock__send_request.return_value = {"mock result": "mock success"}
        params = {}
        strategy_code = "TestStrategyCode"
        endpoint = f'v3/build/python/user/strategy/code/{strategy_code}'
        result = self.api.get_strategy_details(strategy_code)
        mock__send_request.asssert_called_once_with(endpoint=endpoint, params=params)
        self.assertEqual(result, mock__send_request.return_value)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_search_instrument(self, mock__send_request):
        """
        Test for search_instrument method
        """
        mock__send_request.return_value = {"mock result": "mock success"}
        tradingsymbol = "TestTradingSymbol"
        exchange = "TestExchange"
        requires_authorization = False
        params = {'search': tradingsymbol, 'exchange': exchange}
        endpoint = f'v4/portfolio/searchInstrument'
        result = self.api.search_instrument(tradingsymbol, exchange)
        mock__send_request.asssert_called_once_with(endpoint=endpoint, params=params, requires_authorization=requires_authorization)
        self.assertEqual(result, mock__send_request.return_value)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_delete_previous_trades(self, mock__send_request):
        """
        Test for delete_previous_trades method
        """
        mock__send_request.return_value = {"mock result": "mock success"}
        strategy = "TestStrategy"
        method = "delete"
        endpoint = f'v3/build/python/user/strategy/deleteAll?strategyId={strategy}'
        result = self.api.delete_previous_trades(strategy)
        mock__send_request.asssert_called_once_with(method=method, endpoint=endpoint)
        self.assertEqual(result, mock__send_request.return_value)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._AlgoBullsAPI__get_key")
    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_set_strategy_config(self, mock__send_request, mock___get_key):
        """
        Test for set_strategy_config method
        """
        key = "TestKey"
        mock__send_request.return_value = {"mock result": "mock success"}
        mock___get_key.return_value = key
        strategy_code = "TestStrategyCode"
        strategy_config = {"test_key": "test_value"}
        trading_type = TradingType.BACKTESTING
        method = "post"
        endpoint = f'v4/portfolio/tweak/{key}?isPythonBuild=true'
        result = self.api.set_strategy_config(strategy_code, strategy_config, trading_type)
        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        mock__send_request.asssert_called_once_with(method=method, endpoint=endpoint, json_data=strategy_config)
        self.assertEqual(result, (key, mock__send_request.return_value))

    @patch("sys.stdout", new_callable=StringIO)
    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._AlgoBullsAPI__get_key")
    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_start_strategy_algotrading(self, mock__send_request, mock___get_key, mock_stdout):
        """
        Test for start_strategy_algotrading method
        """
        '''
        Testcase for blocks:
            - try:
                - if trading_type in [TradingType.PAPERTRADING, TradingType.BACKTESTING]:
        '''
        key = "TestKey"
        mock__send_request.return_value = {"mock result": "mock success"}
        mock___get_key.return_value = key

        strategy_code = "TestStrategyCode"
        start_timestamp = dt.now(timezone.utc) - timedelta(days=3)
        end_timestamp = dt.now(timezone.utc)
        trading_type = TradingType.BACKTESTING
        lots = 10
        location = "India"
        initial_funds_virtual = 1e9
        broker_details = None

        result = self.api.start_strategy_algotrading(strategy_code, start_timestamp, end_timestamp, trading_type, lots, location, initial_funds_virtual, broker_details)

        endpoint = f'v5/portfolio/strategies?isPythonBuild=true&isLive=false&location={location}'
        method = "patch"
        execute_config = {
            "backDataDate": [start_timestamp.astimezone(timezone.utc).replace(tzinfo=None).isoformat(), end_timestamp.astimezone(timezone.utc).replace(tzinfo=None).isoformat()],
            'isLiveDataTestMode': False,
            'customizationsQuantity': lots,
            'brokingDetails': broker_details,
            'mode': trading_type.name,
            'initialFundsVirtual': initial_funds_virtual
        }
        params = None
        json_data = {'method': 'update', 'newVal': 1, 'key': key, 'record': {'status': 0, 'lots': lots, 'executeConfig': execute_config}, 'dataIndex': 'executeConfig'}

        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        mock__send_request.assert_called_once_with(method=method, endpoint=endpoint, json_data=json_data, params=params)
        self.assertEqual(result, mock__send_request.return_value)

        '''
        Testcase for blocks:
            - try:
                - elif trading_type is TradingType.REALTRADING:
        '''
        mock__send_request.reset_mock()
        mock___get_key.reset_mock()

        trading_type = TradingType.REALTRADING

        result = self.api.start_strategy_algotrading(strategy_code, start_timestamp, end_timestamp, trading_type, lots, location, initial_funds_virtual, broker_details)

        endpoint = f'v5/portfolio/strategies?isPythonBuild=true&isLive=true&location={location}'
        execute_config = {
            "liveDataTime": [start_timestamp.astimezone(timezone.utc).replace(tzinfo=None).isoformat(), end_timestamp.astimezone(timezone.utc).replace(tzinfo=None).isoformat()],
            'isLiveDataTestMode': True,
            'customizationsQuantity': lots,
            'brokingDetails': broker_details,
            'mode': trading_type.name
        }
        json_data = {'method': 'update', 'newVal': 1, 'key': key, 'record': {'status': 0, 'lots': lots, 'executeConfig': execute_config}, 'dataIndex': 'executeConfig'}

        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        mock__send_request.assert_called_once_with(method=method, endpoint=endpoint, json_data=json_data, params=params)
        self.assertEqual(result, mock__send_request.return_value)

        '''
        Testcase for except block
        '''
        mock__send_request.reset_mock()
        mock___get_key.reset_mock()

        base_url = self.api.SERVER_ENDPOINT
        url = f'{base_url}{endpoint}'
        mock_response = Mock()
        status_code = 200

        mock__send_request.side_effect = AlgoBullsAPIForbiddenErrorException(method=method, url=url, response=mock_response, status_code=status_code)
        result = self.api.start_strategy_algotrading(strategy_code, start_timestamp, end_timestamp, trading_type, lots, location, initial_funds_virtual, broker_details)
        self.assertIn(f'{mock__send_request.side_effect.get_error_type()}: {mock__send_request.side_effect.response}', mock_stdout.getvalue())
        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._AlgoBullsAPI__get_key")
    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_stop_strategy_algotrading(self, mock__send_request, mock___get_key):
        """
        Test for stop_strategy_algotrading method
        """
        '''
        Testcase for try block
        '''
        key = "TestKey"
        mock__send_request.return_value = {"mock result": "mock success"}
        mock___get_key.return_value = key

        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING

        result = self.api.stop_strategy_algotrading(strategy_code, trading_type)

        method = 'patch'
        endpoint = 'v5/portfolio/strategies'
        json_data = {'method': 'update', 'newVal': 0, 'key': key, 'record': {'status': 2}, 'dataIndex': 'executeConfig'}
        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        mock__send_request.assert_called_once_with(method=method, endpoint=endpoint, json_data=json_data)
        self.assertEqual(result, mock__send_request.return_value)

        '''
        Testcase for except block
        '''
        mock__send_request.reset_mock()
        mock___get_key.reset_mock()

        base_url = self.api.SERVER_ENDPOINT
        url = f'{base_url}{endpoint}'
        mock_response = Mock()
        status_code = 200
        mock__send_request.side_effect = AlgoBullsAPIForbiddenErrorException(method=method, url=url, response=mock_response, status_code=status_code)

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            self.api.stop_strategy_algotrading(strategy_code, trading_type)

            self.assertIn(f'{mock__send_request.side_effect.get_error_type()}: {mock_response}', mock_stdout.getvalue())
            mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._AlgoBullsAPI__get_key")
    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_get_job_status(self, mock__send_request, mock___get_key):
        """
        Test for get_job_status method
        """
        key = "TestKey"
        mock__send_request.return_value = {"mock result": "mock success"}
        mock___get_key.return_value = key

        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING

        result = self.api.get_job_status(strategy_code, trading_type)

        params = {'key': key}
        endpoint = f'v2/user/strategy/status'
        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        mock__send_request.assert_called_once_with(endpoint=endpoint, params=params)
        self.assertEqual(result, mock__send_request.return_value)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._AlgoBullsAPI__get_key")
    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_get_logs(self, mock__send_request, mock___get_key):
        """
        Test for get_logs method
        """
        key = "TestKey"
        mock__send_request.return_value = {"mock result": "mock success"}
        mock___get_key.return_value = key

        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING
        initial_next_token = "TestInitialNextToken"

        result = self.api.get_logs(strategy_code, trading_type, initial_next_token)

        method = 'post'
        endpoint = 'v4/user/strategy/logs'
        json_data = {'key': key, 'nextForwardToken': initial_next_token, 'limit': self.api.page_size, 'direction': 'forward', 'type': 'userLogs'}
        params = {'isPythonBuild': True, 'isLive': trading_type == TradingType.REALTRADING}
        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        mock__send_request.assert_called_once_with(method=method, endpoint=endpoint, json_data=json_data, params=params)
        self.assertEqual(result, mock__send_request.return_value)

    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._AlgoBullsAPI__get_key")
    @patch("pyalgotrading.algobulls.api.AlgoBullsAPI._send_request")
    def test_get_reports(self, mock__send_request, mock___get_key):
        """
        Test for get_reports method
        """
        '''
        Test for if block
        '''
        key = "TestKey"
        mock__send_request.return_value = {"mock result": "mock success"}
        mock___get_key.return_value = key

        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING
        report_type = TradingReportType.PNL_TABLE
        country = "India"
        current_page = 1

        result = self.api.get_reports(strategy_code, trading_type, report_type, country, current_page)

        endpoint = f'v4/book/pl/data'
        _filter = json.dumps({"tradingType": trading_type.value})
        params = {'pageSize': 0, 'isPythonBuild': "true", 'strategyId': strategy_code, 'isLive': trading_type is TradingType.REALTRADING, 'country': country, 'filters': _filter}

        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        mock__send_request.assert_called_once_with(endpoint=endpoint, params=params)
        self.assertEqual(result, mock__send_request.return_value)

        '''
        Test for elif block
        '''
        mock__send_request.reset_mock()
        mock___get_key.reset_mock()

        report_type = TradingReportType.ORDER_HISTORY

        result = self.api.get_reports(strategy_code, trading_type, report_type, country, current_page)

        endpoint = 'v5/build/python/user/order/charts'
        params = {'strategyId': strategy_code, 'country': country, 'currentPage': current_page, 'pageSize': self.api.page_size, 'isLive': trading_type is TradingType.REALTRADING}
        mock___get_key.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        mock__send_request.assert_called_once_with(endpoint=endpoint, params=params)
        self.assertEqual(result, mock__send_request.return_value)

        '''
        Test for else block
        '''
        mock__send_request.reset_mock()
        mock___get_key.reset_mock()

        report_type = TradingReportType.STATS_TABLE
        with self.assertRaises(NotImplementedError):
            self.api.get_reports(strategy_code, trading_type, report_type, country, current_page)


class TestAlgoBullsConnection(TestCase):
    def setUp(self):
        self.connection = AlgoBullsConnection()
        self.strategy_code = "TestStrategyCode"

    @patch('builtins.print')
    def test_get_authorization_url(self, mock_print):
        self.connection.get_authorization_url()
        mock_print.assert_called_with(f'Please login to this URL with your AlgoBulls credentials and get your developer access token: https://app.algobulls.com/user/login')

    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_all_strategies")
    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.set_access_token")
    def test_set_access_token(self, mock_set_access_token, mock_get_all_strategies):
        """
        Test for set_access_token method
        """
        '''
        Testcase for try block
        '''
        access_token = "TestAccessToken"
        validate_token = True
        self.connection.set_access_token(access_token, validate_token)

        mock_set_access_token.assert_called_once_with(access_token)
        mock_get_all_strategies.assert_called_once()
        '''
        Testcase for except block
        '''
        mock_set_access_token.reset_mock()

        mock_get_all_strategies.side_effect = AlgoBullsAPIUnauthorizedErrorException("get", AlgoBullsAPI.SERVER_ENDPOINT, Mock(), 200)
        self.connection.set_access_token(access_token, validate_token)

    def test_create_strategy(self):
        """
        Test for create_strategy method

        """
        '''
        Testcase: strategy is not a subclass of StrategyBase
        '''
        from pyalgotrading.strategy.strategy_options_base_v2 import IntrumentsMappingManager
        from pyalgotrading.strategy.strategy_base import StrategyBase
        from pyalgotrading.constants import AlgoBullsEngineVersion
        strategy = IntrumentsMappingManager
        overwrite = False
        strategy_code = None
        abc_version = None
        with self.assertRaises(AssertionError) as context:
            self.connection.create_strategy(strategy, overwrite, strategy_code, abc_version)
        self.assertEqual(str(context.exception), f'strategy should be a subclass of class StrategyBase. Got class of type: type{strategy}')

        '''
        Testcase for blocks:
            - if abc_version is None:
                - else:
            - if overwrite is False:
        '''
        strategy = StrategyBase
        strategy.name = "TestStrategyName"

        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.create_strategy") as mock_create_strategy:
            response = {"result": "success"}
            mock_create_strategy.return_value = response
            result = self.connection.create_strategy(strategy, overwrite, strategy_code, abc_version)
            mock_create_strategy.assert_called_once_with(strategy_name=strategy.name, strategy_details=inspect.getsource(strategy), abc_version=AlgoBullsEngineVersion.VERSION_3_3_0.value)
            self.assertEqual(result, response)

        '''
        Testcase for blocks:
            - if abc_version is None:
                - if isinstance(versions_supported, list):
            - if overwrite is False:
        '''
        strategy = StrategyBase
        strategy.name = "TestStrategyName"
        strategy.versions_supported = lambda: [AlgoBullsEngineVersion.VERSION_3_3_0]

        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.create_strategy") as mock_create_strategy:
            response = {"result": "success"}
            mock_create_strategy.return_value = response
            result = self.connection.create_strategy(strategy, overwrite, strategy_code, abc_version)
            mock_create_strategy.assert_called_once_with(strategy_name=strategy.name, strategy_details=inspect.getsource(strategy), abc_version=AlgoBullsEngineVersion.VERSION_3_3_0.value)
            self.assertEqual(result, response)

        '''
        Testcase for blocks:
            - else:
            - if overwrite is False:
        '''
        abc_version = AlgoBullsEngineVersion.VERSION_3_3_0

        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.create_strategy") as mock_create_strategy:
            response = {"result": "success"}
            mock_create_strategy.return_value = response
            result = self.connection.create_strategy(strategy, overwrite, strategy_code, abc_version)
            mock_create_strategy.assert_called_once_with(strategy_name=strategy.name, strategy_details=inspect.getsource(strategy), abc_version=AlgoBullsEngineVersion.VERSION_3_3_0.value)
            self.assertEqual(result, response)

        '''
        Testcase for blocks:
            - else:
            - else:
                - if strategy_code:
        '''
        overwrite = True
        strategy_code = self.strategy_code

        result = self.connection.create_strategy(strategy, overwrite, strategy_code, abc_version)
        self.assertIsNone(result)

        '''
        Testcase for blocks:
            - else:
            - else:
                - else:
                    - try:
        '''
        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_all_strategies") as mock_get_all_strategies:
            strategy_code = self.strategy_code
            strategy_name = "TestStrategyName"
            col1, val1, col2, val2 = "strategyCode", strategy_code, "strategyName", strategy_name
            get_all_strategies_response = {"data": [{col1: val1, col2: val2}]}
            mock_get_all_strategies.return_value = get_all_strategies_response
            with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.update_strategy") as mock_update_strategy:
                update_strategy_response = {"result": "success"}
                mock_update_strategy.return_value = update_strategy_response
                result = self.connection.create_strategy(strategy, overwrite, None, abc_version)
                mock_update_strategy.assert_called_once_with(strategy_code=strategy_code, strategy_name=strategy_name, strategy_details=inspect.getsource(strategy), abc_version=abc_version.value)
                self.assertEqual(result, update_strategy_response)
            mock_get_all_strategies.assert_called_once()

        '''
        Testcase for blocks:
            - else:
            - else:
                - else:
                    - except KeyError:
        '''
        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_all_strategies") as mock_get_all_strategies:
            strategy_code = self.strategy_code
            strategy_name = "TestStrategyName"
            col1, val1, col2, val2 = "invalidStrategyCode", strategy_code, "strategyName", strategy_name
            get_all_strategies_response = {"data": [{col1: val1, col2: val2}]}
            mock_get_all_strategies.return_value = get_all_strategies_response
            with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.create_strategy") as mock_create_strategy:
                create_strategy_response = {"result": "success"}
                mock_create_strategy.return_value = create_strategy_response
                result = self.connection.create_strategy(strategy, overwrite, None, abc_version)
                mock_create_strategy.assert_called_once_with(strategy_name=strategy_name, strategy_details=inspect.getsource(strategy), abc_version=abc_version.value)
                self.assertEqual(result, create_strategy_response)
            mock_get_all_strategies.assert_called_once()

    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_all_strategies")
    def test_get_all_strategies(self, mock_get_all_strategies):
        """
        Test for get_all_strategies method
        """
        '''
        Test for if block
        '''
        col1, val1, col2, val2 = "column1", "value1", "column2", "value2"
        response = {"data": [{col1: val1, col2: val2}]}
        mock_get_all_strategies.return_value = response

        result = self.connection.get_all_strategies()
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.loc[0, col1], val1)
        self.assertEqual(result.loc[0, col2], val2)

        '''
        Test for else block
        '''
        mock_get_all_strategies.reset_mock()
        response["data"] = json.dumps(response["data"])
        mock_get_all_strategies.return_value = response
        result = self.connection.get_all_strategies()
        self.assertIsInstance(result["data"], str)
        self.assertEqual(result, response)

    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_all_strategies")
    def test_get_strategy_name(self, mock_get_all_strategies):
        """
        Test for get_strategy_name method
        """
        '''
        Testcase for try block
        '''
        strategy_name = "TestStrategyName"
        col1, val1, col2, val2 = "strategyCode", self.strategy_code, "strategyName", strategy_name
        response = {"data": [{col1: val1, col2: val2}]}
        mock_get_all_strategies.return_value = response

        result = self.connection.get_strategy_name(self.strategy_code)
        self.assertEqual(result, strategy_name)

        '''
        Testcase for except block
        '''
        strategy_name = "TestStrategyName"
        col1, val1, col2, val2 = "InvalidColumnName", self.strategy_code, "strategyName", strategy_name
        response = {"data": [{col1: val1, col2: val2}]}
        mock_get_all_strategies.return_value = response

        result = self.connection.get_strategy_name(self.strategy_code)
        self.assertIsNone(result)

    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_strategy_details")
    def test_get_strategy_details(self, mock_get_strategy_details):
        """
        Test for get_strategy_details method
        """
        '''
        Testcase: strategy_code is not instance of str
        '''
        strategy_code = 123
        with self.assertRaises(AssertionError) as context:
            self.connection.get_strategy_details(strategy_code)
        self.assertEqual(str(context.exception), f'Argument "strategy_code" should be a string')

        '''
        Testcase for try block
        '''
        strategy_code = self.strategy_code
        strategy_name = "TestStrategyName"
        col1, val1, col2, val2 = "strategyCode", strategy_code, "strategyName", strategy_name
        response = {"data": [{col1: val1, col2: val2}]}
        mock_get_strategy_details.return_value = response

        result = self.connection.get_strategy_details(strategy_code)
        mock_get_strategy_details.assert_called_once_with(strategy_code)
        self.assertEqual(result, response["data"])

        '''
        Testcase for except block
        '''
        mock_get_strategy_details.side_effect = AlgoBullsAPIBadRequestException("get", AlgoBullsAPI.SERVER_ENDPOINT, Mock(), 200)

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            self.connection.get_strategy_details(strategy_code)
            self.assertIn(f'ERROR: No strategy found with ID: {strategy_code}', mock_stdout.getvalue())

    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.search_instrument")
    def test_search_instrument(self, mock_search_instrument):
        """
        Test for search_instrument method
        """
        '''
        Testcase: instrument is not instance of str
        '''
        instrument = 123
        with self.assertRaises(AssertionError) as context:
            self.connection.search_instrument(instrument)
        self.assertEqual(str(context.exception), f'Argument "instrument" should be a string')

        '''
        Testcase: instrument is an instance of str
        '''
        instrument = "TestInstrument"
        exchange = 'NSE'
        col1, val1, col2, val2 = "column1", "value1", "column2", "value2"
        response = {"data": [{col1: val1, col2: val2}]}
        mock_search_instrument.return_value = response

        result = self.connection.search_instrument(instrument)
        mock_search_instrument.assert_called_once_with(instrument, exchange=exchange)
        self.assertEqual(result, response["data"])

    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.delete_previous_trades")
    def test_delete_previous_trades(self, mock_delete_previous_trades):
        """
        Test for delete_previous_trades method
        """
        '''
        Testcase for try block
        '''
        strategy = "TestStrategy"
        response = {"message": "success"}
        mock_delete_previous_trades.return_value = response

        result = self.connection.delete_previous_trades(strategy)
        mock_delete_previous_trades.assert_called_once_with(strategy)
        self.assertEqual(result, response)

        '''
        Testcase for except block
        '''
        ex = AlgoBullsAPIGatewayTimeoutErrorException("get", AlgoBullsAPI.SERVER_ENDPOINT, Mock(), 200)
        mock_delete_previous_trades.side_effect = ex

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            result = self.connection.delete_previous_trades(strategy)
            for _ in range(30):
                self.assertIn(f'Deleting previous trades... in process... (attempt {_})\n{ex}', mock_stdout.getvalue())
            self.assertEqual(result, {})

    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_job_status")
    def test_get_job_status(self, mock_get_job_status):
        """
        Test for get_job_status method
        """
        '''
        Testcase: strategy_code is not instance of str
        '''
        strategy_code = 123
        trading_type = TradingType.BACKTESTING

        with self.assertRaises(AssertionError) as context:
            self.connection.get_job_status(strategy_code, trading_type)
        self.assertEqual(str(context.exception), f'Argument "strategy_code" should be a string')

        '''
        Testcase: trading_type is not instance of TradingType
        '''
        strategy_code = "TestStrategyCode"
        trading_type = TradingReportType.ORDER_HISTORY

        with self.assertRaises(AssertionError) as context:
            self.connection.get_job_status(strategy_code, trading_type)
        self.assertEqual(str(context.exception), f'Argument "trading_type" should be an enum of type {TradingType.__name__}')

        '''
        Testcase
        '''
        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING
        response = {"message": "success"}
        mock_get_job_status.return_value = response

        result = self.connection.get_job_status(strategy_code, trading_type)

        mock_get_job_status.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)
        self.assertEqual(result, response)

    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.stop_strategy_algotrading")
    def test_stop_job(self, mock_stop_strategy_algotrading):
        """
        Test for stop_job method
        """
        '''
        Testcase: strategy_code is not instance of str
        '''
        strategy_code = 123
        trading_type = TradingType.BACKTESTING

        with self.assertRaises(AssertionError) as context:
            self.connection.stop_job(strategy_code, trading_type)
        self.assertEqual(str(context.exception), f'Argument "strategy_code" should be a string')

        '''
        Testcase: trading_type is not instance of TradingType
        '''
        strategy_code = "TestStrategyCode"
        trading_type = TradingReportType.ORDER_HISTORY

        with self.assertRaises(AssertionError) as context:
            self.connection.stop_job(strategy_code, trading_type)
        self.assertEqual(str(context.exception), f'Argument "trading_type" should be an enum of type {TradingType.__name__}')

        '''
        Testcase
        '''
        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING
        self.connection.stop_job(strategy_code, trading_type)
        mock_stop_strategy_algotrading.assert_called_once_with(strategy_code=strategy_code, trading_type=trading_type)

    def test_get_logs(self):
        """
        Test for get_logs method
        """
        '''
        Testcase: strategy_code is not instance of str
        '''
        strategy_code = 123
        trading_type = TradingType.BACKTESTING

        with self.assertRaises(AssertionError) as context:
            self.connection.get_logs(strategy_code, trading_type)
        self.assertEqual(str(context.exception), f'Argument "strategy_code" should be a string')

        '''
        Testcase: trading_type is not instance of TradingType
        '''
        strategy_code = "TestStrategyCode"
        trading_type = TradingReportType.ORDER_HISTORY

        with self.assertRaises(AssertionError) as context:
            self.connection.get_logs(strategy_code, trading_type)
        self.assertEqual(str(context.exception), f'Argument "trading_type" should be an enum of type {TradingType.__name__}')

        '''
        Testcase for blocks:
            - if trading_type is not TradingType.BACKTESTING:
                - except AttributeError:

            - if display_progress_bar:
                - if start_timestamp_map.get(trading_type) and end_timestamp_map.get(trading_type):

            - while True: (FIRST Iteration)
                - if status is None or status == ExecutionStatus.STARTING.value:
                    - if status == ExecutionStatus.STARTING.value:

            - while True: (SECOND Iteration)
                - if status is None or status == ExecutionStatus.STARTING.value:

            - while True: (THIRD Iteration)
                - if display_progress_bar:
                    - if tqdm_progress_bar is None and status == ExecutionStatus.STARTED.value:
                - for i in range(5): (i = 0)
                    - try:
                        - if logs:
                - else:
                    - if type(logs) is list and initial_next_token:
                    - if print_live_logs:
                    - if display_progress_bar:
                        - for log in logs[::-1]: (FIRST Iteration)
                            - except Exception as ex:
                        - for log in logs[::-1]: (SECOND Iteration)
                            - try:
                                - if tqdm_progress_bar is not None and _[0] in ['BT', 'PT', 'RT']:
                    - else:

            - while True: (FOURTH Iteration)
                - if display_progress_bar:
                - for i in range(5): (i = 0)
                    - except AlgoBullsAPIGatewayTimeoutErrorException:
                - for i in range(5): (i = 1)
                    - try:
                - for i in range(5): (i = 2)
                    - try:
                - for i in range(5): (i = 3)
                    - try:
                - for i in range(5): (i = 4)
                    - try:
                - if not logs:
                    - if status in [ExecutionStatus.STOPPED.value, ExecutionStatus.STOPPING.value]:
                        - if display_progress_bar:
                            - if tqdm_progress_bar is not None:
        '''
        from datetime import datetime, time
        from pyalgotrading.constants import ExecutionStatus
        self.connection.saved_parameters = {
            'start_timestamp_map': {
                TradingType.PAPERTRADING: datetime.combine(datetime.now().date(), time(9, 30))
            },
            'end_timestamp_map': {
                TradingType.PAPERTRADING: datetime.combine(datetime.now().date(), time(17, 0))
            }
        }

        # expected_result = ''.join([f"[PT] first log [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]", "second log"])

        def get_logs_side_effect(strategy_code, trading_type, initial_next_token):
            get_logs_side_effect.counter += 1
            if get_logs_side_effect.counter == 1:
                return {"data": [f"[PT] first log [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]", "second log"], "nextForwardToken": "TestToken"}
            elif get_logs_side_effect.counter == 2:
                raise AlgoBullsAPIGatewayTimeoutErrorException("get", AlgoBullsAPI.SERVER_ENDPOINT, Mock(), 200)
            else:
                return {"data": []}

        get_logs_side_effect.counter = 0

        strategy_code = "TestStrategyCode"
        trading_type = TradingType.PAPERTRADING
        display_progress_bar = True
        print_live_logs = True
        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_job_status") as mock_get_job_status:
            status_values = [
                ExecutionStatus.STARTING.value,
                ExecutionStatus.STARTED.value,
                ExecutionStatus.STOPPING.value
            ]
            get_job_status_side_effect = [{"message": value} for value in status_values]
            mock_get_job_status.side_effect = get_job_status_side_effect
            with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_logs") as mock_get_logs:
                mock_get_logs.side_effect = get_logs_side_effect
                result = self.connection.get_logs(strategy_code, trading_type, display_progress_bar, print_live_logs)
                # self.assertEqual(result, expected_result)
                self.assertIn("[PT] first log ", result)

    # FIX
    def test_get_report_order_history(self):
        """
        Test for get_report_order_history method
        """
        '''
        Testcase: strategy_code is not instance of str
        '''
        strategy_code = 123
        trading_type = TradingType.BACKTESTING

        with self.assertRaises(AssertionError) as context:
            self.connection.get_report_order_history(strategy_code, trading_type)
        self.assertEqual(str(context.exception), f'Argument "strategy_code" should be a string')

        '''
        Testcase: trading_type is not instance of TradingType
        '''
        strategy_code = "TestStrategyCode"
        trading_type = TradingReportType.ORDER_HISTORY

        with self.assertRaises(AssertionError) as context:
            self.connection.get_report_order_history(strategy_code, trading_type)
        self.assertEqual(str(context.exception), f'Argument "trading_type" should be an enum of type {TradingType.__name__}')
        '''
        Testcase for blocks:
            - if main_data:
                - else:
        '''
        from tabulate import tabulate
        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING

        get_reports_response = {"totalTrades": 999,
                                "data": [{"orderId": 123, "transaction_type": "SELL", "instrument": "NSE:ADANI", "quantity": 20, "currency": "INR", "price": 20, "customer_tradebook_states": {"timestamp_created": [dt.now()], "state": ["OPEN"]}}]}
        order_detail = [
            ["Order ID", get_reports_response["data"][0]["orderId"]],
            ["Transaction Type", get_reports_response["data"][0]["transaction_type"]],
            ["Instrument", get_reports_response["data"][0]["instrument"]],
            ["Quantity", get_reports_response["data"][0]["quantity"]],
            ["Price", str(get_reports_response["data"][0]["currency"]) + str(get_reports_response["data"][0]["price"])]
        ]

        def get_reports_side_effect(strategy_code, trading_type, report_type, country, current_page):
            get_reports_side_effect.counter += 1
            if get_reports_side_effect.counter == 1:
                raise AlgoBullsAPIGatewayTimeoutErrorException("get", AlgoBullsAPI.SERVER_ENDPOINT, Mock(), 200)
            elif get_reports_side_effect.counter == 2:
                return get_reports_response

        get_reports_side_effect.counter = 0

        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_reports") as mock_get_reports:
            mock_get_reports.side_effect = get_reports_side_effect
            result = self.connection.get_report_order_history(strategy_code, trading_type)
            self.assertIn(tabulate(order_detail, tablefmt="psql"), result)
            self.assertIn(tabulate(get_reports_response["data"][0]["customer_tradebook_states"], headers="keys", tablefmt="psql"), result)

        '''
        Testcase for blocks:
            - if main_data:
                - if render_as_dataframe:
        '''
        # def get_reports_side_effect(strategy_code, trading_type, report_type, country, current_page):
        #     get_reports_side_effect.counter += 1
        #     if get_reports_side_effect.counter == 1:
        #         raise AlgoBullsAPIGatewayTimeoutErrorException("get", AlgoBullsAPI.SERVER_ENDPOINT, Mock(), 200)
        #     elif get_reports_side_effect.counter == 2:
        #         return get_reports_response

        get_reports_response = {"totalTrades": 999,
                                "data": [{"orderId": 123, "transaction_type": "SELL", "instrument": "NSE:ADANI", "quantity": 20, "currency": "INR", "price": 20, "customer_tradebook_states": [{"timestamp_created": dt.now(), "state": "OPEN"}]}]}

        def get_reports_side_effect(strategy_code, trading_type, report_type, country, current_page):
            get_reports_side_effect.counter += 1
            if get_reports_side_effect.counter == 1:
                raise AlgoBullsAPIGatewayTimeoutErrorException("get", AlgoBullsAPI.SERVER_ENDPOINT, Mock(), 200)
            elif get_reports_side_effect.counter == 2:
                return get_reports_response

        get_reports_side_effect.counter = 0

        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_reports") as mock_get_reports:
            mock_get_reports.side_effect = get_reports_side_effect
            result = self.connection.get_report_order_history(strategy_code, trading_type, render_as_dataframe=True)
            # self.assertEqual(get_reports_response["data"][0]["orderId"], result.iloc[0]["orderId"])
            # print("\nresult\n", result)
            # self.assertIn(tabulate(order_detail, tablefmt="psql"), result)
            # self.assertIn(tabulate(get_reports_response["data"][0]["customer_tradebook_states"], headers="keys", tablefmt="psql"), result)

    # FIX
    def test_get_report_pnl_table(self):
        """
        Test for get_report_pnl_table method
        """
        '''
        Testcase: 
        '''
        strategy_code = "TestStrategyCode"
        trading_type = TradingType.BACKTESTING

        data = [{'key': 1978408, 'mode': {'modeIcon': 'customIconBT'}, 'strategy': {'code': '', 'instrument': {'segment': 'NSE', 'tradingsymbol': 'ADANIPOWER'}, 'name': 'Aroon Crossover'},
                 'broker': {'icon': 'https://', 'name': 'AlgoBulls Virtual Broker'},
                 'entry': {'timestamp': '2023-07-28 | 12:15 +0530', 'isBuy': True, 'quantity': 20, 'prefix': '₹', 'price': 256.5, 'variety': '', 'isManual': False, 'popover': {'data': [
                     {'order': {'tradingsymbol': 'NSE:ADANIPOWER', 'segment': 'NSE', 'isBuy': True, 'orderId': 'fb30706fe21c4f59ba7374b8dfe7bdef', 'quantity': 20, 'price': 256.5, 'icon': 'ClockCircleFilled', 'color': '#E22828'},
                      'states': [{'label': 'PUT ORDER REQ RECEIVED', 'timestamp': '2023-07-28 06:45:00+0000'}, {'label': 'VALIDATION PENDING', 'timestamp': '2023-07-28 06:45:00+0000'},
                                 {'label': 'OPEN PENDING', 'timestamp': '2023-07-28 06:45:00+0000'},
                                 {'label': 'OPEN', 'timestamp': '2023-07-28 06:45:00+0000'}, {'label': 'COMPLETE', 'timestamp': '2023-07-28 06:45:00+0000'}]}],
                     'component': {'type': 'timeline', 'container': {'span': 24, 'style': {'alignSelf': 'center'}},
                                   'widget': {'timelineProps': {'mode': 'left', 'style': {'width': '100%'}}}}}},
                 'exit': {'timestamp': '2023-07-28 | 15:30 +0530', 'isBuy': False, 'quantity': 20, 'prefix': '₹', 'price': 257.6, 'variety': '', 'isManual': False, 'popover': {'data': [
                     {'order': {'tradingsymbol': 'NSE:ADANIPOWER', 'segment': 'NSE', 'isBuy': False, 'orderId': '5acde5acaf0742fe8367c63e00edb580', 'quantity': 20, 'price': 257.6, 'icon': 'ClockCircleFilled', 'color': '#E22828'},
                      'states': [{'label': 'PUT ORDER REQ RECEIVED', 'timestamp': '2023-07-28 10:00:00+0000'}, {'label': 'VALIDATION PENDING', 'timestamp': '2023-07-28 10:00:00+0000'},
                                 {'label': 'OPEN PENDING', 'timestamp': '2023-07-28 10:00:00+0000'},
                                 {'label': 'OPEN', 'timestamp': '2023-07-28 10:00:00+0000'}, {'label': 'COMPLETE', 'timestamp': '2023-07-28 10:00:00+0000'}]}],
                     'component': {'type': 'timeline', 'container': {'span': 24, 'style': {'alignSelf': 'center'}},
                                   'widget': {'timelineProps': {'mode': 'left', 'style': {'width': '100%'}}}}}},
                 'pnlAbsolute': {'value': 22.0}, 'pnlPercentage': {'value': 0.43}}]

        with patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.get_reports") as mock_get_reports:
            response = {"data": data}
            mock_get_reports.return_value = response
            result = self.connection.get_report_pnl_table(strategy_code, trading_type, "India")
            print("\nresult\n", result)

            # report_stats = self.connection.get_report_statistics(strategy_code, html_dump=False, pnl_df=result)
            # print("\nreport_stats\n", report_stats)

    @patch("pyalgotrading.algobulls.connection.qs.reports.html")
    def test_get_report_statistics(self, mock_html):
        strategy_code = self.strategy_code
        # In case of ZeroDivisionError
        pnl_df = pd.DataFrame(
            {
                "entry_timestamp": pd.to_datetime(["2021-08-02 10:15:00+05:30", "2021-08-02 13:15:00+05:30"]),
                "net_pnl": [-94.0, -2.0]
            }
        )
        with self.assertRaises(Exception) as value_error:
            self.connection.get_report_statistics(strategy_code=strategy_code, pnl_df=pnl_df)
        self.assertEqual(str(value_error.exception), "ERROR: PnL data generated is too less to perform statistical analysis")

        dummy_data = {
            'instrument_segment': ['NSE', 'NSE', 'NSE', 'NSE', 'NSE'],
            'instrument_tradingsymbol': ['RELIANCE', 'RELIANCE', 'RELIANCE', 'RELIANCE', 'RELIANCE'],
            'entry_timestamp': ['2023-01-02 10:15:00+05:30', '2023-01-03 12:15:00+05:30', '2023-01-05 10:15:00+05:30', '2023-01-05 11:15:00+05:30', '2023-01-06 09:15:00+05:30 '],
            'net_pnl': [660000.0, -242500.0, -577500.0, 505000.0, 397500.0],
        }
        dummy_df = pd.DataFrame(dummy_data)

        # Using .csv file
        dummy_df.to_csv('dummy_pnl_data.csv', index=False)
        self.connection.get_report_statistics(strategy_code=strategy_code, initial_funds=0, report="metrics", file_path='dummy_pnl_data.csv')
        mock_html.assert_called_once()

        # Using .xlsx file
        pd.DataFrame(dummy_data).to_excel('dummy_pnl_data.xlsx', index=False)
        self.connection.get_report_statistics(strategy_code=strategy_code, initial_funds=0, report="metrics", file_path='dummy_pnl_data.xlsx')
        mock_html.assert_called()

        # Using wrong file format
        dummy_df.to_csv('dummy_pnl_data.jpg', index=False)
        with self.assertRaises(Exception) as context:
            self.connection.get_report_statistics(strategy_code=strategy_code, initial_funds=1000, report="metrics", file_path='dummy_pnl_data.jpg')
            os.remove('dummy_pnl_data.jpg')
        self.assertEqual(str(context.exception), f'ERROR: File with extension .jpg is not supported.\n Please provide path to files with extension as ".csv" or ".xlsx"')

        # File without entry_timestamp & net_pnl columns
        dummy_df.drop(columns=['entry_timestamp', 'net_pnl'], inplace=True)
        dummy_df.to_csv('dummy_pnl_data.csv', index=False)
        with self.assertRaises(Exception) as context:
            self.connection.get_report_statistics(strategy_code=strategy_code, initial_funds=0, report="metrics", file_path='dummy_pnl_data.csv')
        self.assertEqual(str(context.exception), "ERROR: Given  .csv file does not have the required columns 'entry_timestamp' and 'net_pnl'.")

        # Wrong time format
        dummy_data['entry_timestamp'] = pd.date_range(start="2021-08-02", periods=5, freq='D')
        dummy_df = pd.DataFrame(dummy_data)
        dummy_df.to_csv('dummy_pnl_data.csv', index=False)
        with self.assertRaises(Exception) as ValueError:
            self.connection.get_report_statistics(strategy_code=strategy_code, initial_funds=0, report="metrics", file_path='dummy_pnl_data.csv')
        self.assertEqual(str(ValueError.exception), "ERROR: Datetime strings inside 'entry_timestamp' column should be of the format %Y-%m-%d %H:%M:%S%z.")
        os.remove('dummy_pnl_data.csv')  # Cleanup

    def test_print_strategy_config(self):
        # if trading_type in [TradingType.BACKTESTING, TradingType.PAPERTRADING]:
        trading_type = TradingType.BACKTESTING
        self.connection.saved_parameters = {
            'strategy_code': '72dfc4ca6a1b41a0844f32a34fd09679',
            'start_timestamp_map': {TradingType.BACKTESTING: dt(2021, 8, 1, 9, 15)},
            'end_timestamp_map': {TradingType.BACKTESTING: dt(2023, 7, 31, 15, 30)},
            'strategy_parameters': {'TIME_PERIOD': 12, 'STANDARD_DEVIATIONS': 2},
            'candle_interval': CandleInterval._60_MINUTES,
            'instruments': ['NSE:TATAMOTORS'],
            'strategy_mode': StrategyMode.INTRADAY,
            'lots': 5,
            'initial_funds_virtual': 7000.0,
            'vendor_details': None}

        data = [
            ['Strategy Name', "TestStrategyName"],
            ['Trading Type', trading_type.name],
            ['Instrument(s)', pprint.pformat(self.connection.saved_parameters['instruments'])],
            ['Quantity/Lots', self.connection.saved_parameters['lots']],
            ['Start Timestamp', self.connection.saved_parameters['start_timestamp_map'][trading_type]],
            ['End Timestamp', self.connection.saved_parameters['end_timestamp_map'][trading_type]],
            ['Parameters', pprint.pformat(self.connection.saved_parameters['strategy_parameters'])],
            ['Candle', self.connection.saved_parameters['candle_interval'].value],
            ['Mode', self.connection.saved_parameters['strategy_mode'].name],
            ['Initial Funds (Virtual)', self.connection.saved_parameters['initial_funds_virtual']]
        ]

        _msg = tabulate(data, headers=['Config', 'Value'], tablefmt="fancy_grid")
        expected_stdout = f"\nStarting the strategy 'TestStrategyName' in {trading_type.name} mode...\n{_msg}\n"

        with patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_strategy_name", return_value="TestStrategyName") as mock_get_strategy_name:
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                self.connection.print_strategy_config(trading_type)
                self.assertIn(expected_stdout, mock_stdout.getvalue())
            mock_get_strategy_name.assert_called_once_with(self.connection.saved_parameters["strategy_code"])

        # elif trading_type in [TradingType.REALTRADING]:
        trading_type = TradingType.REALTRADING
        self.connection.saved_parameters['vendor_details'] = {'brokerName': 'TestBrokerName'}
        self.connection.saved_parameters['start_timestamp_map'] = {TradingType.REALTRADING: time(9, 0)}
        self.connection.saved_parameters['end_timestamp_map'] = {TradingType.REALTRADING: time(15, 0)}

        data.pop()
        data[1] = ['Trading Type', trading_type.name]
        data[4] = ['Start Timestamp', self.connection.saved_parameters['start_timestamp_map'][trading_type]]
        data[5] = ['End Timestamp', self.connection.saved_parameters['end_timestamp_map'][trading_type]]
        data.insert(0, ["Broker Name", self.connection.saved_parameters['vendor_details']['brokerName']])
        data.insert(0, ["Vendor Name", self.connection.saved_parameters['vendor_details']['brokerName']])
        _msg = tabulate(data, headers=['Config', 'Value'], tablefmt="fancy_grid")
        expected_stdout = f"\nStarting the strategy 'TestStrategyName' in {trading_type.name} mode...\n{_msg}\n"

        with patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_strategy_name", return_value="TestStrategyName") as mock_get_strategy_name:
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                self.connection.print_strategy_config(trading_type)
                self.assertIn(expected_stdout, mock_stdout.getvalue())
            mock_get_strategy_name.assert_called_once_with(self.connection.saved_parameters["strategy_code"])

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.delete_previous_trades")
    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.set_strategy_config")
    @patch("pyalgotrading.algobulls.connection.AlgoBullsAPI.start_strategy_algotrading", return_value="Mock response")
    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.search_instrument", return_value=[{"id": 17, "value": "NSE:TATAMOTORS"}])
    def test_start_job(self, mock_search_instrument, mock_start_strategy_algotrading, mock_set_strategy_config, mock_delete_previous_trades):
        strategy_code = 'TestStrategyCode'
        start_timestamp = '2021-08-01 09:15 +0530'
        end_timestamp = '2023-07-31 15:30 +0530'
        instruments = 'NSE:TATAMOTORS'
        lots = 5
        strategy_parameters = {'TIME_PERIOD': 12, 'STANDARD_DEVIATIONS': 2}
        candle_interval = '1 hour'
        mode = "INTRADAY"
        delete_previous_trades = True
        trading_type = TradingType.BACKTESTING
        broking_details = {
            'brokerName': 'ZERODHA',
            'credentialParameters': {}
        }
        initial_funds_virtual = 7000

        expected_saved_params = {
            'strategy_code': strategy_code,
            'start_timestamp_map': {trading_type: get_datetime_with_tz(start_timestamp, trading_type)},
            'end_timestamp_map': {trading_type: get_datetime_with_tz(end_timestamp, trading_type)},
            'strategy_parameters': strategy_parameters,
            'candle_interval': CandleInterval._60_MINUTES,
            'instruments': [instruments],
            'strategy_mode': StrategyMode.INTRADAY,
            'lots': lots,
            'initial_funds_virtual': initial_funds_virtual,
            'vendor_details': broking_details

        }

        expected_kwargs_set_strategy_config = {
            'strategy_code': strategy_code,
            'strategy_config': {
                'instruments': {
                    'instruments': [{"id": mock_search_instrument.return_value[0]["id"]}]
                },
                'lots': lots,
                'userParams': [{'paramName': 'TIME_PERIOD', 'paramValue': 12}, {'paramName': 'STANDARD_DEVIATIONS', 'paramValue': 2}],
                'candleDuration': CandleInterval._60_MINUTES.value,
                'strategyMode': StrategyMode.INTRADAY.value

            },
            'trading_type': trading_type
        }

        expected_kwargs_start_strategy_algotrading = {
            'strategy_code': strategy_code,
            'start_timestamp': get_datetime_with_tz(start_timestamp, trading_type),
            'end_timestamp': get_datetime_with_tz(end_timestamp, trading_type),
            'trading_type': trading_type,
            'lots': lots,
            'initial_funds_virtual': initial_funds_virtual,
            'broker_details': broking_details,
            'location': EXCHANGE_LOCALE_MAP['NSE']
        }

        result = self.connection.start_job(
            strategy_code=strategy_code,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            instruments=instruments,
            lots=lots,
            strategy_parameters=strategy_parameters,
            candle_interval=candle_interval,
            strategy_mode=mode,
            initial_funds_virtual=initial_funds_virtual,
            delete_previous_trades=delete_previous_trades,
            trading_type=trading_type,
            broking_details=broking_details
        )

        self.assertEqual(self.connection.saved_parameters, expected_saved_params)

        mock_delete_previous_trades.assert_called_once_with(strategy_code)
        mock_set_strategy_config.assert_called_once_with(**expected_kwargs_set_strategy_config)
        mock_start_strategy_algotrading.assert_called_once_with(**expected_kwargs_start_strategy_algotrading)
        self.assertEqual(result, mock_start_strategy_algotrading.return_value)

        # For trading_type other than BACKTESTING
        start_timestamp = "15:30 +0530"
        end_timestamp = "15:30 +0530"
        trading_type = TradingType.REALTRADING
        result = self.connection.start_job(
            strategy_code=strategy_code,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            instruments=instruments,
            lots=lots,
            strategy_parameters=strategy_parameters,
            candle_interval=candle_interval,
            strategy_mode=mode,
            initial_funds_virtual=initial_funds_virtual,
            delete_previous_trades=delete_previous_trades,
            trading_type=trading_type,
            broking_details=broking_details
        )
        self.assertEqual(result, mock_start_strategy_algotrading.return_value)

        # Invalid exchange
        start_timestamp = "15:30 +0530"
        end_timestamp = "15:30 +0530"
        instruments = 'I:TATAMOTORS'
        trading_type = TradingType.REALTRADING
        with self.assertRaises(KeyError) as context:
            result = self.connection.start_job(
                strategy_code=strategy_code,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                instruments=instruments,
                lots=lots,
                strategy_parameters=strategy_parameters,
                candle_interval=candle_interval,
                strategy_mode=mode,
                initial_funds_virtual=initial_funds_virtual,
                delete_previous_trades=delete_previous_trades,
                trading_type=trading_type,
                broking_details=broking_details
            )
        self.assertEqual(str(context.exception), "'en-US'")

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.start_job", return_value="Mock return value")
    def test_backtest(self, mock_start_job):
        strategy = 'TestStrategyCode'
        start = '2021-08-01 09:15 +0530'
        end = '2023-07-31 15:30 +0530'
        instruments = 'NSE:TATAMOTORS'
        lots = 5
        parameters = {'TIME_PERIOD': 12, 'STANDARD_DEVIATIONS': 2}
        candle = '1 hour'
        mode = "INTRADAY"
        delete_previous_trades = True
        initial_funds_virtual = 7000
        vendor_details = {
            'brokerName': 'ZERODHA',
            'credentialParameters': {}
        }
        kwargs = {"key": "value"}

        self.connection.backtesting_pnl_data = "NotNone"

        self.connection.backtest(strategy=strategy, start=start, end=end, instruments=instruments, lots=lots, parameters=parameters, candle=candle, mode=mode, delete_previous_trades=delete_previous_trades, initial_funds_virtual=initial_funds_virtual,
                                 vendor_details=vendor_details, **kwargs)
        mock_start_job.assert_called_once_with(strategy_code=strategy, start_timestamp=start, end_timestamp=end, instruments=instruments, lots=lots, strategy_parameters=parameters, candle_interval=candle, strategy_mode=mode,
                                               initial_funds_virtual=initial_funds_virtual, delete_previous_trades=delete_previous_trades, trading_type=TradingType.BACKTESTING, broking_details=vendor_details, **kwargs)
        self.assertIsNone(self.connection.backtesting_pnl_data)

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_job_status", return_value="Mock return value")
    def test_get_backtesting_job_status(self, mock_get_job_status):
        strategy_code = "TestStrategyCode"
        result = self.connection.get_backtesting_job_status(strategy_code)
        mock_get_job_status.assert_called_once_with(strategy_code, TradingType.BACKTESTING)
        self.assertEqual(result, mock_get_job_status.return_value)

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.stop_job", return_value="Mock return value")
    def test_stop_backtesting_job(self, mock_stop_job):
        strategy_code = "TestStrategyCode"
        result = self.connection.stop_backtesting_job(strategy_code)
        mock_stop_job.assert_called_once_with(strategy_code=strategy_code, trading_type=TradingType.BACKTESTING)
        self.assertEqual(result, mock_stop_job.return_value)

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_logs", return_value="Mock return value")
    def test_get_backtesting_logs(self, mock_get_logs):
        strategy_code = "TestStrategyCode"
        display_progress_bar = True
        print_live_logs = False
        result = self.connection.get_backtesting_logs(strategy_code, display_progress_bar, print_live_logs)
        mock_get_logs.assert_called_once_with(strategy_code, trading_type=TradingType.BACKTESTING, display_progress_bar=display_progress_bar, print_live_logs=print_live_logs)
        self.assertEqual(result, mock_get_logs.return_value)

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_report_pnl_table", return_value="Mock return value")
    def test_get_backtesting_report_pnl_table(self, mock_get_report_pnl_table):
        strategy_code = "TestStrategyCode"
        country = "India"
        force_fetch = False
        broker_commission_percentage = None
        broker_commission_price = None
        slippage_percent = None

        result = self.connection.get_backtesting_report_pnl_table(strategy_code, country=country, force_fetch=force_fetch, broker_commission_percentage=broker_commission_percentage, broker_commission_price=broker_commission_price,
                                                                  slippage_percent=slippage_percent)
        mock_get_report_pnl_table.assert_called_once_with(strategy_code, TradingType.BACKTESTING, country, broker_commission_percentage, broker_commission_price, slippage_percent)
        self.assertEqual(result, mock_get_report_pnl_table.return_value)
        self.assertEqual(self.connection.backtesting_pnl_data, mock_get_report_pnl_table.return_value)

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_backtesting_report_pnl_table", return_value="Mock get_backtesting_report_pnl_table")
    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_report_statistics", return_value="Mock get_report_statisticse")
    def test_get_backtesting_report_statistics(self, mock_get_report_statistics, mock_get_backtesting_report_pnl_table):
        result = self.connection.get_backtesting_report_statistics(self.strategy_code)
        self.assertEqual(result, "Mock get_report_statisticse")
        # If self.backtesting_pnl_data is not None
        self.connection.backtesting_pnl_data = {
            'net_pnl': [100, -50, 75, 120, -80, 200, -150, 100, -50, 75],
        }
        result = self.connection.get_backtesting_report_statistics(self.strategy_code)
        self.assertEqual(result, "Mock get_report_statisticse")

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_report_order_history", return_value="Mock get_report_order_history")
    def test_get_backtesting_report_order_history(self, mock_get_report_order_history):
        result = self.connection.get_backtesting_report_order_history(self.strategy_code)
        self.assertEqual(result, "Mock get_report_order_history")

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_logs", return_value="Mock get_logs")
    def test_get_papertrading_logs(self, mock_get_logs):
        result = self.connection.get_papertrading_logs(self.strategy_code)
        self.assertEqual(result, "Mock get_logs")

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_papertrading_report_pnl_table", return_value="Mock get_papertrading_report_pnl_table")
    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_report_statistics", return_value="Mock get_report_statistics")
    def test_get_papertrading_report_statistics(self, mock_get_report_statistics, mock_get_papertrading_report_pnl_table):
        result = self.connection.get_papertrading_report_statistics(self.strategy_code)
        self.assertEqual(result, "Mock get_report_statistics")
        # When self.papertrade_pnl_data is not None
        self.connection.papertrade_pnl_data = {
            'net_pnl': [100, -50, 75, 120, -80, 200, -150, 100, -50, 75],
        }
        result = self.connection.get_papertrading_report_statistics(self.strategy_code)
        self.assertEqual(result, "Mock get_report_statistics")

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_logs", MagicMock(return_value="Mock get_logs"))
    def test_get_realtrading_logs(self):
        result = self.connection.get_realtrading_logs(self.strategy_code)
        self.assertEqual(result, "Mock get_logs")

    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_realtrading_report_pnl_table", MagicMock(return_value="Mock get_realtrading_report_pnl_table"))
    @patch("pyalgotrading.algobulls.connection.AlgoBullsConnection.get_report_statistics", MagicMock(return_value="Mock get_report_statistics"))
    def test_get_realtrading_report_statistics(self):
        result = self.connection.get_realtrading_report_statistics(self.strategy_code)
        self.assertEqual(result, "Mock get_report_statistics")
        # When self.realtrade_pnl_data is not None
        self.connection.realtrade_pnl_data = {
            'net_pnl': [100, -50, 75, 120, -80, 200, -150, 100, -50, 75],
        }
        result = self.connection.get_realtrading_report_statistics(self.strategy_code)
        self.assertEqual(result, "Mock get_report_statistics")


if __name__ == '__main__':
    unittest.main()
