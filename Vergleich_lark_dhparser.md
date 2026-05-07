Vergleich zwischen lark und DHParser
====================================

Die Parsergeneratoren [lark](https://lark-parser.readthedocs.io/) und [DHParser](https://dhparser.readthedocs.io/) ähneln sich in ziemlich stark und liefern, obwohl praktisch vollkommen unabhängig voneinander entwickelt, zum Teil ähnliche Lösungen für typische Herausforderungen von Rahmenwerken für domänenspezifische Sprachen (DSL für "domain specific language"). Im Detail gibt es natürlich eine Reihe von Unterschieden.

Ansatz
------

Sowohl lark als auch DHParser basieren im Kern auf einem Parser-Generator. Dabei schreibt man die Grammatik der formalen Sprache in einer Variante von EBNF, was sehr viel klarer und konziser ist als wenn man sie in einem handgeschriebenen Parser im Programmcode codiert oder, wie bei pyparsing, in einer internen DSL aus Python-Funktionsaufrufen vorgefertigter Parser-Bausteine programmiert. Die EBNF-Grammatik wird bei lark und DHParser in ein Python-Programm zum einlesen ("parsen") von Text in der durch die Grammatik festgelegten Sprache übersetzt ("Stand-Alone-Parser").

Die Philosophie von lark ([link](https://lark-parser.readthedocs.io/en/stable/philosophy.html)) entspricht weitgehend der von DHParser (keine Beschreibung dazu). lark nimmt den Nutzer etwas stärker bei der Hand, DHParser nur, wenn er das möchte (in der Voreinstellung etwas weniger als lark).


Umfang
------

* Überblick zu lark: [link](https://lark-parser.readthedocs.io/en/stable/features.html)

* Überblick zu DHParser: [link](https://dhparser.readthedocs.io/en/latest/Overview.html)

lark ist vor allem ein Parser-Generator, DHParser ist ein vollständiges ("full-stack") DSL-Entwicklungs-Rahmenwerk, das über den Parser-Generator und Hilfsfunktionen bei der Syntax-Baum-Transformation (die bei DHParser vegleichsweise [umfangreicher ausgebaut](https://dhparser.readthedocs.io/en/latest/Overview.html#an-internal-mini-dsl-for-ast-transformation) sind) hinaus noch folgende Komponenten anbietet:

1. Ein Test-Rahmenwerk, das die Test-getriebene Grammatik-Entwicklung erleichtert. [-> link](https://dhparser.readthedocs.io/en/latest/manuals/05_testing.html)

2. Einen Post-Mortem-Debugger für den Parser, der auch automatische für alle gescheiterten Tests ausgelöst wird. [-> link](https://dhparser.readthedocs.io/en/latest/Overview.html#debugger-included)

3. Ein Rahmenwerk für einfache oder verzweigte Datentransformations-Fließbänder. [-> link](https://dhparser.readthedocs.io/en/latest/manuals/04_postprocessing.html#processing-pipelines)

4. Unterstüzung für die Fehlerbehandlung in einer DSL. [-> link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#error-catching)

5. Unterstützung für Serverbetrieb und rudimentäre Unterstützung für das [Language Server Protokoll](https://microsoft.github.io/language-server-protocol/). [-> link](https://dhparser.readthedocs.io/en/latest/Overview.html#language-server-support) 


Parser-Typen
------------

lark unterstützt drei Parsetypen: Earley (kann aus jeder Grammatik einen parser bauen, einschließlich mehrdeutiger Grammatiken, benötigt ggf. quadratische oder, bei mehrdeutigen Grammatiken, kubische Rechenzeit), LALR(1) (relativ eingeschränkter, aber mit linearer Rechenzeit) und CYK (kann auch alle Grammatiken verarbeiten, aber meist nur mit kubischer Rechenzeit).

DHParser unterstützt nur "Parsing Expression Grammars" (lineare Rechenzeit). Damit kann man jede nicht links-rekursive Grammatik verarbeiten (bei DHParser zusätzlich einige einfache Fälle von Linksrekursion), aber keine mehrdeutigen Grammatiken (die man bei DSLs aber eigentlich auch gar nicht gebrauchen kann).

Das fundamentale Paper zu PEGs (wegen der Speicherung der Zwischenergebnisse, die die lineare Zeit ermöglicht, gerne auch "Packrat Parser" genannt) stammt von Brian Ford ([link](https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf)). Das ist die Kurzfassung seiner Magisterarbeit zu dem Thema ([link](https://pdos.csail.mit.edu/~baford/packrat/thesis/thesis.pdf)). Weitere Literatur hat er auf einer Website [verlinkt](https://bford.info/packrat/). Die jüngste, sehr interessante Weiterentwicklung, könnte der Squirell Parser von Luke Hutchinson sein. [link](https://github.com/lukehutch/squirrelparser/blob/main/paper/squirrel_parser.pdf).

Lark kann sowohl scannerlos arbeiten, wobei "Terminale" dann durch reguläre Ausdrücke definiert (oder in reguläre Ausdrücke umgewandelt) werden, als auch auch mit einem externen Scanner bzw. "Lexer" kombiniert werden. Lark unterscheidet relativ scharf zwischen Terminalen und anderen Symbolen, wobei die Namen für die Terminale groß geschrieben werden müssen und Terminale u.a. dadurch definiert sind, dass sie keine Baum-Struktur sondern immer einen komplette String zurückliefern.

DHParser arbeitet immer scannerlos. Terminale werden durch reguläre Ausdrücke definiert. Bei DHParser gibt es keine so scharfe Unterscheidung zwischen Terminalen und anderen Konstrukten. Man kann Symbole, die nicht durch einen einzigen regulären Ausdruck definiert werden, wie Terminale handhaben, indem man bei der Transformation vom konkreten in den abstrakten Syntax-Baum den von ihnen erfassten Teilbaum durch den Eintrag "collapse" im Transformations-Verzeichnis platt macht. 

Scannerlose Parser haben den Vorteil, dass man mit Ihnen ganz gut auch Dokumente erfassen kann, in denen mehrere formale Sprachen gemischt auftreten, wie z.B. Website-Templates, die in HTML mit einer eingebetteten Template-Sprache geschrieben werden. Ein vorgeschalteter Lexer/Scanner wüsste, da er nicht durch die Grammatik gesteuert wird, nicht, wann er die Regeln der einen, wann die der anderen Sprache anwenden sollte.

Ob es auch Vorteile der Aufteiliung in Parser und Scanner/Lexer gegenüber scannerlosen Parsern gibt, oder ob das nur ein alter Zopf ist, weiß ich nicht.


Ausdrucksstärke der Grammatik
-----------------------------

Sowohl lark als auch DHparser unterstützen für die Kodierung der Grammatik EBNF mit ein paar Extras, wobei sich die Extras weitgehend überschneiden, auch wenn sie jeweils etwas anders realisiert werden. Zu diesen Extras gehören folgende:

* _Frühzeitige Vereinfachung des Syntax-Baums_ durch automatische bzw. konventionsbasierte Streichung von Trennzeichen, insignifikanten Leerzeichen und Kommentaren, Reduktion von (anonymen) Knoten, die nur ein Kind-Element enthalten, Zusammenlegung gleichartiger benachbarter Knoten (z.B. aufeinander folgende Zeichen gleicher semantischer Kategorie zu Zeichenketten) etc.. Bei lark sind diese Vereinfachungstechniken größtenteils fest eingebaut und weniger konfigurierbar, dafür allerdings auch klarer und einfacher ([link](https://lark-parser.readthedocs.io/en/stable/tree_construction.html#tree-construction-reference)). Bei DHParser lässt sich das flexibler anpassen, dafür ist es aber auch etwas komplizierter ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#simplifying-syntax-trees-while-parsing)).

   Auf die Details wie diese Vereinfachungen jeweils in dem einen System oder anderen System in der Grammatik kodiert werden gehe ich hier nicht ein, sondern beschränke mich, um einen Eindruck zu geben, nur auf ein Beispiel. Um Textbestandteile ohne eigenen Knoten einzulesen (lark nennt das "inlining") verwendet Lark die Konvention, dass dem zugehörigen Symbol in der Grammatik ein Unterstrich vorangestellt wird:

           start: "(" _greet ")"
          _greet: /\w+/ /\w+/ 

    liefert auf "hello world" angewandt:

          (start "hello world")

    DHParser würde statt dessen den vollständigen Baum zurückliefern:
          
          (start (_greet "hello world"))

    Es sei denn, man fügt am Anfang der Grammatik eine entsprechende Direktive ein:

           @hide = /_\\w+/

           start = "(" _greet ")"
           _greet = /\w+/ /\w+/ 

    Der reguläre Ausdruck nach "hide" wird auf die Namen des Symbole angewandt. Trifft er zu (fullmatch), so produziert das entsprechende Symbol, falls möglich keinen eigenen Knoten. 

    Unter Lark gibt es noch eine weitere Kennzeichnung für "inlining", nämlich ein dem Symbol vorangestelltes Fragezeichen: `?greet: `. Das Fragezeichen legt allerdings eine etwas schwächere Inlining-Regel fest als der Unterstrich, indem der Knoten nur bei einem einzelnen Kindknoten entfernt wird! 
    
    Bei DHParser kann man alternativ zu der oben beschriebenen "@hide"-Direktive auch in der Grammatik direkt vor das Symbol den Modifikator "HIDE" schreiben: `HIDE:greet = `. Der "HIDE"-Modifikator entspricht jedoch nicht dem Fragezeichen von lark, sondern hat genau dieselbe Wirkung wir die "@hide"-Direktive bzw. der Unterstrich bei lark. Will man das Verhalten der Fragezeichen-Markierung von lark erzielen, so kann man das mit der "@reduction"-direktive am Anfang der Grammatik steuern ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#simplifying-syntax-trees-while-parsing)) und natürlich immer in einem zweiten Schritt bei der Baum-Vereinfachung, die bei DHParser "AST-Transformation" genannt wird; gemeint ist dabei die Transformation des konkreten Syntaxbaums (CST) in den bzw. einen abstrakten Syntaxbaum (AST). 

* _Vorausschau und bedingtes Parsen_ wir von lark, soweit ich sehen kann, nur in der einfachen Form der Vorausschau eines Tokens (LALR(1)) angeboten ([link](https://lark-parser.readthedocs.io/en/latest/parsers.html#parsers)). DHParser bietet die bei PEGs übliche, beliebig weite positive oder negative Vorschau, wie man sie auch von regulären Ausdrücken kennt, und mit der sich eine einfache Form von Bedingungen in der Grammatik "programmieren" lässt ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#lookahead-and-lookbehind)), und dazu noch eine - zugegebenermaßen recht idiosynkratische - Form die positiven oder negativen Rückschau mit regulären Ausdrücken.

* _Schablonen_ werden sowohl von lark ([link](https://lark-parser.readthedocs.io/en/stable/grammar.html#templates)) als auch von DHParser angeboten, wo sie Makros genannt werden ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#macros)). ("Schablonen" ist eigentlich der passendere Name, da es sich in beiden Fällen nur um eine sehr einfache substitutionsbasierte Makrosprache handelt.)

* Die _Verknüpfung von Grammatiken bzw. Grammatikquelltexten_ bieten auch beide Pakete an. DHParser tut das lediglich durch einen einfachen include-Mechanismus ohne Namensräume ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#chaining-grammars-with-include)), während lark einen etwas leistungsfähigeres import-system anbietet ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#macros)). Der einfacheren Lösung von DHParser liegt der Gedanke zu Grunde, dass Grammatiken in der Regel nicht so komplex werden (sollten), dass man sie auf mehrere Quelltexte verteilen muss. Und zwischen unterschiedlichen DSL-Projekten ist es sowieso ungefährlicher den (wenigen) gemeinsamen Code per Kopieren und Einsetzen zu teilen als durch einen import aus einer gemeinsamen Quelle.

Ein Extra, das nur Lark anbietet ist die explizite Angabe von Prioritäten für die Produktionen der Grammatik ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#chaining-grammars-with-include)). Allerdings ist dies auch durch die Art der Parser bedingt, die Prioritäten zur Auflösung von Ambiguitäten (Earley) oder Kollisionen (LALR) benötigen. Bei DHParser ergibt sich die Priorität aus der Struktur der Grammatik. Ambiguitäten oder Kollisionen können bei Parsing Expression Grammars prinzipbedingt nicht auftreten.

Über die folgenden Extras verfügt allerdings **nur DHParser**:

* _Fehlerunterstützung_ und zwar für die Lokalisierung von Fehlern, künstliches Auslösen von Fehlern und die Generierung aussagekräftiger Fehlermeldungen und für fehlertolerante Parser, das nicht mit dem ersten Syntax-Fehler abbrechen. Die Verwendung der letzten beiden Mechanismen kann kompliziert sein, aber zumindest gibt es Unterstützung dafür. ([Fehlerbehandlung](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#error-catching) und [Fortführung nach Fehler](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#error-catching))

* _Kontext-sensitive Parser_, die es erlauben in einfacher und beschränkter Form auf schon eingelesenen Text zurück zu greifen - ähnlich wie man bei regulären Ausdrücken im selben Ausdruck auf den Inhalt von Gruppen zurückgreifen kann. Der Mechanismus deckt einige wenige Anwendungsfälle von "semantischen Aktionen" ab, die man aus klassichen Compiler-Parsergeneratoren kennt, und sprengt das Paradigma der kontext-sensitiven Sprachen sowie der Parsing Expression Grammars. Insbesondere kann damit die Garantie linearer Rechenzeit nicht mehr eingehalten werden. 

* _Eigene Parser in Python-code_, mit denen man die vorgegeben Parser-Operatoren ([link](https://dhparser.readthedocs.io/en/latest/Reference.html#ebnf-reference)) erweitern kann und im Prinzip sogar semantische Aktionen realisieren könnte ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#custom-parsers)).


Verbindungen zur "Außenwelt"
----------------------------

Beide Frameworks bieten eine gewisse Unterstützung für fremde Grammatiken. So unterstützt lark [Nearly.js](https://dhparser.readthedocs.io/en/latest/Reference.html#ebnf-reference)-Grammatiken ([link](https://lark-parser.readthedocs.io/en/latest/tools.html#importing-grammars-from-nearley-js)). DHParser kann im "heuristic"-Modus eine ganze Reihe unterschiedlicher Syntax-Varianten von EBNF verarbeiten ([link](https://gitlab.lrz.de/badw-it/DHParser/-/tree/master/examples/FlexibleEBNF)), u.a. auch die von lark (allerdings ohne Direktiven und ohne die vom EBNF-Standard leicht abweichende Semantik von lark voll zu erfassen). DHParser bietet daneben einen Direkt-Export der eigenen Baumstrukturen nach elementtree/lxml und umgekehrt den dazugehörigen Import ([link](https://dhparser.readthedocs.io/en/latest/manuals/02_document-trees.html#elementtree-exchange)), außerdem Serialisierung und (De-Serialisierung) als S-Ausdruck (auch in der Variante SXML), XML/HTML und JSON ([link](https://dhparser.readthedocs.io/en/latest/manuals/02_document-trees.html#elementtree-exchange)). 

