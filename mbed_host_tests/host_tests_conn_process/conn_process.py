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

from multiprocessing import Process
from mbed_host_tests.host_tests_conn_process import run_default_conn_process

def conn_process_factory(logger, options, mbed, event_queue, dut_event_queue, conn_process_name="greentea-client"):
    
    if conn_process_name == "greentea-client":
        logger.prn_inf("initializing greentea-client connection process... ")
        
        # DUT-host communication process
        args = (
            'CONN',
            options,
            mbed,
            event_queue,
            dut_event_queue)

        p = Process(target=run_default_conn_process, args=args)
        p.deamon = True
        p.start()
        return p
    else:
        logger.prn_err("unknown connection process!")
        raise NotImplementedError("Connection Process Factory: unknown connection process '%s'!" % conn_process_name)
