#!/usr/bin/python3

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
import sys

sys.path.extend(['../', './'])

scriptdir = os.path.dirname(os.path.realpath(__file__))

class TestDHParserCommandLineTool:
    def setup(self):
        self.cwd = os.getcwd()
        os.chdir(scriptdir)
        if not os.path.exists('testdata'):
            os.mkdir('testdata')
        self.nulldevice = " >/dev/null" if platform.system() != "Windows" else " > NUL"
        self.python = 'python3 ' if os.system('python3 -V' + self.nulldevice) == 0 else 'python '

    def teardown(self):
        if os.path.exists('testdata/neu/neuServer.py'):
            os.system(self.python + 'testdata/neu/neuServer.py --stopserver' + self.nulldevice)
        if os.path.exists('testdata/neu') and os.path.isdir('testdata/neu'):
            shutil.rmtree('testdata/neu')
        if os.path.exists('testdata') and not os.listdir('testdata'):
            os.rmdir('testdata')
        os.chdir(self.cwd)

    def test_dhparser(self):
        # test compiler creation and execution
        os.system(self.python + '../DHParser/scripts/dhparser.py testdata/neu ' + self.nulldevice)
        os.system(self.python + 'testdata/neu/tst_neu_grammar.py ' + self.nulldevice)
        os.system(self.python + 'testdata/neu/neuCompiler.py testdata/neu/example.dsl '
                  '>testdata/neu/example.xml')
        with open('testdata/neu/example.xml', 'r', encoding='utf-8') as f:
            xml = f.read()
        assert xml.find('<document>') >= 0, xml
        os.remove('testdata/neu/neuCompiler.py')
        os.remove('testdata/neu/example.xml')

        # test server
        os.system(self.python + 'testdata/neu/neuServer.py --stopserver')
        os.system(self.python + 'testdata/neu/neuServer.py testdata/neu/example.dsl '
                  '>testdata/neu/example.xml')
        with open('testdata/neu/example.xml', 'r', encoding='utf-8') as f:
            json = f.read()
        assert json.find('document') >= 0, json
        os.system(self.python + 'testdata/neu/neuServer.py testdata/neu/example.dsl '
                  '>testdata/neu/example.xml')



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
