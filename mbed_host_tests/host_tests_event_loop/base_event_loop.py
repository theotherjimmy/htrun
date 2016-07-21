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

import traceback

from Queue import Empty as QueueEmpty   # Queue here refers to the module, not a class

from time import time
from abc import ABCMeta, abstractmethod

class BaseEventLoop():
    __metaclass__ = ABCMeta

    def __init__(self, logger, event_queue, dut_event_queue, process, test_selector):
        """! Create a Base Event Loop instance containing all the generic sections of an event loop
        @param logger An instance of type <HtrunLogger>
        @param event_queue Queue of events to process
        @param dut_event_queue Queue for sending events
        @param process The process that is running the connection
        @param test_selector The TestSelector that is using the event loop
        @return Object of type <BaseEventLoop>
        """

        self.logger = logger
        self.event_queue = event_queue
        self.dut_event_queue = dut_event_queue
        self.callbacks = {}
        self.p = process
        self.test_selector = test_selector

        # Default test case timeout
        self.timeout_duration = 10
        self.result = None
        self.start_time = None

    def register_callback(self, name, callback):
        """! Register any callbacks that are needed for processing the events
        @param name The string name used to reference the callback
        @param callback The callable to register against the name
        """
        self.callbacks[name] = callback

    def run_loop(self):
        """! Run the event loop, which will process the events that are passed to
             the event_queue, and possibly add events to the dut_event_queue.
        @return TestSelection.TestResults.RESULT_* enum
        """

        self.start_time = time()
        try:
            while (time() - self.start_time) < self.timeout_duration:
                # Handle default events like timeout, host_test_name, ...
                if not self.event_queue.empty():
                    try:
                        event = self.event_queue.get(timeout=1)
                    except QueueEmpty:
                        continue
                    continue_loop = self.process_event(event)
                    if not continue_loop:
                        break
        except Exception:
            self.logger.prn_err("something went wrong in the event loop!")
            self.logger.prn_inf("==== Traceback start ====")
            for line in traceback.format_exc().splitlines():
                print line
            self.logger.prn_inf("==== Traceback end ====")
            self.result = test_selector.RESULT_ERROR

        time_duration = time() - self.start_time
        self.logger.prn_inf("test suite run finished after %.2f sec..."% time_duration)

        self.run_finish()

        return self.result

    @abstractmethod
    def process_event(self, event):
        """! Process an indivdual event passed from the event_queue
        @param event The event taken from the event_queue
        @return True if the next event should be processed, or False if the 
                event loop should stop
        """
        pass

    @abstractmethod
    def run_finish(self):
        """! Perform any finishing processing after the main loop """
        pass
