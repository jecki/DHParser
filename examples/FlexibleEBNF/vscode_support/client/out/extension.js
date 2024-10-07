"use strict";
/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
/* See the VSCode-API: https://code.visualstudio.com/api
   and https://code.visualstudio.com/api/references/vscode-api */
const net = require("net");
const vscode_1 = require("vscode");
const vscode_languageclient_1 = require("vscode-languageclient");
let client;
// import * as path from 'path';
// function startLangServer(command: string): Disposable {
//     const serverOptions: ServerOptions = {
//         command: command,
//     };
//     const clientOptions: LanguageClientOptions = {
//         documentSelector: [{scheme: 'file', language: 'json'}],
//     };
//     return new LanguageClient(command, serverOptions, clientOptions).start();
// }
let defaultPort = 8888;
function startLangServerStream(command, args) {
    const serverOptions = {
        command,
        args,
    };
    // log channel
    const logChannel = {
        name: 'consoleLogger',
        // Only append the logs but send them later
        append(value) {
            console.log('append: ' + value + '.');
        },
        appendLine(value) {
            console.log('appendLine ' + value + '.');
        },
        clear() { console.log('clear()'); },
        show() { console.log('show()'); },
        hide() { console.log('hide()'); },
        dispose() { console.log('dispose()'); }
    };
    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'ebnf' }],
        synchronize: {
            // Notify the server about file changes to '.clientrc files contained in the workspace
            fileEvents: vscode_1.workspace.createFileSystemWatcher('**/.clientrc')
        },
        // outputChannel: logChannel,
        initializationFailedHandler: function (error) {
            console.log('InitializationFailed');
            console.log(error.toString());
            return false;
        }
    };
    console.log('activating language server connector ' + args.toString());
    return new vscode_languageclient_1.LanguageClient(command, `ebnf stream lang server`, serverOptions, clientOptions).start();
}
function startLangServerTCP(addr) {
    const serverOptions = function () {
        return new Promise((resolve, reject) => {
            var client = new net.Socket();
            client.connect(addr, "127.0.0.1", function () {
                resolve({
                    reader: client,
                    writer: client
                });
            });
            console.log('connection created');
        });
    };
    // log channel
    const logChannel = {
        name: 'consoleLogger',
        // Only append the logs but send them later
        append(value) {
            console.log('append: ' + value + '.');
        },
        appendLine(value) {
            console.log('appendLine ' + value + '.');
        },
        clear() { console.log('clear()'); },
        show() { console.log('show()'); },
        hide() { console.log('hide()'); },
        dispose() { console.log('dispose()'); }
    };
    // Options to control the language client
    let clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'ebnf' }],
        synchronize: {
            // Notify the server about file changes to '.clientrc files contained in the workspace
            fileEvents: vscode_1.workspace.createFileSystemWatcher('**/.clientrc')
        },
        // outputChannel: logChannel,
        initializationFailedHandler: function (error) {
            console.log('InitializationFailed');
            console.log(error.toString());
            return false;
        }
    };
    client = new vscode_languageclient_1.LanguageClient('EBNFLanguageServer', `ebnf tcp lang server (port ${addr})`, serverOptions, clientOptions);
    let disposable = client.start();
    return disposable;
}
function activate(context) {
    let disposable = startLangServerStream("python", ["FlexibleEBNFServer.py", "--stream", "--logging"]);
    // let disposable = startLangServerTCP(defaultPort);
    context.subscriptions.push(disposable);
}
exports.activate = activate;
function deactivate() {
    if (!client) {
        return undefined;
    }
    console.log('stop lsp client');
    return client.stop();
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map