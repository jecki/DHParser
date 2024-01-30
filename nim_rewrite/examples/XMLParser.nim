import "../src/nimparser/error"
import "../src/nimparser/nodetree"
import "../src/nimparser/parse"

{.experimental: "codeReordering".}

# document frame and prolog

let document     = "document" ::=     ?(BOM) & prolog & § element & ?(Misc) & EOF
let BOM          = "BOM" ::=          rxp"[\ufeff]|[\ufffe]|[\u0000][\ufeff]|[\ufffe][\u0000]"
let prolog       = "prolog" ::=       ?(WS & XMLDecl) & ?(Misc) & ?(doctypedecl & ?(Misc))
let XMLDecl      = "XMLDecl" ::=      txt"<?xml" & § VersionInfo & ?(EncodingDecl) & ?(SDDecl) & WS & txt"?>"

let VersionInfo  = "VersionInfo" ::=  WS & txt"version" & WS & txt"=" & WS & ((txt"'" & VersionNum & txt"'") | (txt("\"") & VersionNum & txt("\"")))
let VersionNum   = "VersionNum" ::=   rxp"[0-9]+\.[0-9]+"

let EncodingDecl = "EncodingDecl" ::= WS & txt"encoding" & WS & txt"=" & WS & ((txt"'" & EncName & txt"'") | (txt("\"") & EncName & txt("\"")))
let EncName      = "EncName" ::=      rxp"[A-Za-z][A-Za-z0-9._\-]*"

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
let STag         = "Stag" ::=         txt"<" & tagContent & txt">"
let tagContent   = "tagContent" ::=   >>!(rxp"[\/!?]") & § Name & *(WS & Attribute) & WS & >>(txt">"|txt"/>")
let ETag         = "ETag" ::=         txt"</" & § Name & WS & txt">"

let Attribute    = "Attribute" ::=    Name & WS & § txt"=" & WS & AttValue

let content      = "Content" ::=      ?(CharData) & *((element | Reference | CDSect | PI | Comment) & ?(CharData))
element.set                           (emptyElement | voidElement | (STag & content & § ETag))


# literals

let AttValue     = "AttValue" ::=     ( (txt("\"") & § *(rxp("[^<&\"]+") | Reference) & txt("\"")) |
                                        (txt"'" & § *(rxp("[^<&']+") | Reference) & txt"'") |
                                        *(rxp"[^<&'>\s]+"|Reference) )

let SystemLiteral = "SystemLiteral" ::= (txt("\"") & rxp("[^\"]*") & txt("\"")) | (txt"'" & rxp"[^']*" & txt"'")
let PubidLiteral = "PubidLiteral" ::= (txt("\"") & ?(PubidChars) & txt("\"")) | (txt"'" & (PubidCharsSingleQuoted) & txt"'")

# refernces

let Reference    = "Reference" ::=    (EntityRef | CharRef)
let EntityRef    = "EntityRef" ::=    txt"&" & Name & txt";"


# names

let Name         = "Name" ::=         NameStartChar & ?(NameChars)
let NameStartChar = "NameStartChar" ::= rxp("""_|:|[A-Z]|[a-z]
                                               |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                                               |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                                               |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                                               |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                                               |[\U00010000-\U000EFFFF]""")
let NameChars    = "NameChars" ::=    rxp"""(?:_|:|-|\.|[A-Z]|[a-z]|[0-9]
                                            |\u00B7|[\u0300-\u036F]|[\u203F-\u2040]
                                            |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                                            |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                                            |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                                            |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                                            |[\U00010000-\U000EFFFF])+"""

# comments, processing instructions and CDATA sections

let Misc        = "Misc" ::=          +(Comment | PI | S)
let Comment     = "Comment" ::=       txt"<!--" & *(CommentChars | rxp"-(?!-)") & WS & txt"-->"
let PI          = "PI" ::=            txt"<?" & PITarget & ?(WS & PIChars) & txt"?>"
let PITarget    = "PITarget" ::=      >>!(rxp"X|xM|mL|l") & Name
let CDSect      = "CDSect" ::=        txt"<![CDATA[" & CData & txt"]]>"

# characters, explicit whitespace, end of file

let PubidCharsSingleQuoted = "PubidCharsSingleQuoted" ::= rxp"(?:\x20|\x0D|\x0A|[a-zA-Z0-9]|[-()+,.\/:=?;!*#@$_%])+"
let PubidChars  = "PubidChars" ::=    rxp"(?:\x20|\x0D|\x0A|[a-zA-Z0-9]|[-'()+,.\/:=?;!*#@$_%])+"

let CharData    = "CharData" ::=      rxp"(?:(?!\]\]>)[^<&])+"
let CData       = "CData" ::=         rxp"(?:(?!\]\]>)(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]))+"

let PIChars     = "PIChars" ::=       rxp"(?:(?!\?>)(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]))+"
let CommentChars = "CommentChars" ::= rxp"(?:(?!-)(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]))+"
let CharRef     = "CharRef" ::=       (txt"&#" & rxp"[0-9]+" & txt";") | (txt"&#x" & rxp"[0-9a-fA-F]+" & txt";")

let S           = "S" ::=             rxp"\s+"
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
  let testdoc0 = """<?xml version="1.0" encoding="UTF-8"?><note></note>"""
  let testdoc1 = """
    <?xml version="1.0" encoding="UTF-8"?>
    <note date="2018-06-14">
      <to>Tove</to>
      <from>Jani</from>
      <heading>Reminder</heading>
      <body>Don't forget me this weekend!</body>
      <priority level="high" />
      <remark></remark>
      <!-- just a comment -->
    </note>
    """
  let testdoc2 = """
     <?xml version="1.0" encoding="UTF-8"?>
      <h1:DocumentSet xmlns:h1="http://www.startext.de/HiDA/DefService/XMLSchema">
        <h1:ContentInfo>
          <h1:Format>HIDA-DOC1-XML</h1:Format>
          <h1:CreationDate>26.04.2022 11:17:45</h1:CreationDate>
        </h1:ContentInfo>
        <h1:Document DocKey="Tekt    1a0e552c-b6a9-4419-b275-656720c7c3c3" CreatorID="ACTAPRO" OwnerID="ACTAPRO" CreationDate="04.01.2021 13:14:13:419" ChangeDate="10.10.2021 22:23:43:308" DocTitle="Archiv der Bayerischen Akademie der Wissenschaften">
          <h1:Block Type="Tekt">
            <h1:Field Type="Ref_Gp">
              <h1:Field Type="Ref_DocKey" Value="Arch    dd7238e4-c7a8-4b37-9332-99a58c5ed53b"/>
              <h1:Field Type="Ref_Doctype" Value="Arch"/>
              <h1:Field Type="Ref_Type" Value="P"/>
              <h1:Field Type="Ref_DocOrder" Value="74"/>
            </h1:Field>
            <h1:Field Type="ChangeUserID" Value="ACTAPRO"/>
            <h1:Field Type="CreateUserID" Value="ACTAPRO"/>
            <h1:Field Type="ChangeDate" Value="04.01.2021 13:14:17"/>
            <h1:Field Type="CreateDate" Value="04.01.2021 13:14:13"/>
            <h1:Field Type="Ar_Id" Value="Arch    dd7238e4-c7a8-4b37-9332-99a58c5ed53b"/>
            <h1:Field Type="Te_Id" Value="1a0e552c-b6a9-4419-b275-656720c7c3c3"/>
            <h1:Field Type="Te_Bez" Value="Archiv der Bayerischen Akademie der Wissenschaften"/>
            <h1:Field Type="Export_id" Value="Tekt_7ee4e113-9ce2-438a-a61b-95abc859b42b"/>
          </h1:Block>
        </h1:Document>
      </h1:DocumentSet>"""
  let testdoc3 = """<html xmlns:v="urn:schemas-microsoft-com:vml"
    xmlns:o="urn:schemas-microsoft-com:office:office"
    xmlns:w="urn:schemas-microsoft-com:office:word"
    xmlns:m="http://schemas.microsoft.com/office/2004/12/omml"
    xmlns="http://www.w3.org/TR/REC-html40">

    <head>
    <meta http-equiv=Content-Type content="text/html; charset=windows-1252">
    <meta name=ProgId content=Word.Document>
    <meta name=Generator content="Microsoft Word 15">
    <meta name=Originator content="Microsoft Word 15">
    <link rel=File-List href="F_new_files/filelist.xml">
    <!--[if gte mso 9]><xml>
     <o:OfficeDocumentSettings>
      <o:RelyOnVML/>
      <o:AllowPNG/>
      <o:RemovePersonalInformation/>
      <o:RemoveDateAndTime/>
     </o:OfficeDocumentSettings>
    </xml><![endif]-->
    <link rel=themeData href="F_new_files/themedata.thmx">
    <link rel=colorSchemeMapping href="F_new_files/colorschememapping.xml">
    <style>
    <!--
     /* Font Definitions */
     @font-face
      {font-family:Helvetica;
      panose-1:2 11 6 4 2 2 2 2 2 4;
      mso-font-charset:0;
      mso-generic-font-family:swiss;
      mso-font-pitch:variable;
      mso-font-signature:3 0 0 0 1 0;}
    @font-face
      {font-family:Courier;
      panose-1:2 7 4 9 2 2 5 2 4 4;
      mso-font-alt:"Courier New";
      mso-font-charset:0;
      mso-generic-font-family:modern;
      mso-font-pitch:fixed;
      mso-font-signature:3 0 0 0 1 0;}
    -->
    </style>
    <style>
     /* Style Definitions */
     table.MsoNormalTable
      {mso-style-name:"Table Normal";
      mso-tstyle-rowband-size:0;
      mso-tstyle-colband-size:0;
      mso-style-noshow:yes;
      mso-style-priority:99;
      mso-style-parent:"";
      mso-padding-alt:0cm 5.4pt 0cm 5.4pt;
      mso-para-margin:0cm;
      mso-para-margin-bottom:.0001pt;
      mso-pagination:widow-orphan;
      font-size:10.0pt;
      font-family:"Times New Roman",serif;
      mso-ansi-language:DE;
      mso-fareast-language:DE;}
    </style>
    </head>

    <body lang=EN-US link=blue vlink="#954F72" style='tab-interval:35.45pt'>

    <div class=WordSection1>

    <p class=MsoNormal style='text-indent:6.5pt;line-height:normal;mso-pagination:
    none'><b style='mso-bidi-font-weight:normal'><span style='mso-ansi-language:
    EN-US'>f</span></b><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><i style='mso-bidi-font-style:normal'><span style='letter-spacing:
    .25pt;mso-ansi-language:EN-US'>littera</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>sexta</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>alphabeti</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>Latini</span></i><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'><span style='mso-spacerun:yes'>  </span></span><span
    class=jofu2><span style='font-size:8.0pt;mso-bidi-font-size:10.0pt;font-family:
    "Arial",sans-serif;mso-bidi-font-family:"Times New Roman";color:#0070C0;
    letter-spacing:0pt;mso-ansi-language:EN-US'>Weber</span></span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'><span
    style='mso-spacerun:yes'>  </span></span><b style='mso-bidi-font-weight:normal'><span
    style='mso-ansi-language:EN-US'>1</span></b><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>gener.</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>(ad</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>significandum</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>punctum</span></i><i style='mso-bidi-font-style:normal'><span
    style='letter-spacing:-1.75pt;mso-ansi-language:EN-US'>:</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><!--[if supportFields]><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'><span
    style='mso-element:field-begin'></span></span></i><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'><span
    style='mso-spacerun:yes'> </span>GOTOBUTTON F15m_1</span></i><![endif]--><!--[if supportFields]><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'><span
    style='mso-element:field-end'></span></span></i><![endif]--><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>l</span></i><i style='mso-bidi-font-style:normal'><span
    style='letter-spacing:-.75pt;mso-ansi-language:EN-US'>.</span></i><i
    style='mso-bidi-font-style:normal'><span style='mso-fareast-font-family:"Yu Gothic";
    letter-spacing:-1.75pt;mso-ansi-language:EN-US'> </span></i><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>5)</span></i><i style='mso-bidi-font-style:normal'><span
    style='letter-spacing:-1.75pt;mso-ansi-language:EN-US'>:</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Consuet</span><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>Trev.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>32</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>vasa</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>per</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>digamma,</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>id</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>est</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>F,</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>signata.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='text-transform:uppercase;
    letter-spacing:.5pt;mso-ansi-language:EN-US'>Herm.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Augiens</span><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>mens.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>astrolab.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>p.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>204,36</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>ex</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>his</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>quinque</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>partibus</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;mso-ansi-language:EN-US'>iiii</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>utrinque</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>circa</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>C</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>secerne</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>et</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>punctis</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>superius</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>F<a name="F15m_1"></a>,</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>inferius</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>G</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>inscribe</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:normal'><span
    style='letter-spacing:.25pt;mso-ansi-language:EN-US'>eqs</span></i><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='text-transform:uppercase;
    letter-spacing:.5pt;mso-ansi-language:EN-US'>Chron</span><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>reg.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>a.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>1162</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>p.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>109,44</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>(rec.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>II,</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>codd.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>B1,</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>B2,</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>C2)</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>duo</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>gamma</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>esse</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>F,</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>primam</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>litteram</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>nominis</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>Friderici</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>imperatoris.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Conr.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Mur</span><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>summ.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>p.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>142,23</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>Fridericus</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>per</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>capitales</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>F</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>et</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>R</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>cum</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>titella</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>(sc.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>breviatur)</span></i><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'>[MFSP]</span><b style='mso-bidi-font-weight:
    normal'><span style='mso-ansi-language:EN-US'>2</span></b><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>mus.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>(de</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>re</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>v.</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>LexMusLat.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>vol.</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>II.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>s.</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>v.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>‘f’)</span></i><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:-1.75pt;
    mso-ansi-language:EN-US'>:</span></i><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'>[MFSP]</span><b style='mso-bidi-font-weight:normal'><span
    style='mso-ansi-language:EN-US'>a</span></b><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>de</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>littera</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>significativa</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>neumatibus</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>addita</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>(‘Romanusbuchstabe’)</span></i><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:-1.75pt;mso-ansi-language:EN-US'>:</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Notker.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Balb</span><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>ad</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>Lantb.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>p.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>35</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>f,</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>ut</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>cum</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>fragore</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>seu</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>frendore</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>feriatur,</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>efflagitat</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>(<i style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt'>item</span></i></span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Frutolf.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>[?]</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>brev.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>14</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>p.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>103,2).</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'>[MFSP]</span><b style='mso-bidi-font-weight:normal'><span
    style='mso-ansi-language:EN-US'>b</span></b><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>ad</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>tonos</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>significandos</span></i><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:-1.75pt;
    mso-ansi-language:EN-US'>:</span></i><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='text-transform:uppercase;
    letter-spacing:.5pt;mso-ansi-language:EN-US'>Ps.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='text-transform:uppercase;
    letter-spacing:.5pt;mso-ansi-language:EN-US'>Odo</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='text-transform:uppercase;
    letter-spacing:.5pt;mso-ansi-language:EN-US'>Clun</span><span style='mso-ansi-language:
    EN-US'>.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>dial.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>2</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>p.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>253</span><span
    style='font-size:7.0pt;mso-bidi-font-size:10.0pt;position:relative;top:-2.0pt;
    mso-text-raise:2.0pt;mso-ansi-language:EN-US'>b</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'><span style='mso-spacerun:yes'> </span></span><span
    style='mso-ansi-language:EN-US'>scribe</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='letter-spacing:2.25pt;
    mso-ansi-language:EN-US'>..</span><span style='mso-ansi-language:EN-US'>.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>pro</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>F</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>aliam</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>f.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='text-transform:uppercase;
    letter-spacing:.5pt;mso-ansi-language:EN-US'>Comm</span><span style='mso-ansi-language:
    EN-US'>.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>microl.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>70</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>p.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>105</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>a</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>voce</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>D</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>in</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>F</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>est</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>semiditonus.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>333</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>p.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>119</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>in</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>diapason</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>F</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>f.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><i style='mso-bidi-font-style:normal'><span style='letter-spacing:
    .25pt;mso-ansi-language:EN-US'>saepe.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>v.</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>et</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>vol.</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>III.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>p.</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>1,13</span></i><span style='mso-ansi-language:EN-US'>.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'>[MFSP]</span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>in</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>mensura</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>cymbalorum</span></i><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:-1.75pt;mso-ansi-language:EN-US'>:</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Theoph</span><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>sched.</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>3,86</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>p.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>158,23</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>dividat</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>(sc.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>quicumque</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>vult</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>facere</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>cymbala)</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>ceram</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>G</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>per</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>octo</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>et</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>tantum</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>det</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>F</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>litterae,</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>quantum</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>est</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>in</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>summa</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>eius</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>(sc.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span lang=DE style='letter-spacing:.25pt'>G)</span></i><span lang=DE
    style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>et</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>insuper</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>octavam</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>eius</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>partem.</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Cymbala</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>I</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>4</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>accipe</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>totum</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>E</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>et</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>eius</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='text-transform:uppercase;
    mso-ansi-language:EN-US'>viii</span><span style='font-size:7.0pt;mso-bidi-font-size:
    10.0pt;position:relative;top:-2.0pt;mso-text-raise:2.0pt;mso-ansi-language:
    EN-US'>am</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'><span style='mso-spacerun:yes'> </span></span><span style='mso-ansi-language:
    EN-US'>partem</span><span style='mso-fareast-font-family:"Yu Gothic";
    mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:EN-US'>et</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='mso-ansi-language:EN-US'>fac</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>F</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><i style='mso-bidi-font-style:normal'><span style='letter-spacing:
    .25pt;mso-ansi-language:EN-US'>eqs</span></i><span style='mso-ansi-language:
    EN-US'>.</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><i style='mso-bidi-font-style:normal'><span style='letter-spacing:
    .25pt;mso-ansi-language:EN-US'>ibid.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>al</span></i><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'>[MFSP]</span><b style='mso-bidi-font-weight:
    normal'><span style='mso-ansi-language:EN-US'>3</span></b><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>math.</span></i><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:.25pt;mso-ansi-language:EN-US'>numerum</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='text-transform:uppercase;
    letter-spacing:.25pt;mso-ansi-language:EN-US'>xl</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt;
    mso-ansi-language:EN-US'>significans</span></i><i style='mso-bidi-font-style:
    normal'><span style='letter-spacing:-1.75pt;mso-ansi-language:EN-US'>:</span></i><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    style='text-transform:uppercase;letter-spacing:.5pt;mso-ansi-language:EN-US'>Carm</span><span
    style='mso-ansi-language:EN-US'>.</span><span style='mso-fareast-font-family:
    "Yu Gothic";mso-ansi-language:EN-US'> </span><span style='mso-ansi-language:
    EN-US'>de</span><span style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:
    EN-US'> </span><span style='mso-ansi-language:EN-US'>litt.</span><span
    style='mso-fareast-font-family:"Yu Gothic";mso-ansi-language:EN-US'> </span><span
    lang=DE>7</span><span lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span
    lang=DE>sexta</span><span lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span
    lang=DE>quater</span><span lang=DE style='mso-fareast-font-family:"Yu Gothic"'>
    </span><span lang=DE>decem</span><span lang=DE style='mso-fareast-font-family:
    "Yu Gothic"'> </span><span lang=DE>gerit</span><span lang=DE style='mso-fareast-font-family:
    "Yu Gothic"'> </span><span lang=DE>F,</span><span lang=DE style='mso-fareast-font-family:
    "Yu Gothic"'> </span><span lang=DE>que</span><span lang=DE style='mso-fareast-font-family:
    "Yu Gothic"'> </span><span lang=DE>distat</span><span lang=DE style='mso-fareast-font-family:
    "Yu Gothic"'> </span><span lang=DE>ab</span><span lang=DE style='mso-fareast-font-family:
    "Yu Gothic"'> </span><span lang=DE>alpha;</span><span lang=DE style='mso-fareast-font-family:
    "Yu Gothic"'> </span><span lang=DE style='text-transform:uppercase'>xxxx</span><span
    lang=DE>.</span><span lang=DE style='mso-fareast-font-family:"Yu Gothic"'>[MFSP]</span><b
    style='mso-bidi-font-weight:normal'><span lang=DE>4</span></b><span lang=DE
    style='mso-fareast-font-family:"Yu Gothic"'> </span><i style='mso-bidi-font-style:
    normal'><span lang=DE style='letter-spacing:.25pt'>comput.</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>ad</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>significandam</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>litteram</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>dominicalem</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>(‘Sonntagsbuchstabe’;</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>de</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>re</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>v.</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>H.</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>Grotefend,</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>Taschenbuch</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>der</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>Zeitrechnung.</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='font-size:7.0pt;
    mso-bidi-font-size:10.0pt;position:relative;top:-2.0pt;mso-text-raise:2.0pt;
    letter-spacing:.25pt'>14</span><span lang=DE style='letter-spacing:.25pt'>2007.</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>p.</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>4.</span></i><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><i
    style='mso-bidi-font-style:normal'><span lang=DE style='letter-spacing:.25pt'>134sq.)</span><span
    lang=DE style='letter-spacing:-1.75pt'>:</span></i><span lang=DE
    style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE
    style='text-transform:uppercase;letter-spacing:.5pt'>Liber</span><span lang=DE
    style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>ordin.</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>Rhenaug.</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>p.</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>241,27</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>in</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>eo</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE
    style='letter-spacing:2.25pt'>..</span><span lang=DE>.</span><span lang=DE
    style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>anno,</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>cum</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>dies</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>dominica</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>in</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>f</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>evenerit</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>(<i
    style='mso-bidi-font-style:normal'><span style='letter-spacing:.25pt'>sim</span></i>.</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>p.</span><span
    lang=DE style='mso-fareast-font-family:"Yu Gothic"'> </span><span lang=DE>241,36).</span></p>

    </div>
    </body>
    </html>
    """

  # let res = prolog("""<?xml version="1.0" encoding="UTF-8"?>""")
  # let res = element("""<note></note>""")
  # let res = document("""<?xml version="1.0" encoding="UTF-8"?><note></note>""")
  # let res = document(testdoc1)
  # let res = element("""<h1:DocumentSet xmlns:h1="http://www.startext.de/HiDA/DefService/XMLSchema">
  #                     </h1:DocumentSet>""")
  # let res = element("""<h1:ContentInfo>
  #         <h1:Format>HIDA-DOC1-XML</h1:Format>
  #        <h1:CreationDate>26.04.2022 11:17:45</h1:CreationDate>
  #       </h1:ContentInfo>""")
  # let res = element("""<h1:Field Type="Ref_DocKey" Value="Arch    dd7238e4-c7a8-4b37-9332-99a58c5ed53b"/>""")
  # let res = document(testdoc2)
  # let res = STag("""<body lang=EN-US link=blue vlink="#954F72" style='tab-interval:35.45pt'>""")
  var res: EndResult
  try:
    res = element("""<span
      style='mso-spacerun:yes'>  </span>""")
  except ParsingException as pe:
    echo $pe
  # let res = document(testdoc3)
  for e in res.errors:
    echo $e
  echo $res.root.asSxpr()
  echo "ready."
