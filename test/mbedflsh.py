#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2017 ARM Limited

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
from mock import patch

from mbed_host_tests import mbedflsh

class FlashCLI(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parsing(self):
        parser = mbedflsh._cmd_parser_setup()
        try:
            parser.parse_args(["--plugins", "--version"])
            assert False, "Parser allowed conflicting options: --plugins and --version"
        except SystemExit:
            pass
        try:
            parser.parse_args(["--file", "foo", "--version"])
            assert False, "Parser allowed conflicting options: --file and version"
        except SystemExit:
            pass
        try:
            parser.parse_args(["--file", "foo", "--plugins"])
            assert False, "Parser allowed conflicting options: --file and plugins"
        except SystemExit:
            pass

    def test_always_exit(self):
        with patch("sys.exit") as _exit,\
             patch("mbed_host_tests.mbedflsh._cmd_parser_setup") as _parser,\
             patch("mbed_host_tests.host_tests_plugins.call_plugin") as _call_plug:
            _call_plug.return_value = 0
            opts = _parser.return_value.parse_args.return_value
            opts.version = True
            opts.list_plugins = False
            opts.filename = None
            opts.copy_method = 'shell'
            opts.disk = None

            mbedflsh.main()
            _exit.assert_called_with(0)
            _exit.reset_mock()

            opts.version = False
            opts.list_plugins = True
            mbedflsh.main()
            _exit.assert_called_with(0)
            _exit.reset_mock()

            opts.list_plugins = False
            opts.filename = "foo"
            mbedflsh.main()
            _exit.assert_called_with(0)
            _exit.reset_mock()
            _call_plug.assert_called()
