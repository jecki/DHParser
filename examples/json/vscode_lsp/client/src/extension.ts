/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */

import * as net from 'net';
import { workspace, Disposable, ExtensionContext } from 'vscode';
// import * as path from 'path';

// function startLangServer(command: string): Disposable {
// 	const serverOptions: ServerOptions = {
// 		command: command,
// 	};
// 	const clientOptions: LanguageClientOptions = {
// 		documentSelector: [{scheme: 'file', language: 'json'}],
// 	};
// 	return new LanguageClient(command, serverOptions, clientOptions).start();
// }

let language: string = "json";
let defaultPort: number = 8888;


function startLangServerTCP(addr: number) : Disposable {
	const serverOptions: ServerOptions = function() {
		return new Promise((resolve, reject) => {
			console.log('creating connection');
			var client = new net.Socket();
			client.connect(addr, "127.0.0.1", function() {
				resolve({
					reader: client,
					writer: client
				});
			});
		});
	};

	const clientOptions: LanguageClientOptions = {
		documentSelector: [{scheme: 'file', language: language}],
		// synchronize: {
		// 	// Notify the server about file changes to '.clientrc files contained in the workspace
		// 	fileEvents: workspace.createFileSystemWatcher('**/.clientrc')
		// }
	};

	return new LanguageClient(`tcp lang server (port ${addr})`,
	serverOptions, clientOptions).start();
}

import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	// TransportKind
} from 'vscode-languageclient';


export function activate(context: ExtensionContext) {
	// context.subscriptions.push(startLangServer("langserver-python", ["python"]));
	// When developing JS/TS, set {"typescript.tsdk": "/dev/null"} in your user settings in the
	// new VSCode window opened via `npm run vscode`.
	console.log('activating language server connector!');
	context.subscriptions.push(startLangServerTCP(defaultPort));
}



// let client: LanguageClient;

// export function activate(context: ExtensionContext) {

// 	// Create the language client and start the client.
// 	client = new LanguageClient(
// 		'languageServerExample',
// 		'Language Server Example',
// 		serverOptions,
// 		clientOptions
// 	);

// 	// Start the client. This will also launch the server
// 	client.start();
// }

// export function deactivate(): Thenable<void> | undefined {
// 	if (!client) {
// 		return undefined;
// 	}
// 	return client.stop();
// }
