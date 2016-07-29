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
from mock import patch, MagicMock, PropertyMock
from mbed_host_tests.host_tests_conn_process import conn_process_factory, run_default_conn_process


class ConnProcessFactoryTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('logging.getLogger', MagicMock())
    @patch('mbed_host_tests.host_tests_conn_process.conn_process.Process')
    def test_default(self, mock_process):
        property_mock = PropertyMock()
        type(mock_process.return_value).daemon = property_mock
        
        args = (MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock())

        conn_process = conn_process_factory(*args)
        
        mock_process.assert_called_with(target=run_default_conn_process, args=('CONN',) + args)
        property_mock.assert_called_with(True)
        self.assertTrue(mock_process.return_value.start.called, "The conn process was never started")
        self.assertIsInstance(conn_process, MagicMock, "The returned conn process did not match")
    
    @patch('logging.getLogger', MagicMock())
    @patch('mbed_host_tests.host_tests_conn_process.conn_process.Process')
    def test_greentea_client(self, mock_process):
        property_mock = PropertyMock()
        type(mock_process.return_value).daemon = property_mock
        
        args = (MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock())

        conn_process = conn_process_factory(*args, conn_process_name="greentea-client")
        
        mock_process.assert_called_with(target=run_default_conn_process, args=('CONN',) + args)
        property_mock.assert_called_with(True)
        self.assertTrue(mock_process.return_value.start.called, "The conn process was never started")
        self.assertIsInstance(conn_process, MagicMock, "The returned conn process did not match")
    
    @patch('logging.getLogger', MagicMock())
    def test_invalid_conn_process(self):
        self.assertRaises(NotImplementedError, conn_process_factory,
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            "Unknown Conn Process")
