## nimdoc - call nim doc safely, by eliminating the not nil annotation 
##          before running nim doc to avoid SIGSEGV illegal storage access

import std/os
import std/strutils
import std/strformat


when declared(paramStr) and declared(paramCount):
  let N = paramCount()
  if N <= 0:
    echo "Usage: nimdoc [options] filename(s)"
    quit(1)
  var
    options = newSeq[string]()
    fileNames = newSeq[string]() 
    tmpDir = fmt"{getTempDir()}nimdoc/"
  for i in countup(1, N):
    var s = paramStr(i)
    if s[0] == '-':  options.add(s)  else:  fileNames.add(s)
  discard existsOrCreateDir(tmpDir) 
  for nimFile in walkPattern("*.nim"):
    var nimSource = readFile(nimFile)
    nimSource = nimSource.multiReplace([
      ("{.experimental: \"strictNotNil\".}", "# {.experimental: \"strictNotNil\".}"),
      ("not nil", "# not nil")])
    writeFile(tmpDir & nimFile, nimSource)

  for fileName in fileNames:
    var cmd = newSeq[string]()
    cmd.add("nim")
    for opt in options:  cmd.add(opt)
    cmd.add("doc")
    cmd.add(tmpDir & fileName)
    var cmdLine = join(cmd, " ")
    var result = execShellCmd(cmdLine)
    if result != 0:
      removeDir(tmpDir)
      quit(fmt"Some error occurred while executing: {cmdLine}", result)
  let docDir = tmpDir & "htmldocs"
  copyDir(docDir, "htmldocs")
  removeDir(tmpDir)
else:
    echo "cannot read command line parameters"
