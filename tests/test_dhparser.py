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
import random
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


class TestDHParser:
    def test_selftest(self):
        if os.getcwd().replace('\\', '/').rstrip('/').endswith('/DHParser'):
            sys.path.append('./DHParser/scripts/')
        else:
            sys.path.append('../DHParser/scripts/')
        import dhparser
        assert dhparser.selftest(silent=True)


TEST_GRAMMAR = """# Arithmetic-grammar

@ whitespace  = vertical             # implicit whitespace, includes any number of line feeds
@ literalws   = right                # literals have implicit whitespace on the right hand side
@ comment     = /#.*/                # comments range from a '#'-character to the end of the line
@ ignorecase  = False                # literals and regular expressions are case-sensitive
@ drop        = whitespace, strings  # drop anonymous whitespace

expression = term  { (PLUS | MINUS) term}
term       = factor { (DIV | MUL) factor}
factor     = [sign] (NUMBER | VARIABLE | group) { VARIABLE | group }
sign       = POSITIVE | NEGATIVE
group      = "(" expression ")"

PLUS       = "+"
MINUS      = "-"
MUL        = "*"
DIV        = "/"

POSITIVE   = /[+]/      # no implicit whitespace after signs
NEGATIVE   = /[-]/

NUMBER     = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
VARIABLE   = /[A-Za-z]/~
"""


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
                self.dirname = ''
                time.sleep(random.random())
                counter -= 1
        assert self.dirname
        self.nulldevice = " >/dev/null" if platform.system() != "Windows" else " > NUL"
        self.python = sys.executable + ' '

    def teardown(self):
        # return
        name = self.dirname
        if os.path.exists(os.path.join(name, '%sServer.py' % name)):
            system(self.python + os.path.join(name, '%sServer.py --stopserver' % name)
                   + self.nulldevice)
        # time.sleep(0.1)
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

    def test_dhparser_project_test(self):
        name = self.dirname
        # test compiler creation and execution
        system(self.python + os.path.join('..', 'DHParser', 'scripts', 'dhparser.py ')
               + name + self.nulldevice)
        system(self.python + os.path.join(name, 'tst_%s_grammar.py --singlethread ' % name)
               + self.nulldevice)
        system(self.python + os.path.join(name, '%sParser.py ' % name)
               + os.path.join(name, 'example.dsl --xml >') + os.path.join(name, 'example.xml'))
        with open(os.path.join(name, 'example.xml'), 'r', encoding='utf-8') as f:
            xml = f.read()
        assert xml.find('document') >= 0, xml
        os.remove(os.path.join(name, '%sParser.py' % name))
        os.remove(os.path.join(name, 'example.xml'))
        # test server
        system(self.python + os.path.join(name, '%sServer.py ' % name)
               + os.path.join(name, 'example.dsl >') + os.path.join(name, 'example.json'))
        with open(os.path.join(name, 'example.json'), 'r', encoding='utf-8') as f:
            json = f.read()
        assert json.find('document') >= 0, name + ' ' + str(len(json))
        system(self.python + os.path.join(name, '%sServer.py ' % name) +
               os.path.join(name, '/example.dsl ') + self.nulldevice)
        system(self.python + os.path.join(name, '%sServer.py ' % name) +
               os.path.join(name, '/example.dsl ') + self.nulldevice)
        system(self.python + os.path.join(name, '%sServer.py --stopserver' % name)
               + self.nulldevice)
        os.remove(os.path.join(name, '%sServer.py' % name))
        time.sleep(0.1)  # MS Windows needs a little break here...

    def test_dhparser_compiler_generation_and_batch_processing(self):
        name = self.dirname
        with open(os.path.join(name, 'Arithmetic.ebnf'), 'w', encoding='utf-8') as f:
            f.write(TEST_GRAMMAR)
        system(self.python + '../DHParser/scripts/dhparser.py '
               + os.path.join(name, 'Arithmetic.ebnf') + self.nulldevice)
        assert os.path.exists(os.path.join(name, 'ArithmeticParser.py'))
        system(self.python + os.path.join(name, 'ArithmeticParser.py')
               + ' "2 + 3 * 4" ' + self.nulldevice)
        save = os.getcwd()
        os.chdir(name.lstrip())
        os.mkdir('in')
        for i in range(10):
            with open(os.path.join('in', f'data_{i}.txt'), 'w') as f:
                f.write(f'2 / (4 * -5 + {i})\n')
        system(self.python + ' ArithmeticParser.py' + ' in')
        result_list = os.listdir('out')
        result_list.sort()
        assert result_list == ['data_0.sxpr', 'data_1.sxpr', 'data_2.sxpr', 'data_3.sxpr',
                               'data_4.sxpr', 'data_5.sxpr', 'data_6.sxpr', 'data_7.sxpr',
                               'data_8.sxpr', 'data_9.sxpr']
        os.chdir(save)

    def test_dhparser_tst_script_error_report(self):
        name = self.dirname
        # test compiler creation and execution
        system(self.python + os.path.join('..', 'DHParser', 'scripts', 'dhparser.py ')
               + name + self.nulldevice)
        for fname in os.listdir(name):
            if fname.endswith('.ebnf'):
                ebnf_name = fname
                break
        else:
            raise AssertionError('No .ebnf-file found !?')
        ebnf = """# this ebnf-code has errors:\n€€"""
        with open(os.path.join(name, ebnf_name), 'w', encoding='utf-8') as f:
            f.write(ebnf)
        system(self.python + os.path.join(name, 'tst_%s_grammar.py --singlethread ' % name)
               + self.nulldevice)
        for fname in os.listdir(name):
            if fname.endswith('_MESSAGES.txt'):
                break
        else:
            raise AssertionError('No "..._MESSAGES.txt - file found!')
        time.sleep(0.1)  # MS Windows needs a little break here...

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
