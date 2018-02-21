MLW Language Server
===================

Das wird mal ein language server für den MLW-Dialekt.
Gegenüber bloßer Syntaxhervorhebung und externem Werkzeugaufruf
sollte dadurch eine tiefere Integration und bessere Unterstützung
von Visual Studio Code möglich werden.

Das Grundgerüst wurde von: https://github.com/sourcegraph/python-langserver/
übernommen.

Starten mit:

    python python-langserver.py --mode=tcp --addr=2087
