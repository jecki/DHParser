import "../src/nimparser/parse"


# document frame and prolog

let document     = "document" ::=     ?(BOM) & prolog & § element ?(Misc) EOF
let BOM          = "BOM" ::=          rxp"[\ufeff]|[\ufffe]|[\u0000feff]|[\ufffe0000]"
let prolog       = "prolog" ::=       ?(WS & XMLDecl) & ?(Misc) & ?(doctypedecl ?(Misc))
let XMLDelc      = "XMLDecl" ::=      txt"<?xml" & § VersionInfo & ?(EncodingDecl) & ?(SDDecl) & WS & txt"?>"

let VersionInfo  = "VersionInfo" ::=  WS & txt"version" & WS & txt"=" & WS & ((txt"'" & VersionNum & txt"'") | (txt"\"" & VersionNum & txt"\""))
let VersionNum   = "VersionNum" ::=   rxp"[0-9]+\.[0-9]+"

let EncodingDecl = "EncodingDecl" ::= WS & txt"encoding" & WS & txt"=" & WS & ((txt"'" & EncName & txt"'") | (txt"\"" & EncName & txt"\""))
let EncName      = "EncName" ::=      rxp"[A-Za-z][A-Za-z0-9._\-]*"

let SDDecl       = "SDDecl" ::=       WS & txt"standalone" & WS & txt"=" & WS & ((txt"'" & (txt"yes" | txt"no") & txt"'") | (txt"\"" & (txt"yes" | txt"no") & txt"\""))


# document type definition stub

let doctypedecl  = "doctypedecl" ::=  txt"<!DOCTYPE" & WS & § Name & ?(WS & ExternalID) & WS & txt">"
let ExternalID   = "ExternalID"  ::=  (txt"SYSTEM" & § WS & SystemLiteral) | (txt"Piblic" & § WS & PubidLiteral & WS & SystemLiteral)


# logical structures

let element      = "element" ::=      emptyElement | voidElement | (STag & content & § ETag)
let emptyElement = "emptyElement" ::= txt"<" & tagContent & "/>"
let voidElement  = "voidElement" ::=  txt"<" & >>(ic"area" | ic"base" | ic"br" | ic"col" | ic"embed" | ic"hr" |
                                                  ic"img" | ic"inpu" | ic"link" | ic"meta" | ic"param" |
                                                  ic"source" | ic"track" | ic"wbr") & tagContent & txt">"
let STag         = "Stag" ::=         txt"<" & tagContent & txt">"
let tagContent   = "tagContent" ::=   >>!(rxp"[\/!?]") & § Name & *(WS & Attribute) & WS & >>(txt">"|txt"\>")
let ETag         = "ETg" ::=          txt"<" & § Name & WS & txt">"

let Attribute    = "Attribute" ::=    Name & WS & § txt"=" & WS & AttValue

let content      = "Content" ::=      ?(CharData) & *((element | Referencer | CDSect | PI | Comment) & ?(CharData))


# literals

let AttValue     = "AttValue" ::=     ((txt"\"" & *(rxp"[^<&\"]+") | Reference) & txt"\"" |
                                       (txt"'" & *(rxp"[^<&\"]+") | Reference) & txt"'" |
                                       *(rxp"[^<&'>\s]+" | Reference)

let SystemLiteral = "SystemLiteral" ::= (txt"\"" & rxp"[^\"]*" & txt"\"") | (txt"'" & rxp"[^\']*" & txt"'")
let PubidLiteral = "PubidLiteral" ::= (txt"\"" & ?(PubidChars) & txt"\"") | (txt"'" & (PubidCharsSingleQuoted) & txt"'")

# refernces

let Reference    = "Reference" ::=    (EntityRef | CharRef)
let EntityRef    = "EntityRef" ::=    txt"&" & Name & txt";"


# names

let Name         = "Name" ::=         NameStartChar & ?(NameChars)
let NameStartChar = "NameStartChar ::= rxp"""_|:|[A-Z]|[a-z]
                                             |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                                             |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                                             |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                                             |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                                             |[\U00010000-\U000EFFFF]"""
let NameChars    = "NameChars" ::=    rxp"""(?:_|:|-|\.|[A-Z]|[a-z]|[0-9]
                                            |\u00B7|[\u0300-\u036F]|[\u203F-\u2040]
                                            |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                                            |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                                            |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                                            |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                                            |[\U00010000-\U000EFFFF])+"""


when isMainModule:
  echo "hi"
