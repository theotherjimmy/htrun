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

from time import time
from Queue import Empty as QueueEmpty
from mbed_host_tests import BaseHostTest
from mbed_host_tests import get_host_test
from mbed_host_tests.host_tests_event_loop import BaseEventLoop
from mbed_host_tests.host_tests_conn_process import conn_process_factory

class DefaultEventLoop(BaseEventLoop):
    def __init__(self, logger, event_queue, dut_event_queue, test_selector):
        super(DefaultEventLoop, self).__init__(logger, event_queue, dut_event_queue, test_selector)

        self.p = conn_process_factory(
            self.test_selector.options,
            self.test_selector.mbed,
            self.event_queue,
            self.dut_event_queue)

        # Add the needed callbacks
        def callback__notify_prn(key, value, timestamp):
            """! Handles __norify_prn. Prints all lines in separate log line """
            for line in value.splitlines():
                self.logger.prn_inf(line)

        self.register_callback("__notify_prn", callback__notify_prn)
        self.consume_preamble_events = True

        # if True we will allow host test to consume all events after test is finished
        self.callbacks_consume = True
        # Flag check if __exit event occurred
        self.callbacks__exit = False
        # Handle to dynamically loaded host test object
        self.test_supervisor = None
        # Version: greentea-client version from DUT
        self.client_version = None

    def is_host_test_obj_compatible(self, obj_instance):
        """! Check if host test object loaded is actually host test class
             derived from 'mbed_host_tests.BaseHostTest()'
             Additionaly if host test class implements custom ctor it should
             call BaseHostTest().__Init__()
        @param obj_instance Instance of host test derived class
        @return True if obj_instance is derived from mbed_host_tests.BaseHostTest()
                and BaseHostTest.__init__() was called, else return False
        """

        result = False
        if obj_instance:
            result = True
            self.logger.prn_inf("host test class: '%s'"% obj_instance.__class__)

            # Check if host test (obj_instance) is derived from mbed_host_tests.BaseHostTest()
            if not isinstance(obj_instance, BaseHostTest):
                # In theory we should always get host test objects inheriting from BaseHostTest()
                # because loader will only load those.
                self.logger.prn_err("host test must inherit from mbed_host_tests.BaseHostTest() class")
                result = False

            # Check if BaseHostTest.__init__() was called when custom host test is created
            if not obj_instance.base_host_test_inited():
                self.logger.prn_err("custom host test __init__() must call BaseHostTest.__init__(self)")
                result = False

        return result

    def process_event(self, event):
        key, value, timestamp = event
        if self.consume_preamble_events:
            if key == '__timeout':
                # Override default timeout for this event queue
                self.start_time = time()
                self.timeout_duration = int(value) # New timeout
                self.logger.prn_inf("setting timeout to: %d sec"% int(value))
            elif key == '__version':
                self.client_version = value
                self.logger.prn_inf("DUT greentea-client version: " + self.client_version)
            elif key == '__host_test_name':
                # Load dynamically requested host test
                self.test_supervisor = get_host_test(value)

                # Check if host test object loaded is actually host test class
                # derived from 'mbed_host_tests.BaseHostTest()'
                # Additionaly if host test class implements custom ctor it should
                # call BaseHostTest().__Init__()
                if self.test_supervisor and self.is_host_test_obj_compatible(self.test_supervisor):
                    # Pass communication queues and setup() host test
                    self.test_supervisor.setup_communication(self.event_queue, self.dut_event_queue)
                    try:
                        # After setup() user should already register all callbacks
                        self.test_supervisor.setup()
                    except (TypeError, ValueError):
                        # setup() can throw in normal circumstances TypeError and ValueError
                        self.logger.prn_err("host test setup() failed, reason:")
                        self.logger.prn_inf("==== Traceback start ====")
                        for line in traceback.format_exc().splitlines():
                            print line
                        self.logger.prn_inf("==== Traceback end ====")
                        self.result = self.test_selector.RESULT_ERROR
                        return False

                    self.logger.prn_inf("host test setup() call...")
                    if self.test_supervisor.get_callbacks():
                        self.callbacks.update(self.test_supervisor.get_callbacks())
                        self.logger.prn_inf("CALLBACKs updated")
                    else:
                        self.logger.prn_wrn("no CALLBACKs specified by host test")
                    self.logger.prn_inf("host test detected: %s"% value)
                else:
                    self.logger.prn_err("host test not detected: %s"% value)
                    self.result = self.test_selector.RESULT_ERROR
                    return False

                self.consume_preamble_events = False
            elif key == '__sync':
                # This is DUT-Host Test handshake event
                self.logger.prn_inf("sync KV found, uuid=%s, timestamp=%f"% (str(value), timestamp))
            elif key == '__notify_conn_lost':
                # This event is sent by conn_process, DUT connection was lost
                self.logger.prn_err(value)
                self.logger.prn_wrn("stopped to consume events due to %s event"% key)
                self.callbacks_consume = False
                self.result = self.test_selector.RESULT_IO_SERIAL
                return False
            elif key.startswith('__'):
                # Consume other system level events
                pass
            else:
                self.logger.prn_err("orphan event in preamble phase: {{%s;%s}}, timestamp=%f"% (key, str(value), timestamp))
        else:
            if key == '__notify_complete':
                # This event is sent by Host Test, test result is in value
                # or if value is None, value will be retrieved from HostTest.result() method
                self.logger.prn_inf("%s(%s)"% (key, str(value)))
                self.result = value
                return False
            elif key == '__reset_dut':
                # Disconnect to avoid connection lost event
                self.dut_event_queue.put(('__host_test_finished', True, time()))
                self.p.join()

                if value == self.test_selector.RESET_TYPE_SW_RST:
                    self.logger.prn_inf("Performing software reset.")
                    # Just disconnecting and re-connecting comm process will soft reset DUT
                elif value == self.test_selector.RESET_TYPE_HW_RST:
                    self.logger.prn_inf("Performing hard reset.")
                    # request hardware reset
                    self.test_selector.mbed.hw_reset()
                else:
                    self.logger.prn_err("Invalid reset type (%s). Supported types [%s]." %
                                        (value, ", ".join([self.test_selector.RESET_TYPE_HW_RST,
                                                           self.test_selector.RESET_TYPE_SW_RST])))
                    self.logger.prn_inf("Software reset will be performed.")

                # connect to the device
                self.p = conn_process_factory(
                    self.test_selector.options,
                    self.test_selector.mbed,
                    self.event_queue,
                    self.dut_event_queue)
            elif key == '__notify_conn_lost':
                # This event is sent by conn_process, DUT connection was lost
                self.logger.prn_err(value)
                self.logger.prn_wrn("stopped to consume events due to %s event"% key)
                self.callbacks_consume = False
                self.result = self.test_selector.RESULT_IO_SERIAL
                return False
            elif key == '__exit':
                # This event is sent by DUT, test suite exited
                self.logger.prn_inf("%s(%s)"% (key, str(value)))
                self.callbacks__exit = True
                return False
            elif key in self.callbacks:
                # Handle callback
                self.callbacks[key](key, value, timestamp)
            else:
                self.logger.prn_err("orphan event in main phase: {{%s;%s}}, timestamp=%f"% (key, str(value), timestamp))
        return True

    def run_finish(self):
        # Force conn_proxy process to return
        self.dut_event_queue.put(('__host_test_finished', True, time()))
        self.p.join()
        self.logger.prn_inf("CONN exited with code: %s"% str(self.p.exitcode))

        # Callbacks...
        self.logger.prn_inf("No events in queue" if self.event_queue.empty() else "Some events in queue")

        # If host test was used we will:
        # 1. Consume all existing events in queue if consume=True
        # 2. Check result from host test and call teardown()

        if self.callbacks_consume:
            # We are consuming all remaining events if requested
            while not self.event_queue.empty():
                try:
                    (key, value, timestamp) = self.event_queue.get(timeout=1)
                except QueueEmpty:
                    break

                if key == '__notify_complete':
                    # This event is sent by Host Test, test result is in value
                    # or if value is None, value will be retrieved from HostTest.result() method
                    self.logger.prn_inf("%s(%s)"% (key, str(value)))
                    self.result = value
                elif key.startswith('__'):
                    # Consume other system level events
                    pass
                elif key in self.callbacks:
                    self.callbacks[key](key, value, timestamp)
                else:
                    self.logger.prn_wrn(">>> orphan event: {{%s;%s}}, timestamp=%f"% (key, str(value), timestamp))
            self.logger.prn_inf("stopped consuming events")

        if self.result is not None:  # We must compare here against None!
            # Here for example we've received some error code like IOERR_COPY
            self.logger.prn_inf("host test result() call skipped, received: %s"% str(self.result))
        else:
            if self.test_supervisor:
                self.result = self.test_supervisor.result()
            self.logger.prn_inf("host test result(): %s"% str(self.result))

        if not self.callbacks__exit:
            self.logger.prn_wrn("missing __exit event from DUT")

        #if not callbacks__exit and not result:
        if not self.callbacks__exit and self.result is None:
            self.logger.prn_err("missing __exit event from DUT and no result from host test, timeout...")
            self.result = self.test_selector.RESULT_TIMEOUT

        self.logger.prn_inf("calling blocking teardown()")
        if self.test_supervisor:
            self.test_supervisor.teardown()
        self.logger.prn_inf("teardown() finished")
