#!/usr/bin/python

import os, re

CHUNK_SIZE = 50
MAX_PAGES  = 300

input_name = "Promotion.dvi"
output_prefix = "Diss"


page = 0
while page < MAX_PAGES:
    even = re.sub(" ","",str(range(page, page + CHUNK_SIZE, 2))[1:-1])
    odd = re.sub(" ","",str(range(page+1, page + CHUNK_SIZE, 2))[1:-1])

    pagenr = re.sub(" ","0","%3i"%page)
    
    even_name = output_prefix + pagenr + "e.pdf"
    odd_name = output_prefix + pagenr + "o.pdf"

    print "processing pages: %i - %i" % (page, page+CHUNK_SIZE-1)

    even_call = "dvipdfm -o pdfs/%s  -s %s  %s" % (even_name, even, input_name)
    odd_call = "dvipdfm -o pdfs/%s  -s %s  %s" % (odd_name, odd, input_name)
    
    os.system(even_call)
    os.system(odd_call)
    
    page += CHUNK_SIZE
    
