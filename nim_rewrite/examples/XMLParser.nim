import std/[paths, strutils]
when not defined(js):
  import std/[dirs]

# import nimprof

import "../src/nimparser/error"
import "../src/nimparser/nodetree"
import "../src/nimparser/parse"

{.experimental: "codeReordering".}

# document frame and prolog

let document     = "document" ::=     ?(BOM) & prolog & § element & ?(Misc) & EOF
let BOM          = "BOM" ::=          cr"[\ufeff]|[\ufffe]|[\u0000][\ufeff]|[\ufffe][\u0000]"
let prolog       = "prolog" ::=       ?(WS & XMLDecl) & ?(Misc) & ?(doctypedecl & ?(Misc))
let XMLDecl      = "XMLDecl" ::=      txt"<?xml" & § VersionInfo & ?(EncodingDecl) & ?(SDDecl) & WS & txt"?>"

let VersionInfo  = "VersionInfo" ::=  WS & txt"version" & WS & txt"=" & WS & ((txt"'" & VersionNum & txt"'") | (txt("\"") & VersionNum & txt("\"")))
let VersionNum   = "VersionNum" ::=   cr"[0-9]+" & txt"." & cr"[0-9]+"

let EncodingDecl = "EncodingDecl" ::= WS & txt"encoding" & WS & txt"=" & WS & ((txt"'" & EncName & txt"'") | (txt("\"") & EncName & txt("\"")))
let EncName      = "EncName" ::=      cr"[A-Za-z]" & cr"[A-Za-z0-9._\-]*"

let SDDecl       = "SDDecl" ::=       WS & txt"standalone" & WS & txt"=" & WS & ((txt"'" & (txt"yes" | txt"no") & txt"'") | (txt("\"") & (txt"yes" | txt"no") & txt("\"")))


# document type definition stub

let doctypedecl  = "doctypedecl" ::=  txt"<!DOCTYPE" & WS & § Name & ?(WS & ExternalID) & WS & txt">"
let ExternalID   = "ExternalID"  ::=  (txt"SYSTEM" & § WS & SystemLiteral) | (txt"Piblic" & § WS & PubidLiteral & WS & SystemLiteral)


# logical structures

let element      = "element" ::=      Forward()
let emptyElement = "emptyElement" ::= txt"<" & tagContent & txt"/>"
let voidElement  = "voidElement" ::=  txt"<" & >>(ic"area" | ic"base" | ic"br" | ic"col" | ic"embed" | ic"hr" |
                                                  ic"img" | ic"inpu" | ic"link" | ic"meta" | ic"param" |
                                                  ic"source" | ic"track" | ic"wbr") & tagContent & txt">"
let STag         = "STag" ::=         txt"<" & tagContent & txt">"
let tagContent   = "tagContent" ::=   >>!(cr"[/!?]") & § Name & *(WS & Attribute) & WS & >>(txt">"|txt"/>")
let ETag         = "ETag" ::=         txt"</" & § Name & WS & txt">"

let Attribute    = "Attribute" ::=    Name & WS & § txt"=" & WS & AttValue

let content      = "Content" ::=      ?(CharData) & *((element | Reference | CDSect | PI | Comment) & ?(CharData))
element.set                           (emptyElement | voidElement | (STag & content & § ETag))


# literals

let AttValue     = "AttValue" ::=     ( (txt("\"") & § *(cr("[^<&\"]+") | Reference) & txt("\"")) |
                                        (txt"'" & § *(cr("[^<&']+") | Reference) & txt"'") |
                                        *(cr"[^<&'>\s]+"|Reference) )

let SystemLiteral = "SystemLiteral" ::= (txt("\"") & cr("[^\"]*") & txt("\"")) | (txt"'" & cr"[^']*" & txt"'")
let PubidLiteral = "PubidLiteral" ::= (txt("\"") & ?(PubidChars) & txt("\"")) | (txt"'" & (PubidCharsSingleQuoted) & txt"'")

# refernces

let Reference    = "Reference" ::=    (EntityRef | CharRef)
let EntityRef    = "EntityRef" ::=    txt"&" & Name & txt";"


# names

let Name         = "Name" ::=         NameStartChar & ?(NameChars)
let NameStartChar = "NameStartChar" ::= cr("""[_:]|[A-Z]|[a-z]
                                               |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                                               |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                                               |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                                               |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                                               |[\U00010000-\U000EFFFF]""")
let NameChars    = "NameChars" ::=    cr"""([_:.-]|[A-Z]|[a-z]|[0-9]
                                            |[\u00B7]|[\u0300-\u036F]|[\u203F-\u2040]
                                            |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                                            |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                                            |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                                            |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                                            |[\U00010000-\U000EFFFF])+"""

# comments, processing instructions and CDATA sections

let Misc        = "Misc" ::=          +(Comment | PI | S)
let Comment     = "Comment" ::=       txt"<!--" & *(CommentChars | (txt"-" & >>!(txt"-"))) & WS & txt"-->"
let PI          = "PI" ::=            txt"<?" & PITarget & ?(WS & PIChars) & txt"?>"
let PITarget    = "PITarget" ::=      >>!(ic"XML") & Name
let CDSect      = "CDSect" ::=        txt"<![CDATA[" & CData & txt"]]>"

# characters, explicit whitespace, end of file

let PubidCharsSingleQuoted = "PubidCharsSingleQuoted" ::= cr"([\x20\x0D\x0A]|[a-zA-Z0-9]|[-()+,.\/:=?;!*#@$_%])+"
let PubidChars  = "PubidChars" ::=    cr"([\x20\x0D\x0A]|[a-zA-Z0-9]|[-'()+,.\/:=?;!*#@$_%])+"

let CharData    = "CharData" ::=      +(cr"[^<&\]]+" | +(>>!(txt"]]>") & txt"]"))
let CData       = "CData" ::=         +(cr"([\x09\x0A\x0D]|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF])+" | +(>>!(txt"]]>") & txt"]"))


let PIChars     = "PIChars" ::=       *(cr"([\x09\x0A\x0D]|[\u0020-\u003E]|[\u0040-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF])+" | rxp"\?(?!>)")
let CommentChars = "CommentChars" ::= cr"([\x09\x0A\x0D]|[\u0020-\u002C]|[\u002E-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF])+"
let CharRef     = "CharRef" ::=       (txt"&#" & cr"[0-9]+" & txt";") | (txt"&#x" & cr"[0-9a-fA-F]+" & txt";")

let S           = "S" ::=             cr"[\s]+"
let WS          = ":WS" ::=           Drop(Whitespace(r"\s*", ""))  # Drop
let EOF         = "EOF" ::=           >>! rxp"."

DropStrings(document)

tagContent.error(anyPassage, "syntax error in tag-name of opening or empty tag:  {1}")
tagContent.resume(atRe"(?=>|\/>)")
ETag.error(anyPassage, "syntax error in tag-name of closing tag:  {1}")
ETag.resume(atRe"(?=>)")
Attribute.error(anyPassage, "syntax error in attribute definition:  {1}")
Attribute.resume(atRe"(?=>|\/>)")

# characters


when isMainModule:
  when defined amd64:
    echo "amd64"
  elif defined x86:
    echo "x86 !?"
  else:
    echo "probably arm"

  # when defined(js):
  import K
  let source = KSource

  # else:
  #   let d = getCurrentDir().string
  #   echo $d
  #   if d.endsWith("/DHParser"):
  #     setCurrentDir(Path("nim_rewrite/examples"))
  #   let source = readFile("K.html")

  # echo "+++"
  # let tst = Comment("""<!-- abc -->""")
  # echo tst.root.asSxpr
  # echo $tst.errors
  # echo $Comment
  # echo "+++"

  echo $source.len
  let res = document(source)
  echo "---"
  # echo res.root.asSxpr()
  echo "---"
  for e in res.errors:
    echo $e
    echo ""


