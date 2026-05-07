Vergleich zwischen lark und DHparser
====================================

lark und DHParser ähnlen sich in ziemlich stark und liefern, obwohl praktisch vollkommen unabhängig voneinander entwickelt, zum Teil ähnliche Lösungen für typische Herausforderungen von Rahmenwerken für domänenspezifische Sprachen (DSL für "domain specific language"). Im Detail gibt es natürlich eine Reihe von Unterschieden.

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

2. Ein Post-Mortem-Debugger für den Parser, der auch automatische für alle gescheiterten Tests ausgelöst wird. [-> link](https://dhparser.readthedocs.io/en/latest/Overview.html#debugger-included)

3. Ein Rahmenwerk für einfache oder verzweigte Datentransformations-Fließbäner. [-> link](https://dhparser.readthedocs.io/en/latest/manuals/04_postprocessing.html#processing-pipelines)

4. Unterstüzung für die Fehlerbehandlung in einer DSL. [-> link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#error-catching)

5. Unterstützung für Serverbetrieb und rudimentäre Unterstützung für das [Language Server Protokoll](https://microsoft.github.io/language-server-protocol/). [-> link](https://dhparser.readthedocs.io/en/latest/Overview.html#language-server-support) 


Parser-Typen
------------

lark unterstützt zwei Parsetypen: Earley (kann aus jeder Grammatik einen parser bauen, einschließlich mehrdeutiger Grammatiken, benögt aber ggf. mehr als lineare Rechenzeit) und LALR(1) (relativ eingeschränkter, aber mit linearer Rechenzeit). 

DHParser unterstützt nur "Parsing Expression Grammars" (lineare Rechenzeit). Damit kann man jede nicht links-rekursive Grammatik verarbeiten (bei DHParser zusätzlich einige einfache Fälle von Linksrekursion), aber keine mehrdeutigen Grammatiken (die man bei DSLs aber eigentlich auch gar nicht gebrauchen kann).

Das fundamentale Paper zu PEGs (wegen der Speicherung der Zwischenergebnisse, die die lineare Zeit ermöglicht, gerne auch "Packrat Parser" genannt) stammt von Brian Ford ([link](https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf)). Das ist die Kurzfassung seiner Magisterarbeit zu dem Thema ([link](https://pdos.csail.mit.edu/~baford/packrat/thesis/thesis.pdf)). Weitere Literar hat er auf einer Website [verlinkt](https://bford.info/packrat/). Die jüngste, sehr interessante Weiterentwicklung, könnte der Squirell Parser von Luke Hutchinson sein. [link](https://github.com/lukehutch/squirrelparser/blob/main/paper/squirrel_parser.pdf).

Lark kann sowohl scannerlos arbeiten, wobei "Terminale" dann durch reguläre Ausdrücke definiert (oder in reguläre Ausdrücke umgewandelt) werden, als auch auch mit einem externen Scanner bzw. "Lexer" kombiniert werden. Lark unterscheidet relativ scharf zwischen Terminalen und anderen Symbolen, wobei die Namen für die Terminale groß geschrieben werden müssen und Terminale u.a. dadurch definiert sind, dass sie keine Baum-Struktur sondern immer einen komplette String zurückliefern.

DHParser arbeitet immer scannerlos. Terminale werden durch reguläre Ausdrücke definiert. Bei DHParser gibt es keine so scharfe Unterscheidung zwischen Terminalen und anderen Konstrukten. Man kann Symbole, die nicht durch einen einzigen regulären Ausdruck definiert werden, wie Terminale handhaben, indem man bei der Transformation vom konkreten in den abstrakten Syntax-Baum den von ihnen erfassten Teilbaum durch den Eintrag "collapse" im Transformationsverzeichnis platt macht. 

Scannerlose Parser haben den Vorteil, dass man mit Ihnen ganz gut auch Dokumente erfassen kann, in denen mehrere formale Sprachen gemischt auftreten, wie z.B. Website-Templates, die in HTML mit einer eingebetteten Template-Sprache geschrieben werden. Ein vorgeschalteter Lexer/Scanner wüsste, da er nicht durch die Grammatik gesteuert wird, nicht, wann er die Regeln der einen, wann die der anderen Sprache anwenden sollte.

Ob es auch Vorteile der Aufteiliung in Parser und Scanner/Lexer gegenüber scannerlosen Parsern gibt, oder ob das nur ein alter Zopf ist, weiß ich nicht.


Ausdrucksstärke der Grammatik
-----------------------------

Sowohl lark als auch DHparser unterstützen für die Kodierung der Grammatik EBNF mit ein paar Extras, wobei sich die Extras weitgehend überschneiden, auch wenn sie jeweils etwas anders realisiert werden. Zu diesen Extras gehören folgende:

* Frühzeitige Vereinfachung des Syntax-Baums durch automatische bzw. konventionsbasierte Streichung von Trennzeichen, insignifikanten Leerzeichen und Kommentaren, Reduktion von (anonymen) Knoten, die nur ein Kind-Element enthalten, Zusammenlegung gleichartiger benachbarter Knoten (z.B. aufeinander folgende Zeichen gleicher semantischer Kategorie zu Zeichenketten) etc.. Bei lark sind diese Vereinfachungstechniken größtenteils festeingebaut und weniger konfigurierbar, dafür allerdings auch klarer und einfacher ([link](https://lark-parser.readthedocs.io/en/stable/tree_construction.html#tree-construction-reference)). Bei DHParser lässt sich das flexibler anpassen, dafür ist es aber auch etwas komplizierter ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#simplifying-syntax-trees-while-parsing)).

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
    
    Bei DHParser kann man alternativ zu der oben beschriebenen "@hide"-Direktive auch in der Grammatik direkt vor das Symbol den Modifikator "HIDE" schreiben: `HIDE:greet = `. Der "HIDE"-Modifikator entspricht jedoch nicht dem Fragezeichen von lark, sondern hat genau dieselbe Wirkung wir die "@hide"-Direktive bzw. der Unterstrich bei lark. Will man das Verhalten der Fragezeichen-Markierung von lark erzielen, so kann man das mit der "@reduction"-direktive am Anfang der Grammatik steuern ([link](https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#simplifying-syntax-trees-while-parsing)) und natürlich immer in einem zweiten Schritt bei der Baum-Vereinfachung, die bei DHParser "AST-Transformation" genannnt wird; gemeint ist dabei die Transformation des konkreten Syntaxbaums (CST) in den bzw. einen abstrakten Syntaxbaum (AST). 

* dd