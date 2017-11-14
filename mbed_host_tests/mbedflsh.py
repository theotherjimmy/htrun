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
import argparse

from . import host_tests_plugins


def _cmd_parser_setup():
    """! Creates simple command line parser
    """
    parser = argparse.ArgumentParser(
        prog="mbedflsh",
        description="Flash mbed devices from command line using mbed-host-test"
                    " flashing plugins.")
    commands = parser.add_argument_group(title="commands")\
                     .add_mutually_exclusive_group(required=True)

    commands.add_argument('-f', '--file',
                          dest='filename',
                          help='Flash a file onto an mbed device')

    parser.add_argument("-d", "--disk",
                        dest="disk",
                        help="Target disk (mount point) path. Example: F:, /mnt/MBED",
                        metavar="DISK_PATH")

    parser.add_argument("-c", "--copy",
                        dest="copy_method",
                        default='shell',
                        choices=host_tests_plugins.get_plugin_caps('CopyMethod'),
                        help="Copy (flash the target) method selector.",
                        metavar="COPY_METHOD")

    commands.add_argument('--plugins',
                          dest='list_plugins',
                          default=False,
                          action="store_true",
                          help='Print registered plugins and exit')

    commands.add_argument('--version',
                          dest='version',
                          default=False,
                          action="store_true",
                          help='Print package version and exit')
    return parser


def main():
    """! The `mbedflsh` command flashes mbeds from command line
    """
    parser = _cmd_parser_setup()
    opts = parser.parse_args(sys.argv[1:])

    if opts.version:
        import pkg_resources
        version = pkg_resources.require("mbed-host-tests")[0].version
        print(version)
        sys.exit(0)
    elif opts.list_plugins:
        host_tests_plugins.print_plugin_info()
        sys.exit(0)
    elif opts.filename:
        print("mbedflsh: opening file %s..." % opts.filename)
        sys.exit(host_tests_plugins.call_plugin(
            'CopyMethod', opts.copy_method,
            image_path=opts.filename, destination_disk=opts.disk))
