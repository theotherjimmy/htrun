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

from mbed_host_tests.host_tests_parser import DefaultParser

def parser_factory(config, logger, parser_name="kivi-parser"):
    """! Factory producing parsers based on the name
    @param config Global configuration for the parser
    @param logger Logger for recording the chosen parser
    @param event_loop_name Name of the parser (Default: 'kivi-parser')
    @return Object of type <BaseParser> or None if type of parser is unknown (parser_name)
    """

    if parser_name == "kivi-parser":
        # Produce and return the parser
        logger.prn_inf("initializing KiVi Parser... ")
        parser = DefaultParser()
        return parser
    else:
        logger.prn_err("unknown parser!")
        raise NotImplementedError("Parser factory: unknown parser '%s'!" % parser_name)
