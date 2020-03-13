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
                os.mkdir('test_dhparser_data')
                counter = 0
            except FileExistsError:
                time.sleep(1)
                counter -= 1
        self.nulldevice = " >/dev/null" if platform.system() != "Windows" else " > NUL"
        self.python = sys.executable + ' '

    def teardown(self):
        if os.path.exists('test_dhparser_data/neu/neuServer.py'):
            system(self.python + 'test_dhparser_data/neu/neuServer.py --stopserver' + self.nulldevice)
        if os.path.exists('test_dhparser_data/neu') and os.path.isdir('test_dhparser_data/neu'):
            shutil.rmtree('test_dhparser_data/neu')
        if os.path.exists('test_dhparser_data') and not os.listdir('test_dhparser_data'):
            os.rmdir('test_dhparser_data')
        os.chdir(self.cwd)
        if os.path.exists(LOG_DIR) and os.path.isdir(LOG_DIR):
            for fname in os.listdir(LOG_DIR):
                os.remove(os.path.join(LOG_DIR, fname))
            os.rmdir(LOG_DIR)

    def test_dhparser(self):
        # test compiler creation and execution
        system(self.python + '../DHParser/scripts/dhparser.py test_dhparser_data/neu ' + self.nulldevice)
        system(self.python + 'test_dhparser_data/neu/tst_neu_grammar.py ' + self.nulldevice)
        system(self.python + 'test_dhparser_data/neu/neuParser.py test_dhparser_data/neu/example.dsl '
                  '>test_dhparser_data/neu/example.xml')
        with open('test_dhparser_data/neu/example.xml', 'r', encoding='utf-8') as f:
            xml = f.read()
        assert xml.find('document') >= 0, xml
        os.remove('test_dhparser_data/neu/neuParser.py')
        os.remove('test_dhparser_data/neu/example.xml')

        # test server
        system(self.python + 'test_dhparser_data/neu/neuServer.py --stopserver' + self.nulldevice)
        system(self.python + 'test_dhparser_data/neu/neuServer.py test_dhparser_data/neu/example.dsl '
                  '>test_dhparser_data/neu/example.xml')
        with open('test_dhparser_data/neu/example.xml', 'r', encoding='utf-8') as f:
            json = f.read()
        assert json.find('document') >= 0, json
        system(self.python + 'test_dhparser_data/neu/neuServer.py test_dhparser_data/neu/example.dsl ' + self.nulldevice)
        system(self.python + 'test_dhparser_data/neu/neuServer.py test_dhparser_data/neu/example.dsl ' + self.nulldevice)
        system(self.python + 'test_dhparser_data/neu/neuServer.py --stopserver' + self.nulldevice)
        pass



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
