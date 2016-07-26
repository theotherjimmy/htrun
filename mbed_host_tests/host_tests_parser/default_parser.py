#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2011-2016 ARM Limited

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
from time import time
from mbed_host_tests.host_tests_parser import BaseParser

class DefaultParser(BaseParser):
    def __init__(self):
        # Regex for the KiVi Parser
        super(DefaultParser, self).__init__(r"\{\{([\w\d_-]+);([^\}]+)\}\}\n")

    def get_kv(self):
        """! Return the KV results from the buffer 
        @return Tuple of type (key, value, timestamp)
        """
        m = self.re.search(self.buff[self.buff_idx:])
        if m:
            (key, value) = m.groups()
            kv_str = m.group(0)
            self.buff_idx = self.buff.find(kv_str, self.buff_idx) + len(kv_str)
        return (key, value, time())
