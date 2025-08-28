#!/bin/sh

cd ~/Entwicklung/DHParser
rm -r experimental/mock
python3 DHParser/scripts/dhparser.py experimental/mock
cd experimental/mock
python3 ./tst_mock_grammar.py
