# MLW Notation

Im folgenden wird die vereinfachte Notation für MLW-Artikel beschrieben.
Die vereinfachte Notation erlaubt es einen Artikel mit einem Text-Editor
einzugeben und dann automatisch nach XML zu übersetzen.

Um die Beschreibung einfach zu halten, wird im Folgenden der Standardfall
eines MLW-Artikels beschrieben. Sonderfälle, die strukturelle Abweichungen
beinhalten können, werden später erklärt.

## Grobstruktur

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

Alle Positionen im Artikelkopf (*Etymologie-Position, Schreibweisen-Position,
Struktur-Position, Gebrauchs-Position, Metrik-Position,
Verwechselungs-Position*) sind nach ein- und demselben Schema aufgebaut:

Am Anfang steht ein Schlüsselwort, das anzeigt, um welche Artikelkopf-Position
es sich handelt, z.B. SCHREIBWEISE, danach folgen ein oder mehrere
*Besonderheiten* und für jede Besonderheit ein oder mehrere *Varianten*
mit *Belegen*. Die Varianten einer Besonderheit können (müssen aber nicht)
wiederum verschiedenen Unterkategorien zugeordnet sein.

Beispiel 1:

    SCHREIBWEISE
    script.:
        hym-:   {=> ziel_1}
        em-:    Chron. Fred.; 2,35sqq. capit.; p. 43.; 2,36 p. 60,10.
        ym-:    Chart. Sangall.; A 194.
        impir-: {=> ziel_2}

Hier ist "script." die Bezeichnung einer Besonderheit, während "hym-", "em-",
"ym-", "impir-" jeweils Varianten dieser Besonderheit repräsentieren. Die
auf die Varianten folgenden Belge können entweder Verweise (z.B: "{=> ziel_1}"),
die auf eine frei vergebene Sprungmarke verweisen sein (siehe weiter unten die
Erklärungen zu "Verweise") oder Belegstellen, bei denen immer ein Werk gefolgt
von Stellenangaben und ggf. Zitaten angegeben wird. Das genaue Format wird weiter
unten unter "Belege" näher beschrieben.

Beispiel 2:

    STRUKTUR
        form. sing.:
            gen.:
                -ri: * {=> ziel_3}
                     * {adde} Annal. Plac. a.; 1266; p. 516,21.
                -iae: Chron. Fred.; 2,33.; p. 56,22. 2,35.
            abl.:
                -um: Chron. Fred.; 2,15. 2,35sqq. capit.; p. 43.

Bei diesem Beispiel ist "form. sing." eine Besonderheit, die die Unterkategorien
"gen." und "abl." enthält.

Man beachte, dass für die Variante "-ri" unterhalb von
"gen." mehrere Belege angegeben sind. Sobald mehr als ein Beleg angeben ist,
muss jeder neue Beleg durch einen Stern "*" eigeleitet werden. Als ein Beleg zählt
dabei ein Verweis oder ein Werk mit möglicherweise mehreren Stellenangaben.
Eine weitere Stellenangabe innerhalb eines Werks darf nicht mit einem Stern
eingeleitet werden, sondern wird von der vorhergehenden Stellenangabe oder vom Werk
mit einem einfachen Semikolon abgetrennt.

Die allgemeine Form für Artikelkopf-Positionen kan man grob so darstellen:

    SCHLÜSSELWORT
        Besonderheit :
            [Unterkategorie :]
                Variante : Beleg
                   .
                   .
                   .
           .
           .
           .

Die Einrückungen sind übrigens nicht zwingend. Sie helfen aber besonders bei den
Positionen im Artikelkopf, die Übersicht zu behalten.

### Bedeutungsposition

Die Bedeutungsposition besteht aus einer Folge von Bedeutungs-,
Unterbedeutungs-, Unterunterbedeutungs-, ...-Blöcken, die bis zu
sechs Ebenen tief verschachtelt werden können.

Wie schon die anderen Abschnitte des Wörterbuchartikels wird jeder
Bedeutungsblock durch ein Schlüsselwort eingeleitet.
Auf der obersten Bedeutungsebene ist das das Schlüsselwort "BEDEUTUNG".
Tiefere Bedeutungsebenenen werden mit den Schlüsselwörtern "UNTER_BEDEUTUNG",
"UNTER_UNTER_BEDEUTUNG", "UUU_BEDEUTUNG" bis hin zu "UUUUU_BEDEUTUNG" (für die
6. Ebenentiefe) eingeleitet.

Auf dieses Schlüsselwort folgt zunächst die Angabe eines Interpretaments (sprich
deutsche und lateinische Übersetzung) oder eine kategoriale Angabe dafür,
in welcher Hinsicht oder in welchem Sinne die folgenden Belege das beschriebene
Wort verwenden ("in univ.", "sensu communi", ...).

Interpretamente werden immer als eine durch Kommata getrennte Liste von Wörtern
notiert, die entweder durch das Schlüsselwort "LATEINISCH" (oder abgekürzt "LAT")
oder "DEUTSCH" (oder abgekürzt "DEU") eingeleitet werden. Später im Druck erscheinen
diese Schlüsselwörter, wie auch alle anderen Schlüsselwörter, natürlich nicht mehr,
sondern die lateinische und deutsche Bedeutungsangabe werden durch einen langen
Spiegelstrich getrennt.

Kategoriale Angaben werden nicht durch ein zusätzliches Schlüsselwort eingeleitet,
sondern bestehen aus einer Folge von Wörtern, die durch einen Doppelpunkt
abgeschlossen ist.

Beispiel 1 (Interpretament):

    BEDEUTUNG
    LATEINISCH iussum, praeceptum, mandatum
    DEUTSCH	   Befehl, Anweisung, Auftrag

Beispiel 2 (Interpretament):

    BEDEUTUNG
    LATEINISCH	potestas, dominatio, dicio
    DEUTSCH		Macht, Herrschaft, Herrschaftsgewalt {plur. sensu sing. :
                {=> v. ibi. al. imperator40m_2}}

Wie dieses Beispiel zeigt, dürfen Interpretamente auch Bearbeiter/innen-Zusätze
(die immer in geschweiften Klammern stehen) und Verweise, Anker etc. enthalten.
