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

from time import time
from conn_primitive_serial import SerialConnectorPrimitive
from conn_primitive_remote import RemoteConnectorPrimitive

def conn_primitive_factory(conn_resource, config, event_queue, logger):
    """! Factory producing connectors based on type and config
    @param conn_resource Name of connection primitive (e.g. 'serial' for
           local serial port connection or 'grm' for global resource manager)
    @param event_queue Even queue of Key-Value protocol
    @param config Global configuration for connection process
    @param logger Host Test logger instance
    @return Object of type <ConnectorPrimitive> or None if type of connection primitive unknown (conn_resource)
    """
    if conn_resource == 'serial':
        # Standard serial port connection
        # Notify event queue we will wait additional time for serial port to be ready

        # Get extra configuration related to serial port
        port = config.get('port')
        baudrate = config.get('baudrate')
        serial_pooling = int(config.get('serial_pooling', 60))

        logger.prn_inf("notify event queue about extra %d sec timeout for serial port pooling"%serial_pooling)
        event_queue.put(('__timeout', serial_pooling, time()))

        logger.prn_inf("initializing serial port listener... ")
        connector = SerialConnectorPrimitive(
            'SERI',
            port,
            baudrate,
            config=config)
        return connector

    elif conn_resource == 'grm':
        # Start GRM (Gloabal Resource Mgr) collection

        # Get extra configuration related to remote host
        remote_pooling = int(config.get('remote_pooling', 30))

        # Adding extra timeout for connection to remote resource host
        logger.prn_inf("notify event queue about extra %d sec timeout for remote connection"%remote_pooling)
        event_queue.put(('__timeout', remote_pooling, time()))

        logger.prn_inf("initializing global resource mgr listener... ")
        connector = RemoteConnectorPrimitive(
            'GLRM',
            config=config)
        return connector

    else:
        logger.pn_err("unknown connection resource!")
        raise NotImplementedError("ConnectorPrimitive factory: unknown connection resource '%s'!"% conn_resource)
        return None
