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

from mbed_host_tests.host_tests_logger import HtrunLogger
from mbed_host_tests.host_tests_event_loop import DefaultEventLoop

def event_loop_factory(config,
                       logger_name,
                       event_queue,
                       dut_event_queue,
                       process,
                       test_selector,
                       event_loop_name="greentea-client"):
    """! Factory producing event loops based on the name and the config
    @param config Global configuration for the event loop
    @param logger Name of logger to be produced
    @param event_queue Queue of events to process
    @param dut_event_queue Queue for sending events
    @param process The process that is running the connection
    @param test_selector The TestSelector that is using the event loop
    @param event_loop_name Name of the event loop (Default: 'greentea-client')
    @return Object of type <BaseEventLoop> or None if type of event loop is unknown (event_loop_name)
    """

    logger = HtrunLogger(logger_name)

    if event_loop_name == "greentea-client":
        # Produce and return the event loop
        logger.prn_inf("initializing default event loop... ")
        event_loop = DefaultEventLoop(
            logger,
            event_queue,
            dut_event_queue,
            process,
            test_selector)
        return event_loop
    else:
        logger.prn_err("unknown event loop!")
        raise NotImplementedError("EventLoop factory: unknown event loop '%s'!" % event_loop_name)
        return None
