import re
rx = re.compile(r'''(?:(?P<t1>theod\.)(?P<w1>(?:[ \t]*(?:\n[ \t]*(?![ \t]*\n))?)?))(?:(?P<t2>inf\.)(?P<w2>(?:[ \t]*(?:\n[ \t]*(?![ \t]*\n))?)?)?)(?:(?P<t3>vet\.)(?P<w3>(?:[ \t]*(?:\n[ \t]*(?![ \t]*\n))?)?)?)''')
