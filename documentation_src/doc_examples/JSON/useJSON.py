#!/usr/bin/env python3

"""useJSON.py - an example script for how to import and
                use a generated parser from whing a
                Python-script
"""

import sys
import JSONParser


example_json = """
{ "Phonebook" : 
  [ 
    { "Name": "Peter Smith",
      "Phone": "123 456" },
    { "Name": "Sally Bean",
      "Phone": "654 321" }
  ]
}
"""

def parse_phonebook(json_str):
    result, errors = JSONParser.compile_src(json_str)
    if errors:
        raise ValueError("\n".join(str(e) for e in errors))
    return result

def read_phonebook_from_disk(file_name):
    result_file_name = file_name + ".parsed"
    error_file_name = JSONParser.process_file(file_name, result_file_name)
    if error_file_name:
        raise ValueError(f'Errors in {file_name}! '
            f'Messages written to {error_file_name}')
    else:
        print("")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        read_phonebook_from_disk(sys.argv[1])
    else:
        print(parse_phonebook(example_json))
