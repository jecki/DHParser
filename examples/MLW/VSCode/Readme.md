Visual Studio Code Unterstütztung
=================================

Zum installieren der VSCode-Unterstützung müssen die
Unterverzeichnisse `mlwcolors` und `mlwquelle` in das
Konfigurationsverzeichnis von VSCode ("~/.vscode") kopiert oder von
dort verlinkt werden. Die `tasks.json`-Datei gehört in das
`.vscode`-Verzeichnis unterhalb des Hauptverzeichnisses des Projekts,
also z.B. `MLW/.vscode`. Sie wird dann ausgewertet und die darin
angegebenen Aufgaben in Visual Studio Code verfügbar gemacht, wenn das
Hauptverzeichnis in VSCode (im Beispiel `MLW`) geöffnet wird.
