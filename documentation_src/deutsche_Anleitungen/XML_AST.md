XML AST und Datenbaum
=====================

Ein kleines Beispiel zur Verdeutlichung des Unterschiedes zwischen dem
(abstrakten oder konkreten) Syntax-Baum und der Struktur der in diesem Baum
kodierten Daten. Insbesondere wenn letztere wiederum eine Baumstruktur ist, kann
es leicht zu verwechselungen kommen.


XML-Beispiel-Dokument
---------------------

Als Ausganspunkt sei folgendes XML-Beispiel-Dokument gewählt:

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


Die Grammatik von XML
---------------------

Die Grammatik von XML ist in der EBNF-Notation beschrieben auf
<https://www.w3.org/TR/xml/>. Hier ein Ausschnitt: 

    element	       ::= EmptyElemTag | STag content ETag
    STag	       ::= '<' Name (S Attribute)* S? '>'
    Attribute	   ::= Name Eq AttValue
    ETag           ::= '</' Name S? '>'
    content	       ::= CharData? ((element | Reference | CDSect | PI | Comment) CharData?)*
    EmptyElemTag   ::= '<' Name (S Attribute)* S? '/>'

Die Definitionen (auch "Produktionen" genannt) der in diesem Ausschnitt referierten
Symbols wie "Name", "AttValue", "CharData" finden sich an anderer Stelle in der
Grammatik und sind hier nicht wiedergegeben. S für Leerraum, d.h. ein oder mehrere 
Leerzeichen oder Zeilenwechsel.


Der abstrakte Syntaxbaum
------------------------

Parst man diese Dokument, mit einem Parser, der aus der offiziellen
XML-Grammatik <https://www.w3.org/TR/xml/> generiert worden ist, so
könnte der abstrakte Syntaxbaum (AST) wie folgt so aussehen. ("könnte", weil der
AST durch Bereinigungen und Vereinfachungen aus konkreten Syntaxbaum 
entsteht, wobei es große Freiheiten dabei gibt, welche Bereinigungen
man vornimmt.)  Der abstrakte Syntaxbaum wird hier als S-Ausdruck 
serialisiert, weil das etwas übersichtlicher ist als XML und um 
Verwechselungen mit dem Daten-XML zu vermeiden.:

    (document
      (XMLDecl
        (VersionInfo "1.0")
        (EncodingDecl "UTF-8"))
      (element
        (STag
          (Name "note")
          (Attribute
            (Name "date")
            (AttValue "2018-06-14")))
        (content
          (CharData
            ""
            "  ")
          (element
            (STag
              (Name "to"))
            (content
              (CharData "Tove"))
            (ETag
              (Name "to")))
          (CharData
            ""
            "  ")
          (element
            (STag
              (Name "from"))
            (content
              (CharData "Jani"))
            (ETag
              (Name "from")))
          (CharData
            ""
            "  ")
          (element
            (STag
              (Name "heading"))
            (content
              (CharData "Reminder"))
            (ETag
              (Name "heading")))
          (CharData
            ""
            "  ")
          (element
            (STag
              (Name "body"))
            (content
              (CharData "Don't forget me this weekend!"))
            (ETag
              (Name "body")))
          (CharData
            ""
            "  ")
          (element
            (emptyElement
              (Name "priority")
              (Attribute
                (Name "level")
                (AttValue "high"))))
          (CharData
            ""
            "  ")
          (element
            (STag
              (Name "remark"))
            (content)
            (ETag
              (Name "remark")))
          (CharData
            ""
            "  ")
          (Comment " just a comment ")
          (CharData
            ""
            ""))
        (ETag
          (Name "note"))))


Wie man sieht, besteht der Syntaxbaum des "to"-elements aus einem Wurzelknoten
mit dem Tag-Namen "element", einem "STag"-Knoten" und einem "ETag"-Knoten. In XML
würde das so aussehen:

    <element>
        <STag>
            <Name>to</Name>
            <content>
                <CharData>Tove</CharData>
            </content>
        </STag>
        <ETag>
            <Name>to</Name>
        </ETag>
    </element>

Wie man sieht, hat der Syntaxbaum des XML-Schnipsels `<to>Tove</to>` eine
andere und sehr viel kompliziertere Struktur als der Schnispel selbst.

Die Datenstruktur muss also in jedem Fall erst durch eine Transformation
aus dem Syntaxbaum abgeleitet werden. Z.B. durch folgenden 
einfachen und naheliegenden Algorithmus möglich:

    def on_element(self, node):
        if len(node.children) == 1:
            return self.on_emptyElement(node['emptyElement'])
        stag = node['STag']
        tag_name = stag['Name'].content

        assert node['ETag']['Name'].content == tag_name, \
            "Namen des öffnenden und schließenden Tags stimmen nicht überein!"

        node.tag_name = tag_name
        node.result = self.compile(node['content']) if 'content' in node else tuple()
        return node

Der Datenbaum
-------------

Der nach der Transformation gewonnene Datenbaum sieht so aus: 

    (:XML
      (?xml `(version "1.0") `(encoding "UTF-8"))
      (note `(date "2018-06-14")
        (to
          "Tove"
        )
        (from
          "Jani"
        )
        (heading
          "Reminder"
        )
        (body
          "Don't forget me this weekend!"
        )
        (priority `(level "high"))
        (remark)
        (!--
          " just a comment "
        )
      )
    )

Da entspricht dem ursprünglichen XML bis auf das umschließende `:XML`-tag. Bei
letzterem handelt es sich um eine Artefakt von DHParser
<https://gitlab.lrz.de/badw-it/DHParser>, weil die Baumverarbeitungsroutinen von
DHParser verlagen, das jedes Dokument genau eine Wurzel hat. (Vgl.
<https://dhparser.readthedocs.io/en/latest/manuals/nodetree.html>) Diese Tag
kann bei der Serialierung als XML einfach weggelassen werden.

Unklarheit des Begriffs "AST"
-----------------------------

Man kann den Begriff "AST" auch so verwenden, dass der zuletzt gezeigte
"Datenbaum" als der abstrakte Syntaxbaum bezeichnet wird, und der zuvor gezeigte
"AST" als (bereinigter) konkreter Syntaxbaum. Der AST wäre dann der erste im
Sinne der Anwendungsdomäne nutzbare Baum, der aus dem Parsing-Vorgang und null
oder mehr weiteren Transformationen gewonnen wurde. 

Das würde der Bedeutung des Begriffs "AST" bei Programmiersprachen eher
entsprechen, wo der AST eine Struktur darstellt, die zumindes im Prinzip schon
durch einen Interpreter ausführbar wäre und so gesehen schon das lauffähige 
Programm repräsentiert. Vgl. <https://dhparser.readthedocs.io/en/latest/manuals/transform.html>