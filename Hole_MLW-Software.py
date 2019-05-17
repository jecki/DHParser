#!/usr/bin/python3

"""Lädt das MLW-Installationsskript vonb gitlab herunter und startet es.
Nach dem Starten wird das Installationsskript wieder gelöscht, d.h. um
es wieder zu starten, muss erst dieses Skript wieder ausgeführt werden,
welches das jeweils aktuelle Installationsskript herunterlädt.
"""

import os
import ssl
import sys
import urllib.request

cwd = os.path.abspath(os.getcwd())
if cwd.endswith('MLW-DSL'):
    print('Der Pfad "%s" scheint das MLW-Git-Repositorium zu enthalten.' % cwd)
    print('Dieses Skript sollte nicht innerhalb des MLW-Git-Repositoriums ausgeführt werden!')
    sys.exit(1)

PFAD = "https://gitlab.lrz.de/badw-it/MLW-DSL/raw/master/Installiere-MLW.py"
SKRIPT_NAME = os.path.basename(PFAD)

# Lade Installationsskript herunter
with urllib.request.urlopen(PFAD, context=ssl.create_default_context()) as https:
    skript = https.read()

# Speichere Installationsskript im aktuellen Ordner (Desktop)
with open(SKRIPT_NAME, 'wb') as datei:
    datei.write(skript)

# Führe Installationsskript aus
os.system('python.exe ' + SKRIPT_NAME)

# Lösche Installationsskript nach der Ausführung, damit nicht versehentlich
# ein veraltetes Installationsskript gestartet wird.
os.remove(SKRIPT_NAME)
