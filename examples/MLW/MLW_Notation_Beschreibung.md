MLW Notation
=============

Im folgenden wird die vereinfachte Notation für MLW-Artikel beschrieben. 
Die vereinfachte Notation erlaubt es einen Artikel mit einem Text-Editor
einzugeben und dann automatisch nach XML zu übersetzen. 


Um die Beschreibung einfach zu halten, wird im Folgenden der Standardfall
eines MLW-Artikels beschrieben. Sonderfälle, die strukturelle Abweichungen
beinhalten können, werden später erklärt.


Grobstruktur
------------

Jeder Artikel besteht aus einer Folge von Beschreibungsblöcken, 
sogenannten "Positionen", die jeweils durch
ein vollständig großgeschriebenes Schlüsselwort, wie z.B. "BEDEUTUNG",
eingeleit. Ein Block endet immer dort, wo der nächste Artikelteil
anfängt. (Eine Ausnahme bilden Unterbedeutungsblöcke, die ineinander
verschachtelt sein können und immer dort aufhören, wo ein neuer Artikelteil
derselben oder einer niedrigeren Ebene beginnt.)

Die Abfolge der Blöcke sieht so aus:

    LEMMA
    GRAMMATIK
    
    [ETYMOLOGIE]
    [SCHREIBWEISE]
    [STRUKTUR]
    [GEBRAUCH]
    [METRIK]
    [VERWECHSELBAR]
    
    BEDEUTUNG
        UNTER_BEDEUTUNG
        .
        .
        .
    .
    .
    .
    
    VERWEISE
    AUTORIN
    
Die Blöcke in eckigen Klammern bilden den Artikelkopf. Sie sind optional, 
d.h. sie dürfen vorkommen, müssen aber nicht, und ihre Reihenfolge ist beliebig.

Mit Ausnahme der Blöcke im Artikelkopf hat jeder dieser Blöcke jeweils eine 
eigene Feinstruktur. Die Blöcke im Artikelkopf haben alle ein- und dieselbe
Feinstruktur.


Feinstruktur
------------

Im folgenden wird die Feinstruktur der einzelnen Positionen beschrieben. 
Der Einfachheit halber werden zunächst nur die Standardfälle dargestellt.


### LEMMA-Position

Die Lemmaposition wird durch das Schlüsselword LEMMA eingeleitet, gefolgt von
dem (ggf. "gesternten") Lemmawort. Durch Zeilenwechsel getrennt
können darauf mehrere "Lemmavarianten" folgen. In der Regel werden hier
nur Abkürzungen zur Bezeichnung bestimmter sprachlicher Phänomene
angegeben. (Das System verbietet es aber auch nicht an dieser Stelle
vollständige Wörter anzugeben.) Zum Schluss kann, wiederum durch eine Leerzeile
getrennt, noch ein Zusatzhinweis des Bearbeiters oder der Bearbeiterin
wie z.B. `{sim.}` folgen. Zusätze werden als solche dadurch kenntlich
gemacht, indem man sie in geschweifte Klammern einschließt.

(Hinweis: Im Druck und in der Vorschau werden die geschweiften Klammern nicht
mit angezeigt und statt dessen, das was innerhlab der geschweiften
Klammern steht kursiv gesetzt.)

Beispiel:

    LEMMA *facitergula

        fascitergula
        facietergula
        facistergula
        facitercula
        {sim.}   

Die zusätzliche Leerzeile zur deutlicheren optischen Trennung von Lemmawort
und Lemmavarianten ist nicht zwingend und kann auch weggelassen werden, 
ebenso wie die Einrückung der Lemmavarianten und des Zusatzes.

Das allgemeine Format für die LEMMA-Angabe sieht so aus:

    LEMMA [*]Lemmawort
    
        [Lemmavariante 1]
        [Lemmavariante 2]
                .
                .
                .
        {Zusatz}


### GRAMMATIK-Position

Die Grammatik-Position wird durch das Schlüsselwort "GRAMMATIK" eingeleitet.
Darauf folgt die Wortart, die Angabe der Flexion und - bei Nomen - der Genus.
Die Angabe der Wortart ist optional und kann auch weggelassen werden.
Wir die Wortart jedoch angegeben, so muss sie von der Flexion durch
ein Semikolon getrennt werden. Zwischen Flexion und Genus genügt
demgegenüber ein einfaches Leerzeichen, so wie das auch später im Druck
erscheint.

Die Flexion wird abgekürzt mit führendem Spiegelstrich angegen, ggf. kann es
mehrere solcher Angaben geben, die durch Komma getrennt sind (z.B. "-us, -i").

Der Genus kann in abgekürzter Form ("f.") oder in ausgeschriebener Form
("femininum") angegeben werden. 

Wie schon beim Lemma können in der Grammatik-Position mehrere
Grammatik-Varianten folgen. Bei den Grammatik-Varianten wird keine Wortart
mehr angegeben, sondern lediglich die Flexion und ggf. der Genus. 

Nach der Angabe einer Grammatikvariante folgen, abgetrennt durch einen Doppelpunkt 
*immer* ein oder mehrere Belege. Bei den Belegen kann es sich immer um einen
einfachen Verweis handeln, oder um direkte Belege mit Werk, Stellenangabe und
ggf. wörtlichem Zitat. Folgen mehrere Belege, so müssen sie durch einen Stern 
"*" eingeleitet werden.

Verweise werden wie Zusätze mit geschweiften Klammern umschlossen, wobei direkt
nach der öffnenden Klammer ein Pfleilsymbol ("=>") steht, auf das die Zielmarke folgt.
(Näheres siehe unten).

Beispiel:

    GRAMMATIK
        nomen; -ae f.
    
        -us, -i m.:  {=> ibi_1}
        -um, -i n.:  {=> ibi_2}

Die allgemeine Form lautet:

    GRAMMATIK
        [Wortart;] Flexion [Genus]
    
        Flexion [Genus]: Beleg [* Beleg] ...
            .
            .
            .
            
### Artikelkopf-Positionen

Alle Positionen im Artikelkopf (Etymologie-Position, Schreibweisen-Position,
Struktur-Position, Gebrauchs-Position, Metrik-Position, 
Verwechselungs-Position) sind nach ein- und demselben Schema aufgebaut.

