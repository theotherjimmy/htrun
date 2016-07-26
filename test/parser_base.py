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

import re
import unittest
from mock import patch, MagicMock
from mbed_host_tests.host_tests_parser import BaseParser, DefaultParser, parser_factory


class BaseParserTestCase(unittest.TestCase):

    class ParserClassMock(BaseParser):
        def __init__(self):
            super(BaseParserTestCase.ParserClassMock, self).__init__(r"test")

        def get_kv(self, event):
            pass

    def setUp(self):
        self.PARSER = self.ParserClassMock()

    def tearDown(self):
        self.PARSER = None

    def test_append(self):
        payload = "Test Payload"
        payload_end = "End Test Payload"

        self.PARSER.append(payload)
        self.PARSER.append(payload_end)

        self.assertTrue(self.PARSER.buff.startswith(payload), "The buffer was not appended correctly")
        self.assertTrue(self.PARSER.buff.endswith(payload_end), "The buffer was not appended correctly")

    def test_search(self):
        test_payload = "test"
        test_payload_missing = "not"

        self.PARSER.append(test_payload)
        self.PARSER.append(test_payload_missing)

        self.assertIsNotNone(self.PARSER.search())
        self.PARSER.buff_idx = len(test_payload) - 1
        self.assertIsNone(self.PARSER.search())
