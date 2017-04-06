#!/usr/bin/python3

"""logs.py - basic log file support for DHParser

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.


Module ``logs`` defines the global variable LOGGING which contains
the name of a directory where log files shall be placed. By setting
its value to the empty string "" logging can be turned off.

To read the directory name function ``LOGS_DIR()`` should be called
rather than reading the variable LOGGING. ``LOGS_DIR()`` makes sure
the directory exists and raises an error if a file with the same name
already exists.
"""

import os


__all__ = ['logging_on', 'logging_off', 'LOGGING', 'LOGS_DIR']


LOGGING: str = "LOGS"  # LOGGING = "" turns logging off!


def logging_on(log_subdir="LOGS"):
    "Turns logging of syntax trees and parser history on."
    global LOGGING
    LOGGING = log_subdir


def logging_off():
    "Turns logging of syntax trees and parser history off."
    global LOGGING
    LOGGING = ""


def LOGS_DIR() -> str:
    """Returns a path of a directory where log files will be stored.
    
    The default name of the logging directory is taken from the LOGGING
    variabe (default value 'LOGS'). The directory will be created if it
    does not exist. If the directory name does not contain a leading
    slash '/' it will be created as a subdirectory of the current
    directory Any files in the logging directory can be overwritten!
    
    Raises:
        AssertionError if logging has been turned off 
    Returns:
        name of the logging directory
    """
    global LOGGING
    if not LOGGING:
        raise AssertionError("Cannot use LOGS_DIR() if logging is turned off!")
    dirname = LOGGING
    if os.path.exists(LOGGING):
        if not os.path.isdir(LOGGING):
            raise IOError('"' + LOGGING + '" cannot be used as log directory, '
                                          'because it is not a directory!')
    else:
        os.mkdir(LOGGING)
    info_file_name = os.path.join(LOGGING, 'info.txt')
    if not os.path.exists(info_file_name):
        with open(info_file_name, 'w') as f:
            f.write("This directory has been created by DHParser to store log files from\n"
                    "parsing. ANY FILE IN THIS DIRECTORY CAN BE OVERWRITTEN! Therefore,\n"
                    "do not place any files here or edit existing files in this directory\n"
                    "manually.\n")
    return dirname
