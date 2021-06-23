#! /usr/bin/python

import sys, os

try:
    cmdName = (os.path.split(sys.argv[0])[1])[:7]
    if cmdName == "iso2utf":
        table = { "\xe4": "\xc3\xa4",
                  "\xf6": "\xc3\xb6",
                  "\xfc": "\xc3\xbc",
                  "\xc4": "\xc3\x84",
                  "\xd6": "\xc3\x96",
                  "\xdc": "\xc3\x9c",
                  "\xdf": "\xc3\x9f" }
        
    elif cmdName == "utf2iso":
        table = { "\xc3\xa4": "\xe4",
                  "\xc3\xb6": "\xf6",
                  "\xc3\xbc": "\xfc",
                  "\xc3\x84": "\xc4",
                  "\xc3\x96": "\xd6",
                  "\xc3\x9c": "\xdc",
                  "\xc3\x9f": "\xdf" }

    else: raise IndexError

    fName = sys.argv[1]; bckName = fName+"."+cmdName
    os.rename(fName, bckName)
    src = file(bckName, "r")
    dst = file(fName, "w")
    for line in src:
        for key, value in table.iteritems():
            line = line.replace(key, value)
        dst.write(line)
    src.close()
    dst.close()
    
                  
except IndexError:
    print "Usage: iso2utf FILE"
    print "       utf2iso FILE"
except IOError:
    print "IO Error encountered!"



