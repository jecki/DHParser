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


# Tasks

task release_clang, "Build a production release (macOS)":
  --verbose
  --forceBuild:on
  --cc:clang
  --define:release
  --deepcopy:on
  --cpu:arm64
  --passC:"-flto -target arm64-apple-macos14" 
  --passL:"-flto -target arm64-apple-macos14"
  --hints:off
  --outdir:"."
  setCommand "c", "src/nimparser/parse.nim"


