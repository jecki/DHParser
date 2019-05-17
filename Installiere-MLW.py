#!/usr/bin/python3

"""Installiere-MLW.py - installiert MLW-Erweiterungen für Visual Studio Code

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

import datetime
import os
import platform
import re
import shutil
import ssl
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable
import urllib.request
import zipfile


VSC_MINDEST_VERSION = (1,22,0)


#######################################################################
#
# Beispielartikel: fascitergula
#
#######################################################################

Beispielartikel = """
LEMMA *facitergula

  (fasc-, -iet-, -ist-, -rcu-)
  {sim.}


GRAMMATIK
    nomen; -ae f.

    -us, -i m.:  {=> faceterculi}
    -um, -i n.:  {=> facitergulum}


SCHREIBWEISE
    script.:
        vizreg-:       {=> vizregule}
        festregel(a):  {=> festregelę}
        fezdregl(a):   {=> fezdreglę}


BEDEUTUNG  pannus, faciale, sudarium -- Gesichtstuch, Schweißtuch,
  Tuch {usu liturg.}{de re v. {=> eintrag/ibi_X}}:

  * CATAL. thes. Germ.; 28,11 (post 851) "#facitergulum III"

  * FORM. Sangall.; 39 p. 421,16
  "munuscula ... direximus, hoc est palliolum ... , #facitergulas duas"

  * CATAL.  thes. Germ.; 18,7 "#faceterculi  viginti  quatuor"

  * LIBRI confrat.; III app. A  6  p.  137,30 "pulpitum ...  #facitergula
  cocco imaginata circumdari iussit {pontifex}"

  * CATAL. thes. Germ.; 76,15 "#faciterulae II"; 40,5 VI "#vizregule";
  129a,5 "#facisterculas II."; 24,8  "#facitella X"; 114,8 VIII
  "#fezdreglę";  6,24  "#fasciutercule VII"; 92,6 "#fascerculę tres.";
  21,20 IIII "#festregelę" {saepe}


BEDEUTUNG  capital, rica -- Kopftuch:

  * TRANSL. Libor.  I; 32
  "raptis feminarum #facitergulis (fa[s]citergiis  {var. l.})."

  * TRANSL. Libor. II; 20
  "nuditatem  membrorum  illius {puellae}  tegere  festinarunt  fideles clerici 
  et  laici  inprimis cum eorum #facitercula, dein vestibus solitis."

AUTORIN Weber
"""

#######################################################################
#
# Quell und Zielverzeichnisse (vorgegeben)
#
#######################################################################

def bestimme_vsc_version(kommando):
    with subprocess.Popen([kommando, "-v"], stdout=subprocess.PIPE,
                          bufsize=1, universal_newlines=True) as p:
        version_info = [line for line in p.stdout]
    if version_info:
        version = tuple(int(part) for part in version_info[0].split('.'))
    else:
        version = (0, 0, 0)
    return version

nutzerverzeichnis = os.path.expanduser('~')
heimverzeichnis = 'H:\\MLW-DSL' if os.path.exists('H:') else \
    os.path.join(nutzerverzeichnis, 'MLW-DSL')
vsc_ersatzpfad = os.path.join(os.path.expanduser('~'), 'VSCode')
vsc_kommando = 'code'

if platform.system() == "Windows":
    vsc_kommando = 'C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd'
    alt_vsc_kommando = os.path.join(vsc_ersatzpfad, 'bin', 'code.cmd')
    if not os.path.exists(vsc_kommando):
        vsc_kommando = 'C:\\Program Files (x86)\\Microsoft VS Code\\bin\\code.cmd'
        if not os.path.exists(vsc_kommando):
            vsc_kommando = os.path.join(os.path.expanduser('~'),
                                        "AppData\\Local\\Programs\\Microsoft VS Code\\bin\\code.cmd")
        if not os.path.exists(vsc_kommando):
            vsc_kommando = alt_vsc_kommando
else:
    alt_vsc_kommando = os.path.join(vsc_ersatzpfad, 'bin', 'code')
    try:
        subprocess.run([vsc_kommando, '-v'])
    except FileNotFoundError:
        vsc_kommando = alt_vsc_kommando

mlw_version = (0, 0, 0)
arbeitsverzeichnis = os.path.join(heimverzeichnis, 'MLW-Artikel')
softwareverzeichnis_name = 'MLW-Software'
softwareverzeichnis = os.path.join(heimverzeichnis, softwareverzeichnis_name)
skriptverzeichnis = os.path.dirname(os.path.realpath(__file__))
archivadresse = "https://gitlab.lrz.de/badw-it/MLW-DSL/repository/master/archive.zip"
dhparser_archivadresse = "https://gitlab.lrz.de/badw-it/DHParser/repository/master/archive.zip"
if platform.system() == "Windows":
    vsc_archivadresse = "https://eckhartarnold.de/backup/VSCode_win32.zip"
elif platform.system() == "Linux":
    vsc_archivadresse = "https://eckhartarnold.de/backup/VSCode_linux.zip"
else:
    vsc_archivadresse = 'kein Archiv mit VSCode hinterlegt!'
vsc_konfig_verzeichnis = os.path.join(os.path.expanduser('~'), '.vscode')

vsc_version = (0, 0, 0)
alt_vsc_version = (0, 0, 0)
try:
    vsc_version = bestimme_vsc_version(vsc_kommando)
    if vsc_version < VSC_MINDEST_VERSION and alt_vsc_kommando != vsc_kommando:
        kommando = alt_vsc_kommando
        alt_vsc_version = bestimme_vsc_version(alt_vsc_kommando)
    else:
        kommando = vsc_kommando
except FileNotFoundError:
    kommando = alt_vsc_kommando
vsc_vorhanden = vsc_version != (0, 0, 0)
version = max(vsc_version, alt_vsc_version)

schon_installiert = max(alt_vsc_version, vsc_version) >= VSC_MINDEST_VERSION \
                    and os.path.exists(softwareverzeichnis)


def lies_versionshinweise(ordner=softwareverzeichnis):
    try:
        with open(os.path.join(ordner, 'ÄNDERUNGEN.txt'),
                  'r', encoding='utf-8') as f:
            änderungen = f.read()
        match = re.search(r'Version\s+(\d+\.\d+\.\d+)(\s*\w*)', änderungen)
        versions_str = match.group(0)
        versions_tuple = tuple(int(part) for part in match.group(1).split('.'))
        match = re.search('-------+\n(.*?)Version', änderungen, flags=re.DOTALL)
        versions_hinweise = match.group(1).strip()
        return versions_str, versions_tuple, versions_hinweise
    except FileNotFoundError:
        print('Konnte "ÄNDERUNGEN.txt" nicht finden - schade :-(')
        return "unknown", (0, 0, 0), ""


#######################################################################
#
# Installationsroutinen
#
#######################################################################


FortschrittsRückruf = Callable[[str, float], None]
FehlerRückruf = Callable[[str], None]
AbbruchRückruf = Callable[[], bool]


def Installiere_Fremdsoftware(MSG: FortschrittsRückruf,
                               WARN: FehlerRückruf,
                               abbruch: AbbruchRückruf=lambda: False):
    global vsc_kommando, alt_vsc_kommando, kommando, \
        version, vsc_version, alt_vsc_version, vsc_vorhanden
    MSG('Prüfe, ob Visual Studio Code installiert und Version aktuell', 0.0)

    if vsc_vorhanden:
        if vsc_version < VSC_MINDEST_VERSION:
            if alt_vsc_kommando != vsc_kommando:
                vsc_kommando = alt_vsc_kommando

        if version < VSC_MINDEST_VERSION:
            WARN('VERALTETE Visual Studio Code Version %i.%i.%i gefunden!\n' % version
                 + 'Als Notlösung wird eine neuere Version parallel installiert.', 0.1)
            vsc_vorhanden = False
        else:
            MSG('Aktuelle Visual Studio Code Version %i.%i.%i gefunden' % version, 0.1)
    else:
        MSG('Visual Studio Code nicht gefunden!', 0.1)

    if abbruch():
        return

    if not vsc_vorhanden:
        MSG('NOTLÖSUNG: Visual Studio Code ToGo-Installation.')

        if os.path.exists(vsc_ersatzpfad):
            if os.path.exists(alt_vsc_kommando) or not os.listdir(vsc_ersatzpfad):
                MSG('Lösche altes Visual Studio Code ToGo', 0.2)
                shutil.rmtree(vsc_ersatzpfad)
            else:
                raise Exception('Pfad %s existiert bereits,\nscheint aber ' % vsc_ersatzpfad +
                                'nicht Visual Studio Code zu enthalten. '
                                'Kann VSC dort nicht installieren')

        MSG('Lade Visual Studio Code "ToGo" herunter...', 0.3)
        with urllib.request.urlopen(vsc_archivadresse, context=ssl.create_default_context()) as https:
            data = https.read()

        if abbruch():
            return

        if not os.path.exists(vsc_ersatzpfad):
            MSG('Erstelle Verzeichnis: ' + vsc_ersatzpfad, 0.6)
            os.mkdir(vsc_ersatzpfad)

        archivpfad = os.path.join(vsc_ersatzpfad, 'VSCode.zip')
        with open(archivpfad, 'wb') as f:
            MSG('Speichere ' + archivpfad, 0.7)
            f.write(data)

        if abbruch():
            os.remove(archivpfad)
            return

        MSG('Entpacke Visual Studio Code...', 0.8)
        with zipfile.ZipFile(archivpfad) as z:
            # wurzelverzeichnis = z.namelist()[0]
            z.extractall(vsc_ersatzpfad)
        os.remove(archivpfad)
        if abbruch():
            shutil.rmtree(vsc_ersatzpfad)
            return

        if platform.system() != "Windows":
            MSG('Setze Datei-Rechte für ausführbare VSC-Dateien.')
            os.chmod(os.path.join(vsc_ersatzpfad, 'code'), 0o100755)
            os.chmod(os.path.join(vsc_ersatzpfad, 'bin', 'code'), 0o100755)

        if os.path.exists(vsc_kommando):
            MSG('Visual Studio Code ToGo wurde erfoglreich installiert', 1.0)
            vsc_vorhanden = True
            kommando = alt_vsc_kommando
            alt_vsc_version = VSC_MINDEST_VERSION
            version = VSC_MINDEST_VERSION
        else:
            WARN('Fehler bei der Installation von Visual Studio Code :-(')

    MSG('Visual Studio Code Kommandopfad: ' + kommando)


def Lade_MLW_Software_herunter(MSG: FortschrittsRückruf,
                               WARN: FehlerRückruf,
                               abbruch: AbbruchRückruf=lambda: False):
    """
    Lädt die aktuelle MLW-Software aus dem master-Zweig des gitlab-
    Speichers herunter. Verschiebt die alte Softwasre in das
    Unterverzeichnis "VERALTET".
    """
    MSG('Lade MLW-Software vom gitlab-Server herunter...', 0.0)
    with urllib.request.urlopen(archivadresse, context=ssl.create_default_context()) as https:
        data = https.read()

    if abbruch():
        return

    if not os.path.exists(heimverzeichnis):
        MSG('Erstelle Verzeichnis: ' + heimverzeichnis, 0.1)
        os.mkdir(heimverzeichnis)

    archivpfad = os.path.join(heimverzeichnis, 'MLW-Archiv.zip')
    with open(archivpfad, 'wb') as f:
        f.write(data)

    if abbruch():
        os.remove(archivpfad)
        return

    MSG('Entpacke MLW-Software im Heimverzeichnis...', 0.2)
    with zipfile.ZipFile(archivpfad) as z:
        wurzelverzeichnis = z.namelist()[0]
        z.extractall(heimverzeichnis)
    os.remove(archivpfad)
    wurzelpfad = os.path.join(heimverzeichnis, wurzelverzeichnis)
    if abbruch():
        shutil.rmtree(wurzelpfad)
        return

    if os.path.exists(softwareverzeichnis):
        global mlw_version
        mlw_version = lies_versionshinweise()[1]
        MSG('Verschiebe alte MLW-Software (Version %i.%i.%i) ins VERALTET-Verzeichnis.'
            % mlw_version, 0.4)
        zielpfad = softwareverzeichnis + '_VERALTET_' \
            + datetime.datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
        os.rename(softwareverzeichnis, zielpfad)
        veraltet_dir = os.path.join(heimverzeichnis, 'MLW-VERALTET')
        if not os.path.exists(veraltet_dir):
            os.mkdir(veraltet_dir)
        if os.path.isdir(veraltet_dir):
            shutil.move(zielpfad, veraltet_dir)
        else:
            WARN('WARNUNG: Pfad "%s" ist kein Verzeichnis! Alte Version verbleibt im Heimverzeichnis.'
                % veraltet_dir)
    MSG('Benenne neues MLW-Softwareverzeichnis in "%s" um'
        % softwareverzeichnis_name, 0.5)
    os.rename(wurzelpfad, softwareverzeichnis)

    MSG('Lade DHParser-submodule-Software vom gitlab-Server herunter...', 0.6)
    with urllib.request.urlopen(dhparser_archivadresse,
                                context=ssl.create_default_context()) as https:
        data = https.read()

    if abbruch():
        return

    dhparser_archivpfad = os.path.join(softwareverzeichnis, 'DHParser-submodule-Archiv.zip')
    with open(dhparser_archivpfad, 'wb') as f:
        f.write(data)

    if abbruch():
        os.remove(dhparser_archivpfad)
        return

    MSG('Entpacke DHParser-submodule im MLW-Software-Verzeichnis...', 0.8)
    dhparser_verzeichnis = os.path.join(softwareverzeichnis, 'DHParser-submodule')
    if os.path.exists(dhparser_verzeichnis):
        os.rmdir(dhparser_verzeichnis)
    with zipfile.ZipFile(dhparser_archivpfad) as z:
        wurzelverzeichnis = z.namelist()[0]
        z.extractall(softwareverzeichnis)
    os.remove(dhparser_archivpfad)
    wurzelpfad = os.path.join(softwareverzeichnis, wurzelverzeichnis)
    if abbruch():
        shutil.rmtree(wurzelpfad)
        return
    os.rename(wurzelpfad, dhparser_verzeichnis)

    MSG('MLW-Software steht bereit', 1.0)


def Initialisiere_Arbeitsverzeichnis(MSG: FortschrittsRückruf,
                                     WARN: FehlerRückruf,
                                     abbruch: AbbruchRückruf = lambda: False):
    """Erstellt (falls nicht schon vorhanden) und initialisiert ein lokales
    Arbeitsverzeichnis, in welchem MLW-Artikel mit Visual Studio Code
    bearbeitet werden können und dabei von Syntax-Highlighting, Vorschau
    etc. profitieren.

    Dazu wird im Arbeitsverzeichnis ein .vscode Unterverzeichnis angelegt,
    in welchem eine ``tasks.json`` abgelegt wird, in der der Aufruf des
    MLW-Compilers aus Visual Studio Code heraus konfiguiert wird.

    Das Syntax-Highlighting und die Code-Schnipsel (für die Vorschläge von
    Belegtexten) kann man - aus welchen Gründen auch immer - nicht i,
    lokalen .vscode Verzeichnis konfigurieren. Die notwendigen
    Konfigurationsdateien daher aus dem MLW-Softwareverzeichnis
    in das "globale" .vscode Verzeichnis innerhalb des Heimverzeichnis'
    des Nutzers kopiert.
    """
    if not os.path.exists(arbeitsverzeichnis):
        MSG('Erstelle Arbeitsverzeichnise "%s"' % arbeitsverzeichnis, 0.2)
        os.mkdir(arbeitsverzeichnis)

    lokales_vsc_verzeichnis = os.path.join(arbeitsverzeichnis, '.vscode')
    if not os.path.exists(lokales_vsc_verzeichnis):
        MSG('Erstelle lokales ".vscode"-Verzeichnis', 0.4)
        os.mkdir(lokales_vsc_verzeichnis)

    vsc_quell_verzeichnis = os.path.join(softwareverzeichnis, 'VSCode')
    tasks_datei = os.path.join(vsc_quell_verzeichnis, 'tasks.json')
    with open(tasks_datei, 'r') as datei:
        tasks = datei.read()

    voller_compilerpfad = os.path.join(softwareverzeichnis, 'MLWCompiler.py').replace('\\', '\\\\')
    voller_serverpfad = os.path.join(softwareverzeichnis, 'MLWServer.py').replace('\\', '\\\\')
    tasks = tasks.replace('./MLWCompiler.py', voller_compilerpfad).\
        replace('python MLWCompiler.py', 'python ' + voller_compilerpfad)
    tasks = tasks.replace('./MLWServer.py', voller_serverpfad).\
        replace('python MLWServer.py', 'python ' + voller_serverpfad)
    # encoding = 'cp1252' if platform.system() == "Windows" else 'utf-8'
    with open(os.path.join(lokales_vsc_verzeichnis, 'tasks.json'), 'w', encoding='utf-8') \
            as datei:
        MSG('Schreibe tasks.json', 0.6)
        datei.write(tasks)

    with open(os.path.join(arbeitsverzeichnis, "Beispiel.mlw"), 'w', encoding="utf-8") as datei:
        MSG('Erstelle Beispielartikel im Arbeitsverzeichnis')
        datei.write(Beispielartikel)

    fortschritt = 0.7
    for vsc_modul in ['mlwquelle']:
        quell_verzeichnis = os.path.join(vsc_quell_verzeichnis, vsc_modul)
        erweiterungs_verzeichnis = os.path.join(vsc_konfig_verzeichnis, 'extensions')
        MSG('Kopiere Visual Studio Code module "%s"' % vsc_modul, fortschritt)
        fortschritt += 0.1
        ziel_verzeichnis = os.path.join(erweiterungs_verzeichnis, vsc_modul)
        if os.path.exists(ziel_verzeichnis):
            shutil.rmtree(ziel_verzeichnis)
        shutil.copytree(quell_verzeichnis, ziel_verzeichnis)

    ## Installiere CodeMap
    # result = subprocess.check_output('code --install-extension oleg-shilo.codemap', shell=True)
    # if re.search(r'Extension .*? (?:successfully|is already) installed', str(result)) is not None:
    #     MSG('Erweiterung CodeMap ist (nun) installiert')
    # else:
    #     MSG('Bei der Installation der Erweiterung CodeMap trat ein Fehler auf:')
    #     MSG(result)
    #
    # print(vsc_quell_verzeichnis, vsc_konfig_verzeichnis)
    # ## Hole das Installationsverzeichnis
    # codemap_dirname = ""
    # for root, dirs, files in os.walk(erweiterungs_verzeichnis):
    #     if codemap_dirname != "":
    #         break
    #     for name in dirs:
    #         if name.startswith('oleg-shilo.codemap-'):
    #             codemap_dirname = os.path.join(erweiterungs_verzeichnis, name)
    #             break
    #
    # ## und passe dessen Config an
    # with open(os.path.join(vsc_quell_verzeichnis, 'codemap.mlw.json'), mode="r", encoding="utf-8") as f:
    #     config_codemap_mlw = f.read()
    # with open(os.path.join(codemap_dirname, 'package.json'), mode="r", encoding="utf-8") as f:
    #     config_codemap_original = f.read()
    #
    # match = re.search(r'("properties": .*?"codemap\.textModeLevelPrefix": \{[^\}]+\},)(?:.+?"codemap\.\w+".*?"description".+?\s+\},?)+', config_codemap_original, re.MULTILINE|re.DOTALL)
    # if match is None:
    #     MSG("Konnte Config für CodeMape nicht anpassen!")
    # else:
    #     with open(os.path.join(codemap_dirname, 'package.json'), mode="w", encoding="utf-8") as f:
    #         f.write(config_codemap_original.replace(match.group(0), match.group(1) + "\n" + config_codemap_mlw).replace('"name": "Code Map"', '"name": "MLW Artikelnavigation"'))
    fortschritt += 0.1
    MSG('Visual-Studio-Code-Module für MLW stehen bereit', 1.0)


#######################################################################
#
# Terminal-Ausgabe
#
#######################################################################


def msg_terminal(txt, fortschritt):
    print(txt)


def err_terminal(txt):
    print(txt)


#######################################################################
#
# tkinter-Oberfläche
#
#######################################################################

class MLWInstallationsAnwendung(tk.Tk):
    """
    Eine kleine GUI-Anwendung zur Installation der MLW-Software.
    """
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title('MLW-Software-Installation')
        self.minsize(640, 480)
        self.option_add("*tearOff", False)
        self.protocol("WM_DELETE_WINDOW", self.bei_beende)

        self.arbeitsverzeichnis = tk.StringVar()
        self.arbeitsverzeichnis.set(arbeitsverzeichnis)

        self.betaversion = tk.BooleanVar()
        self.betaversion.set(False)

        global schon_installiert
        self.probieren_erlaubt = 'normal' if schon_installiert else 'disabled'
        self.erzeuge_bedienelemente()
        self.verknüpfe_bedienelemente()
        self.baue_eingabemaske()

        self.schloss = threading.Lock()
        self.arbeiter = None
        self.abbruch_flagge = False
        self.deiconify()

    def erzeuge_bedienelemente(self):
        """Erzeugt die Bedienelemente, jedoch noch ohne das Layout
        festzulegen."""
        self.überschrift = tk.Label(
            self, justify=tk.LEFT, text=
            'Diese Programm installiert bzw. aktualisiert die notwendigen Skripte für die\n'
            'Eingabe von MLW-Artikeln in einer vereinfachten Notation.\n\n'
            'Außerdem legt es ein Arbeitsverzeichnis für die MLW-Artikel an. Falls das\n'
            'Verzeichnis schon existiert, wird lediglich die darin versteckte Konfiguration für\n'
            'den Visual-Studio-Code-Editor aktualisiert.\n\n'
            'Es wird vorausgesetzt, dass der Editor "Visual Studio Code" bereits auf dem System\n'
            'installiert ist.\n\n'
            'Um die Installation durchzuführen, bitte unten auf START klicken.'
        )
        self.arbeitsverzeichnis_info = tk.Label(self, text='Arbeitsverzeichnis:')
        self.arbeitsverzeichnis_eingabe = tk.Entry(self, textvariable=self.arbeitsverzeichnis)
        self.arbeitsverzeichnis_auswahl = tk.Button(self, text="...", command=lambda:
                self.pfadauswahl('Wähle Arbeitsverzeichnis', self.arbeitsverzeichnis,
                                 self.arbeitsverzeichnis_eingabe))
        self.log_info = tk.Label(self, text='Fortschritt:')
        self.log = tk.Text(self, bg="lightgrey")
        self.betaknopf = tk.Checkbutton(text="β-Version", fg="red", variable=self.betaversion,
                                        command=self.bei_beta)
        self.betalabel = tk.Label(text='Für die aktuellste Testversion, bitte das Häkchen '
                                       'vor "β-Version"setzen.')
        self.startknopf = tk.Button(text="START ->", fg="blue", command=self.bei_start)
        self.probierenknopf = tk.Button(text="Ausprobieren ->", fg="black",
                                        command=self.bei_ausprobieren, state=self.probieren_erlaubt)
        self.endeknopf = tk.Button(text="ENDE", fg='red', command=self.bei_endeknopf)

    def verknüpfe_bedienelemente(self):
        """Verknüpft die Bedienelemente mit GUI-Ereignissen, wie
        Druck auf die Escape-Taste etc.
        """
        self.bind("<Escape>", lambda event: self.breche_ab())
        self.arbeitsverzeichnis_eingabe.bind("<Return>", self.prüfe_arbeitsverzeichnis)
        self.arbeitsverzeichnis_eingabe.bind("<FocusOut>", self.prüfe_arbeitsverzeichnis)

    def baue_eingabemaske(self):
        """Legt das Layout der Bedienelemente fest."""
        padWE = dict(sticky=(tk.W, tk.E), padx="5", pady="5")
        padW = dict(sticky=(tk.W,), padx="5", pady="5")
        padE = dict(sticky=(tk.E,), padx="5", pady="5")
        padNW = dict(sticky=(tk.W, tk.N), padx="5", pady="5")
        self.überschrift.grid(row=0, column=1, **padW)
        self.arbeitsverzeichnis_info.grid(row=1, column=0, **padW)
        self.arbeitsverzeichnis_eingabe.grid(row=1, column=1, **padWE)
        self.arbeitsverzeichnis_auswahl.grid(row=1, column=2, **padWE)
        self.log_info.grid(row=2, column=0, **padNW)
        self.log.grid(row=2, column=1, **padWE)
        self.log["height"] = 15
        self.columnconfigure(1, weight=1)
        self.betaknopf.grid(row=3, column=0, **padW)
        self.betalabel.grid(row=3, column=1, **padW)
        self.startknopf.grid(row=4, column=0, **padW)
        self.probierenknopf.grid(row=4, column=1, **padW)
        self.endeknopf.grid(row=4, column=2, **padW)

    def pfadauswahl(self, titel, variable, anzeige):
        """Ruft eine Auswahlbox aus, mit der sich ein Pfad im Dateisystem
        auswählen lässt."""
        value = variable.get() or None
        pfad = tk.filedialog.askdirectory(title=titel, initialdir=value)
        if pfad:
            variable.set(pfad)

    def prüfe_arbeitsverzeichnis(self, event):
        name = self.arbeitsverzeichnis.get()
        if not name:
            self.arbeitsverzeichnis.set('MLW')

    def lies_abbruch_flagge(self):
        with self.schloss:
            flagge = self.abbruch_flagge
        return flagge

    def abbruch(self) -> bool:
        flagge = self.lies_abbruch_flagge()
        if flagge:
            self.schreibe_log("\n-------------------------\n"
                              "INSTALLATION ABGEBROCHEN!\n"
                              "-------------------------\n")
            with self.schloss:
                self.startknopf['fg'] = 'blue'
                self.startknopf['text'] = 'START ->'
                self.probierenknopf['fg'] = 'black'
                self.probierenknopf['state'] = self.probieren_erlaubt
                self.update()
        return flagge

    def brich_ab(self):
        with self.schloss:
            self.startknopf['fg'] = 'blue'
            self.startknopf['text'] = 'START ->'
            self.abbruch_flagge = True

    def lösche_log(self):
        with self.schloss:
            self.log.delete("1.0", tk.END)
            self.update()

    def schreibe_log(self, text, fortschritt=1.0):
        with self.schloss:
            self.log.insert(tk.END, text + '\n')
            self.log.yview_moveto(1.0)
            self.update()

    def installiere(self):
        def abgebrochen():
            with self.schloss:
                flagge = self.abbruch_flagge
                self.abbruch_flagge = False
            return flagge

        def warnung_rückruf(meldung, fortschritt=1.0):
            tk.messagebox.showerror(title="Fehler / Warnung!", message=meldung)
            self.schreibe_log(meldung)

        try:
            Installiere_Fremdsoftware(self.schreibe_log, warnung_rückruf,
                                      self.abbruch)
            # self.brich_ab(); return  # for debugging!
        except Exception as e:
            warnung_rückruf(str(e))
            self.brich_ab()
        # if abgebrochen():
        #     return

        try:
            beta = self.betaversion.get()
            global archivadresse, dhparser_archivadresse
            if beta:
                archivadresse = archivadresse.replace('master', 'development')
                dhparser_archivadresse = dhparser_archivadresse.replace('master', 'development')
            Lade_MLW_Software_herunter(self.schreibe_log, warnung_rückruf,
                                       self.abbruch)
            if beta:
                archivadresse = archivadresse.replace('development', 'master')
                dhparser_archivadresse = dhparser_archivadresse.replace('development', 'master')
        except Exception as e:
            warnung_rückruf(str(e))
            self.brich_ab()
        if abgebrochen():
            return

        try:
            Initialisiere_Arbeitsverzeichnis(self.schreibe_log, warnung_rückruf,
                                             self.abbruch)
        except Exception as e:
            warnung_rückruf(str(e))
            self.brich_ab()
        if abgebrochen():
            return

        self.schreibe_log("\n============================\n"
                          "INSTALLATION ERFOLGREICH :-)\n"
                          "============================\n")
        with self.schloss:
            self.startknopf['fg'] = 'black'
            self.startknopf['text'] = 'START ->'
            self.probierenknopf['fg'] = 'green'
            self.probierenknopf['state'] = 'normal'
            self.update()
        self.abbruch_flagge = False

        v_str, v_tuple, v_hinweise = lies_versionshinweise(softwareverzeichnis)
        if v_tuple > mlw_version:
            self.schreibe_log("\nNEUE VERSION: " + v_str + '\n\n')
            self.schreibe_log(v_hinweise + '\n')
        else:
            self.schreibe_log("VERSION: " + v_str + '\n\n')

    def bei_beta(self):
        pass
        # if self.betaversion.get():
        #     tk.messagebox.showwarning(title="Warnung!",
        #                               message="Die beta-Version ist zwar schon\n"
        #                                       "fortgeschrittener, enthält aber\n"
        #                                       "oft noch Fehler!")

    def bei_start(self):
        if self.startknopf['text'] == "Abbrechen":
            with self.schloss:
                self.abbruch_flagge = True
            return
        self.abbruch_flagge = False
        self.startknopf['fg'] = 'darkred'
        self.startknopf['text'] = 'Abbrechen'
        self.probierenknopf['fg'] = 'black'
        self.probierenknopf['state'] = 'disabled'
        self.update()
        global arbeitsverzeichnis
        arbeitsverzeichnis = self.arbeitsverzeichnis.get()
        self.arbeiter = threading.Thread(target=self.installiere)
        self.arbeiter.start()

    def bei_ausprobieren(self):
        if self.abbruch_flagge:
            tk.messagebox.showerror(title="Fehler!",
                                    message = "Kann Arbeitsumgebung nicht starten,\n"
                                              "da die Installation abgebrochen wurde!")

        try:
            global vsc_vorhanden, vsc_kommando, kommando, version
            if version < VSC_MINDEST_VERSION:
                tk.messagebox.showerror(title="Fehler!",
                                        message='Keine aktuelle Visual Studio Code Version!\n'
                                                'Bitte erst Installation durch Klicken auf '
                                                '"Start" ausführen.')
                return
            elif not os.path.exists(softwareverzeichnis):
                tk.messagebox.showerror(title="Fehler!",
                                        message='MLW-Spezialfotware noch nicht installiert!\n'
                                                'Bitte erst Installation durch Klicken auf '
                                                '"Start" ausführen.')
                return

            self.schreibe_log('Führe aus: ' + kommando)
            if platform.system() == "Windows":
                popen_cmd = [kommando, arbeitsverzeichnis,
                             os.path.join(arbeitsverzeichnis, 'Beispiel.mlw'),
                             os.path.join(softwareverzeichnis, 'MLW_Notation_Beschreibung.md')]

            else:
                # Linux subprocess.Popen bug?
                popen_cmd = [" ".join([kommando, arbeitsverzeichnis,
                                      os.path.join(arbeitsverzeichnis, 'Beispiel.mlw'),
                                      os.path.join(softwareverzeichnis,
                                                   'MLW_Notation_Beschreibung.md')])]
            proc = subprocess.Popen(popen_cmd, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            # subprocess.run wartet anders als subprocess.Popen auf die Beendigung des Unterprozesses,
            # was hier nicht erwünscht ist.
            # subprocess.run([vsc_kommando, arbeitsverzeichnis,
            #                 os.path.join(arbeitsverzeichnis, 'Beispiel.mlw'),
            #                 os.path.join(softwareverzeichnis, 'MLW_Notation_Beschreibung.md')])
        except FileNotFoundError as e:
            tk.messagebox.showerror(title="Fehler!",
                                    message="Visual Studio Code Editor nicht gefunden\n"
                                            "oder gar nicht installiert.\n\nFehlermeldung:\n"
                                            + str(e))

    def bei_beende(self):
        self.destroy()
        self.quit()

    def bei_endeknopf(self):
        self.brich_ab()
        if self.arbeiter and self.arbeiter.is_alive():
            self.schreibe_log('Warte auf Abbruch der Installation...')
            def ende():
                if self.lies_abbruch_flagge() == False:
                    self.bei_beende()
                else:
                    self.after(200, ende)
            self.after(200, ende)
        else:
            self.bei_beende()


#######################################################################
#
# Rumpfprogramm
#
#######################################################################


if __name__ == "__main__":
    # # debug: lies_versionshinweise()
    # import sys
    # vstr, vtpl, hinweise = lies_versionshinweise('.')
    # print(hinweise)
    # sys.exit(0)
    anwendung = MLWInstallationsAnwendung()
    anwendung.lösche_log()
    anwendung.mainloop()

