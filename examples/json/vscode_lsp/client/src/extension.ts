/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */

import * as net from 'net';
import { workspace, commands, Disposable, ExtensionContext, OutputChannel } from 'vscode';

import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	TransportKind,
	InitializeError
} from 'vscode-languageclient';

import { ResponseError } from 'vscode-languageserver-protocol';
let client: LanguageClient;

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


let defaultPort: number = 8888;


function startLangServerTCP(addr: number) : Disposable {
	const serverOptions: ServerOptions = function() {
		return new Promise((resolve, reject) => {
			var client = new net.Socket();
			client.connect(addr, "127.0.0.1", function() {
				resolve({
					reader: client,
					writer: client
				});
			});
			console.log('connection created');
		});
	};

	const logChannel: OutputChannel = {
		name: 'consoleLogger',
		// Only append the logs but send them later
		append(value: string) {
			console.log('append()');
			console.log(value);
		},
		appendLine(value: string) {
			console.log('appendLine()');
			console.log(value);
		},
		clear() { console.log('clear()'); },
		show() { console.log('show()'); },
		hide() { console.log('hide()'); },
		dispose() { console.log('dispose()'); }
	};

	let clientOptions: LanguageClientOptions = {
		documentSelector: [{scheme: 'file', language: 'json'}],
		// synchronize: {
		// 	// Notify the server about file changes to '.clientrc files contained in the workspace
		// 	fileEvents: workspace.createFileSystemWatcher('**/.clientrc')
		// },
		outputChannel: logChannel,
		initializationFailedHandler: function(error: ResponseError<InitializeError> | Error | any): boolean {
			console.log('InitializationFailed');
			console.log(error.toString());
			return false;
		}
	};

	console.log('starting lang server');
	client = new LanguageClient(
		'JSONLanguageServer',
		`json tcp lang server (port ${addr})`,
		serverOptions,
		clientOptions);
	let disposable = client.start();
	return disposable;
}

export function activate(context: ExtensionContext) {
	console.log('activating language server connector!');
	let disposable = startLangServerTCP(defaultPort);
	context.subscriptions.push(disposable);
}


// export function deactivate(): Thenable<void> | undefined {
// 	if (!client) {
// 		return undefined;
// 	}
// 	console.log('stop lsp client');
// 	return client.stop();
// }
