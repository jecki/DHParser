# Package

version       = "0.1.0"
author        = "eckhart"
description   = "A rewrite of DHParser.parse and parts of DHParser.nodetree in nim to drastically increase parsing speed"
license       = "Apache-2.0"
srcDir        = "src"
binDir        = "bin"
installExt    = @["nim"]
bin           = @["nimparserpkg"]


# Dependencies

requires "nim >= 2.0.0"
