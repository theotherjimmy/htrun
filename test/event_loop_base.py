#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited
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
from multiprocessing import Queue
from mock import patch, MagicMock
from mbed_host_tests.host_tests_event_loop import BaseEventLoop


class BaseEventLoopTestCase(unittest.TestCase):

    class EventLoopClassMock(BaseEventLoop):
        def __init__(self, event_queue=MagicMock(), timeout=10):
            super(BaseEventLoopTestCase.EventLoopClassMock, self).__init__(
                MagicMock(),
                event_queue,
                MagicMock(),
                MagicMock(),
                timeout_duration=timeout)

        def process_event(self, event):
            return False

        def run_finish(self):
            pass

    def setUp(self):
        self.EVENTLOOP = self.EventLoopClassMock()

    def tearDown(self):
        self.EVENTLOOP = None

    def test_register_callback(self):
        def test_callback():
            return 'test_register_callback'

        self.EVENTLOOP.register_callback('callback', test_callback)

        self.assertEqual('test_register_callback', self.EVENTLOOP.callbacks['callback']())

    def test_register_multiple_callbacks(self):
        def test_callback():
            return 'test_register_callback'
        def test_callback2():
            return 'test_register_callback2'

        self.EVENTLOOP.register_callback('callback', test_callback)
        self.EVENTLOOP.register_callback('callback2', test_callback2)

        self.assertEqual('test_register_callback', self.EVENTLOOP.callbacks['callback']())
        self.assertEqual('test_register_callback2', self.EVENTLOOP.callbacks['callback2']())

    @patch('test.event_loop_base.BaseEventLoopTestCase.EventLoopClassMock.run_finish')
    @patch('test.event_loop_base.BaseEventLoopTestCase.EventLoopClassMock.process_event')
    def test_run_loop_processes_events(self, mock_process_event, mock_run_finish):
        def mock_process_event_side_effect(event):
            return event[1]
        mock_queue = Queue()
        mock_queue.put(('Event1', True))
        mock_queue.put(('Event2', True))
        mock_queue.put(('Event3', False))

        self.EVENTLOOP.event_queue=mock_queue
        mock_process_event.side_effect = mock_process_event_side_effect
        self.EVENTLOOP.run_loop()

        mock_process_event.assert_any_call(('Event1', True))
        mock_process_event.assert_any_call(('Event2', True))
        mock_process_event.assert_any_call(('Event3', False))
        mock_run_finish.assert_called_with()

    @patch('test.event_loop_base.BaseEventLoopTestCase.EventLoopClassMock.run_finish')
    @patch('test.event_loop_base.BaseEventLoopTestCase.EventLoopClassMock.process_event')
    def test_run_loop_timeout(self, mock_process_event, mock_run_finish):
        # Force the event processing to last longer than the timeout
        def mock_process_event_side_effect(event):
            from time import sleep
            sleep(2)
            return event[1]
        mock_queue = Queue()
        mock_queue.put(('Event1', True))
        mock_queue.put(('Event2', False))

        # Set the timeout to less than the sleep
        self.EVENTLOOP.timeout_duration = 1
        self.EVENTLOOP.event_queue=mock_queue
        mock_process_event.side_effect = mock_process_event_side_effect
        self.EVENTLOOP.run_loop()

        mock_process_event.assert_any_call(('Event1', True))
        self.assertEqual(1, mock_process_event.call_count, "Loop did not time out")
        mock_run_finish.assert_called_with()

    @patch('test.event_loop_base.BaseEventLoopTestCase.EventLoopClassMock.run_finish')
    @patch('test.event_loop_base.BaseEventLoopTestCase.EventLoopClassMock.process_event')
    def test_run_loop_exceptions(self, mock_process_event, mock_run_finish):
        def mock_process_event_side_effect(event):
            raise Exception("Test Exception")
            return event[1]
        mock_queue = Queue()
        mock_queue.put(('Event1', False))
        mock_test_selector = MagicMock()
        mock_test_selector.RESULT_ERROR = "Test Return"

        self.EVENTLOOP.event_queue=mock_queue
        self.EVENTLOOP.test_selector = mock_test_selector
        mock_process_event.side_effect = mock_process_event_side_effect

        try:
            result = self.EVENTLOOP.run_loop()
            self.assertEqual("Test Return", result)
        except Exception, e:
            if str(e) == "Test Exception":
                self.fail("The main loop Exception was not caught")
            else:
                raise e
        mock_run_finish.assert_called_with()

    @patch('test.event_loop_base.BaseEventLoopTestCase.EventLoopClassMock.run_finish')
    @patch('multiprocessing.Queue')
    def test_run_loop_empty_queue(self, mock_queue, mock_run_finish):
        def mock_queue_get_side_effect(timeout):
            raise Queue.Empty("Test Empty")
        mock_queue.get.side_effect = mock_queue_get_side_effect
        mock_queue = Queue()
        mock_queue.put('Event1')

        self.EVENTLOOP.event_queue=mock_queue

        try:
            self.EVENTLOOP.run_loop()
        except QueueEmpty, e:
            if str(e) == "Test Empty":
                self.fail("The Empty Queue exception is not being caught")
            else:
                raise e
        mock_run_finish.assert_called_with()

if __name__ == '__main__':
    unittest.main()
