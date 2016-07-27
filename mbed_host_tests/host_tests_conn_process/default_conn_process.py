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

import uuid
from time import time
from Queue import Empty as QueueEmpty
from mbed_host_tests.host_tests_logger import HtrunLogger
from mbed_host_tests.host_tests_parser import parser_factory
from mbed_host_tests.host_tests_conn_proxy import conn_primitive_factory

def run_default_conn_process(
    logger_name,
    options,
    mbed,
    event_queue,
    dut_event_queue):
    """! Function which represents the conn process
    @param logger_name Name of the logger which will be created
    @param options Global options specififed from the command line
    @param mbed Details on the devices and their connections
    @param event_queue Queue of events to process
    @param dut_event_queue Queue for sending events
    @return Int representing the exit status of the process
    """
    
    # Create device info here as it may change after restart.
    config = {
        "digest" : "serial",
        "port" : mbed.port,
        "baudrate" : mbed.serial_baud,
        "program_cycle_s" : options.program_cycle_s,
        "reset_type" : options.forced_reset_type,
        "target_id" : options.target_id,
        "serial_pooling" : options.pooling_timeout,
        "forced_reset_timeout" : options.forced_reset_timeout,
        "sync_behavior" : options.sync_behavior,
        "platform_name" : options.micro,
        "image_path" : mbed.image_path,
    }

    if options.global_resource_mgr:
        grm_module, grm_host, grm_port = options.global_resource_mgr.split(':')

        config.update({
            "conn_resource" : 'grm',
            "grm_module" : grm_module,
            "grm_host" : grm_host,
            "grm_port" : grm_port,
        })

    logger = HtrunLogger(logger_name)
    logger.prn_inf("starting default connection process...")

    # Configuration of conn_opriocess behaviour
    sync_behavior = int(config.get('sync_behavior', 1))
    sync_timeout = config.get('sync_timeout', 1.0)
    conn_resource = config.get('conn_resource', 'serial')

    # Create connector instance with proper configuration
    connector = conn_primitive_factory(conn_resource, config, event_queue, logger)
    # Create simple buffer we will use for Key-Value protocol data
    buffer = parser_factory({}, logger)

    # List of all sent to target UUIDs (if multiple found)
    sync_uuid_list = []

    # We will ignore all kv pairs before we get sync back
    sync_uuid_discovered = False

    # Some RXD data buffering so we can show more text per log line
    print_data = str()

    def __send_sync(timeout=None):
        sync_uuid = str(uuid.uuid4())
        # Handshake, we will send {{sync;UUID}} preamble and wait for mirrored reply
        if timeout:
            logger.prn_inf("resending new preamble '%s' after %0.2f sec"% (sync_uuid, timeout))
        else:
            logger.prn_inf("sending preamble '%s'"% sync_uuid)
        connector.write_kv('__sync', sync_uuid)
        return sync_uuid

    # Send simple string to device to 'wake up' greentea-client k-v parser
    connector.write("mbed" * 10, log=True)

    # Sync packet management allows us to manipulate the way htrun sends __sync packet(s)
    # With current settings we can force on htrun to send __sync packets in this manner:
    #
    # * --sync=0        - No sync packets will be sent to target platform
    # * --sync=-10      - __sync packets will be sent unless we will reach
    #                     timeout or proper response is sent from target platform
    # * --sync=N        - Send up to N __sync packets to target platform. Response
    #                     is sent unless we get response from target platform or
    #                     timeout occur

    if sync_behavior > 0:
        # Sending up to 'n' __sync packets
        logger.prn_inf("sending up to %s __sync packets (specified with --sync=%s)"% (sync_behavior, sync_behavior))
        sync_uuid_list.append(__send_sync())
        sync_behavior -= 1
    elif sync_behavior == 0:
        # No __sync packets
        logger.prn_wrn("skipping __sync packet (specified with --sync=%s)"% sync_behavior)
    else:
        # Send __sync until we go reply
        logger.prn_inf("sending multiple __sync packets (specified with --sync=%s)"% sync_behavior)
        sync_uuid_list.append(__send_sync())
        sync_behavior -= 1

    loop_timer = time()
    while True:

        # Check if connection is lost to serial
        if not connector.connected():
            error_msg = connector.error()
            connector.finish()
            event_queue.put(('__notify_conn_lost', error_msg, time()))
            break

        # Send data to DUT
        try:
            (key, value, _) = dut_event_queue.get(block=False)
        except QueueEmpty:
            pass # Check if target sent something
        else:
            # Return if state machine in host_test_default has finished to end process
            if key == '__host_test_finished' and value == True:
                logger.prn_inf("received special event '%s' value='%s', finishing"% (key, value))
                connector.finish()
                return 0
            connector.write_kv(key, value)

        data = connector.read(2048)
        if data:

            # We want to print RXD data with nice line division in log
            print_data += data
            print_data_lines = print_data.split('\n')
            if print_data_lines:
                if data.endswith('\n'):
                    for line in print_data_lines:
                        if line:
                            logger.prn_rxd(line)
                            event_queue.put(('__rxd_line', line, time()))
                    print_data = str()
                else:
                    for line in print_data_lines[:-1]:
                        if line:
                            logger.prn_rxd(line)
                            event_queue.put(('__rxd_line', line, time()))
                    print_data = print_data_lines[-1]

            # Stream data stream KV parsing
            buffer.append(data)
            while buffer.search():
                key, value, timestamp = buffer.get_kv()

                if sync_uuid_discovered:
                    event_queue.put((key, value, timestamp))
                    logger.prn_inf("found KV pair in stream: {{%s;%s}}, queued..."% (key, value))
                else:
                    if key == '__sync':
                        if value in sync_uuid_list:
                            sync_uuid_discovered = True
                            event_queue.put((key, value, time()))
                            idx = sync_uuid_list.index(value)
                            logger.prn_inf("found SYNC in stream: {{%s;%s}} it is #%d sent, queued..."% (key, value, idx))
                        else:
                            logger.prn_err("found faulty SYNC in stream: {{%s;%s}}, ignored..."% (key, value))
                    else:
                        logger.prn_wrn("found KV pair in stream: {{%s;%s}}, ignoring..."% (key, value))

        if not sync_uuid_discovered:
            # Resending __sync after 'sync_timeout' secs (default 1 sec)
            # to target platform. If 'sync_behavior' counter is != 0 we
            # will continue to send __sync packets to target platform.
            # If we specify 'sync_behavior' < 0 we will send 'forever'
            # (or until we get reply)

            if sync_behavior != 0:
                time_to_sync_again = time() - loop_timer
                if time_to_sync_again > sync_timeout:
                    sync_uuid_list.append(__send_sync(timeout=time_to_sync_again))
                    sync_behavior -= 1
                    loop_timer = time()

    return 0
