#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import unittest
from mock import patch, MagicMock
from mbed_host_tests.host_tests_logger import HtrunLogger
from mbed_host_tests.host_tests_event_loop import event_loop_factory
from mbed_host_tests.host_tests_event_loop import BaseEventLoop, DefaultEventLoop

class EventLoopFactoryTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('logging.getLogger')
    def test_default(self, mock_logging_getLogger):
        mock_logging_getLogger.return_value = MagicMock()

        event_loop = event_loop_factory(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock())

        self.assertTrue(isinstance(event_loop, DefaultEventLoop))

    @patch('logging.getLogger')
    def test_greentea_client(self, mock_logging_getLogger):
        mock_logging_getLogger.return_value = MagicMock()

        event_loop = event_loop_factory(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            "greentea-client")

        self.assertTrue(isinstance(event_loop, DefaultEventLoop))

    @patch('mbed_host_tests.host_tests_event_loop.DefaultEventLoop.__init__')
    @patch('logging.getLogger')
    def test_greentea_client_logger(self, mock_logging_getLogger, mock_default_event_loop_init):
        mock_logging_getLogger.return_value = MagicMock()
        mock_default_event_loop_init.return_value = None

        event_loop = event_loop_factory(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            "greentea-client")

        call_args = mock_default_event_loop_init.call_args
        self.assertIsNotNone(call_args)
        self.assertIsInstance(call_args[0][0], HtrunLogger)

    @patch('logging.getLogger')
    def test_invalid_event_loop(self, mock_logging_getLogger):
        mock_logging_getLogger.return_value = MagicMock()

        self.assertRaises(NotImplementedError, event_loop_factory, 
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            "DoesNotExist")

if __name__ == '__main__':
    unittest.main()
