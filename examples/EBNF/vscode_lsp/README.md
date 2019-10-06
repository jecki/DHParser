# JSON LSP-integration for Visual Studio Code

See <https://code.visualstudio.com/api/language-extensions/language-server-extension-guide>

## Functionality

Client-module for Visual Studio Code to connect jsonServer.py as a language-server for json

## Running the Sample

- Run `npm install` in this folder. This installs all necessary npm modules in the client folder
- Run `python3 ../jsonServer.py --startserver`
- Open VS Code on this folder.
- Press Ctrl+Shift+B to compile the client and server.
- Switch to the Debug viewlet.
- Select `Launch Client` from the drop down.
- Run the launch config.
- If you want to debug the server as well use the launch configuration `Attach to Server`
- In the [Extension Development Host] instance of VSCode, open a document in 'jsonc' language mode.

