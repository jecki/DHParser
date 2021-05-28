#!/usr/bin/env python3

"""test_dhparser.py - tests of the dhparser.py command line tool


Author: Eckhart Arnold <arnold@badw.de>

Copyright 2017 Bavarian Academy of Sciences and Humanities

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

import os
import platform
import shutil
import subprocess
import sys
import time

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
LOG_DIR = os.path.abspath(os.path.join(scriptpath, "LOGS"))

from DHParser.testing import unique_name


def system(s: str) -> int:
    # return os.system(s)
    return subprocess.call(s, shell=True)


# TODO: make this code multiprocessing safe!
class TestDHParserCommandLineTool:
    def setup(self):
        self.cwd = os.getcwd()
        os.chdir(scriptpath)
        # avoid race-condition
        counter = 10
        while counter > 0:
            try:
                self.dirname = unique_name('test_dhparser_data')
                os.mkdir(self.dirname)
                counter = 0
            except FileExistsError:
                time.sleep(0.5)
                counter -= 1
        self.nulldevice = " >/dev/null" if platform.system() != "Windows" else " > NUL"
        self.python = sys.executable + ' '

    def teardown(self):
        name = self.dirname
        if os.path.exists(name + '/%sServer.py' % name):
            system(self.python + name + '/%sServer.py --stopserver' % name + self.nulldevice)
        if os.path.exists(name) and os.path.isdir(name):
            shutil.rmtree(name)
        if os.path.exists(name) and not os.listdir(name):
            os.rmdir(name)
        cfg_name = '%sServer.py.cfg' % name
        if os.path.exists(cfg_name):
            os.remove(cfg_name)
        os.chdir(self.cwd)
        if os.path.exists(LOG_DIR) and os.path.isdir(LOG_DIR):
            for fname in os.listdir(LOG_DIR):
                os.remove(os.path.join(LOG_DIR, fname))
            os.rmdir(LOG_DIR)
        # if os.path.exists('out') and os.path.isdir('out'):
        #     os.rmdir('out')

    def test_dhparser(self):
        name = self.dirname
        # test compiler creation and execution
        system(self.python + '../DHParser/scripts/dhparser.py ' + name + self.nulldevice)
        system(self.python + name + '/tst_%s_grammar.py --singlethread ' % name + self.nulldevice)
        system(self.python + name + '/%sParser.py ' % name + name + '/example.dsl >' + name + '/example.xml')
        with open(name + '/example.xml', 'r', encoding='utf-8') as f:
            xml = f.read()
        assert xml.find('document') >= 0, xml
        os.remove(name + '/%sParser.py' % name)
        os.remove(name + '/example.xml')
        # test server
        system(self.python + name + '/%sServer.py --stopserver' % name + self.nulldevice)
        system(self.python + name + '/%sServer.py ' % name + name + '/example.dsl >' + name + '/example.xml')
        with open(name + '/example.xml', 'r', encoding='utf-8') as f:
            json = f.read()
        assert json.find('document') >= 0, name + ' ' + str(len(json))
        system(self.python + name + '/%sServer.py ' % name + name + '/example.dsl ' + self.nulldevice)
        system(self.python + name + '/%sServer.py ' % name + name + '/example.dsl ' + self.nulldevice)
        system(self.python + name + '/%sServer.py --stopserver' % name+ self.nulldevice)


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
