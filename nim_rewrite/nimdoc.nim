## nimdoc - call nim doc safely, by eliminating the not nil annotation 
##          before running nim doc to avoid SIGSEGV illegal storage access

import std/os
import std/strutils
import std/strformat


when declared(paramStr) and declared(paramCount):
  let N = paramCount()
  if N <= 0:
    echo "Usage: nimdoc [options] filename"
    quit(1)
  let fileName = paramStr(N)
  var tmpDir = fmt"{getTempDir()}/nimdoc/"
  discard existsOrCreateDir(tmpDir) 
  for nimFile in walkPattern("*.nim"):
    var nimSource = readFile(nimFile)
    nimSource = nimSource.multiReplace([
      ("{.experimental: \"strictNotNil\".}", "# {.experimental: \"strictNotNil\".}"),
      ("not nil", "# not nil")])
    writeFile(tmpDir & nimFile, nimSource)
  var cmd = newSeq[string]()
  cmd.add("nim")
  for i in countup(1, N - 1):
    cmd.add(paramStr(i))
  cmd.add("doc")
  cmd.add(tmpDir & fileName)
  var cmdLine = join(cmd, " ")
  var result = execShellCmd(cmdLine)
  if result == 0:
    let docDir = tmpDir & "htmldocs"
    copyDir(docDir, ".")
    removeDir(tmpDir)
  else:
    removeDir(tmpDir)
    quit(fmt"Some error occurred while executing: {cmdLine}", result)
else:
    echo "cannot read command line parameters"
