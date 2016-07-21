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

Author: Przemyslaw Wirkus <Przemyslaw.Wirkus@arm.com>
"""


import sys
import traceback
from time import time
from Queue import Empty as QueueEmpty   # Queue here refers to the module, not a class

from mbed_host_tests import BaseHostTest
from multiprocessing import Process, Queue, Lock
from mbed_host_tests import print_ht_list
from mbed_host_tests import get_host_test
from mbed_host_tests import enum_host_tests
from mbed_host_tests import host_tests_plugins
from mbed_host_tests.host_tests_logger import HtrunLogger
from mbed_host_tests.host_tests_conn_proxy import conn_process
from mbed_host_tests.host_tests_event_loop import event_loop_factory
from mbed_host_tests.host_tests_runner.host_test import DefaultTestSelectorBase
from mbed_host_tests.host_tests_toolbox.host_functional import handle_send_break_cmd

class DefaultTestSelector(DefaultTestSelectorBase):
    """! Select default host_test supervision (replaced after auto detection) """
    RESET_TYPE_SW_RST   = "software_reset"
    RESET_TYPE_HW_RST   = "hardware_reset"

    def __init__(self, options):
        """! ctor
        """
        self.options = options

        self.logger = HtrunLogger('HTST')

        # Handle extra command from
        if options:
            if options.enum_host_tests:
                path = self.options.enum_host_tests
                enum_host_tests(path, verbose=options.verbose)

            if options.list_reg_hts:    # --list option
                print_ht_list(verbose=options.verbose)
                sys.exit(0)

            if options.list_plugins:    # --plugins option
                host_tests_plugins.print_plugin_info()
                sys.exit(0)

            if options.version:         # --version
                import pkg_resources    # part of setuptools
                version = pkg_resources.require("mbed-host-tests")[0].version
                print version
                sys.exit(0)

            if options.send_break_cmd:  # -b with -p PORT (and optional -r RESET_TYPE)
                handle_send_break_cmd(port=options.port,
                    disk=options.disk,
                    reset_type=options.forced_reset_type,
                    verbose=options.verbose)
                sys.exit(0)

            if options.global_resource_mgr:
                # If Global Resource Mgr is working it will handle reset/flashing workflow
                # So local plugins are offline
                self.options.skip_reset = True
                self.options.skip_flashing = True

        DefaultTestSelectorBase.__init__(self, options)

    def run_test(self):
        """! This function implements key-value protocol state-machine.
            Handling of all events and connector are handled here.
        @return Return self.TestResults.RESULT_* enum
        """
        event_queue = Queue()       # Events from DUT to host
        dut_event_queue = Queue()   # Events from host to DUT {k;v}

        self.logger.prn_inf("starting host test process...")

        def start_conn_process():
            # Create device info here as it may change after restart.
            conn_config = {
                "digest" : "serial",
                "port" : self.mbed.port,
                "baudrate" : self.mbed.serial_baud,
                "program_cycle_s" : self.options.program_cycle_s,
                "reset_type" : self.options.forced_reset_type,
                "target_id" : self.options.target_id,
                "serial_pooling" : self.options.pooling_timeout,
                "forced_reset_timeout" : self.options.forced_reset_timeout,
                "sync_behavior" : self.options.sync_behavior,
                "platform_name" : self.options.micro,
                "image_path" : self.mbed.image_path,
            }

            if self.options.global_resource_mgr:
                grm_module, grm_host, grm_port = self.options.global_resource_mgr.split(':')

                conn_config.update({
                    "conn_resource" : 'grm',
                    "grm_module" : grm_module,
                    "grm_host" : grm_host,
                    "grm_port" : grm_port,
                })

            # DUT-host communication process
            args = (event_queue, dut_event_queue, conn_config)
            p = Process(target=conn_process, args=args)
            p.deamon = True
            p.start()
            return p
        p = start_conn_process()
        
        # No configuration options needed for the default event loop
        event_loop = event_loop_factory(
            {},
            'HTST',
            event_queue,
            dut_event_queue,
            p,
            self)

        return event_loop.run_loop()

    def execute(self):
        """! Test runner for host test.

        @details This function will start executing test and forward test result via serial port
                 to test suite. This function is sensitive to work-flow flags such as --skip-flashing,
                 --skip-reset etc.
                 First function will flash device with binary, initialize serial port for communication,
                 reset target. On serial port handshake with test case will be performed. It is when host
                 test reads property data from serial port (sent over serial port).
                 At the end of the procedure proper host test (defined in set properties) will be executed
                 and test execution timeout will be measured.
        """
        result = self.RESULT_UNDEF

        # hello sting with htrun version, for debug purposes
        self.logger.prn_inf(self.get_hello_string())

        try:
            # Copy image to device
            if self.options.skip_flashing:
                self.logger.prn_inf("copy image onto target... SKIPPED!")
            else:
                self.logger.prn_inf("copy image onto target...")
                result = self.mbed.copy_image()
                if not result:
                    result = self.RESULT_IOERR_COPY
                    return self.get_test_result_int(result)

            # Execute test if flashing was successful or skipped
            test_result = self.run_test()

            if test_result == True:
                result = self.RESULT_SUCCESS
            elif test_result == False:
                result = self.RESULT_FAILURE
            elif test_result is None:
                result = self.RESULT_ERROR
            else:
                result = test_result

            # This will be captured by Greentea
            self.logger.prn_inf("{{result;%s}}"% result)
            return self.get_test_result_int(result)

        except KeyboardInterrupt:
            return(-3)    # Keyboard interrupt
