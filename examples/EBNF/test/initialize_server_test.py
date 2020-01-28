#!/usr/bin/env python

import asyncio
import sys



request_1 = """Content-Length: 4642

{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "initialize",
  "params": {
    "processId": 3406,
    "rootPath": "/home/eckhart/Entwicklung/DHParser/examples/json",
    "rootUri": "file:///home/eckhart/Entwicklung/DHParser/examples/json",
    "capabilities": {
      "workspace": {
        "applyEdit": true,
        "workspaceEdit": {
          "documentChanges": true
        },
        "didChangeConfiguration": {
          "dynamicRegistration": true
        },
        "didChangeWatchedFiles": {
          "dynamicRegistration": true
        },
        "symbol": {
          "dynamicRegistration": true,
          "symbolKind": {
            "valueSet": [
              1,
              2,
              3,
              4,
              5,
              6,
              7,
              8,
              9,
              10,
              11,
              12,
              13,
              14,
              15,
              16,
              17,
              18,
              19,
              20,
              21,
              22,
              23,
              24,
              25,
              26
            ]
          }
        },
        "executeCommand": {
          "dynamicRegistration": true
        },
        "configuration": true,
        "workspaceFolders": true
      },
      "textDocument": {
        "publishDiagnostics": {
          "relatedInformation": true
        },
        "synchronization": {
          "dynamicRegistration": true,
          "willSave": true,
          "willSaveWaitUntil": true,
          "didSave": true
        },
        "completion": {
          "dynamicRegistration": true,
          "contextSupport": true,
          "completionItem": {
            "snippetSupport": true,
            "commitCharactersSupport": true,
            "documentationFormat": [
              "markdown",
              "plaintext"
            ],
            "deprecatedSupport": true
          },
          "completionItemKind": {
            "valueSet": [
              1,
              2,
              3,
              4,
              5,
              6,
              7,
              8,
              9,
              10,
              11,
              12,
              13,
              14,
              15,
              16,
              17,
              18,
              19,
              20,
              21,
              22,
              23,
              24,
              25
            ]
          }
        },
        "hover": {
          "dynamicRegistration": true,
          "contentFormat": [
            "markdown",
            "plaintext"
          ]
        },
        "signatureHelp": {
          "dynamicRegistration": true,
          "signatureInformation": {
            "documentationFormat": [
              "markdown",
              "plaintext"
            ]
          }
        },
        "definition": {
          "dynamicRegistration": true
        },
        "references": {
          "dynamicRegistration": true
        },
        "documentHighlight": {
          "dynamicRegistration": true
        },
        "documentSymbol": {
          "dynamicRegistration": true,
          "symbolKind": {
            "valueSet": [
              1,
              2,
              3,
              4,
              5,
              6,
              7,
              8,
              9,
              10,
              11,
              12,
              13,
              14,
              15,
              16,
              17,
              18,
              19,
              20,
              21,
              22,
              23,
              24,
              25,
              26
            ]
          }
        },
        "codeAction": {
          "dynamicRegistration": true
        },
        "codeLens": {
          "dynamicRegistration": true
        },
        "formatting": {
          "dynamicRegistration": true
        },
        "rangeFormatting": {
          "dynamicRegistration": true
        },
        "onTypeFormatting": {
          "dynamicRegistration": true
        },
        "rename": {
          "dynamicRegistration": true
        },
        "documentLink": {
          "dynamicRegistration": true
        },
        "typeDefinition": {
          "dynamicRegistration": true
        },
        "implementation": {
          "dynamicRegistration": true
        },
        "colorProvider": {
          "dynamicRegistration": true
        }
      }
    },
    "trace": "verbose",
    "workspaceFolders": [
      {
        "uri": "file:///home/eckhart/Entwicklung/DHParser/examples/json",
        "name": "json"
      }
    ]
  }
}
"""

request_2 = """Content-Length: 60

{"jsonrpc":"2.0","id":0,"method":"initialized","params":{}}
"""


async def initialization(host='127.0.0.1', port=8888):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print('request_1')
        writer.write(request_1.encode())
        response = (await reader.read(8192)).decode()
        print(response)
        print('request_2')
        writer.write(request_2.encode())
        print('r_2 sent')
        # response = (await reader.read(8192)).decode()
        # print('r_2 response received')
        # print(response)
        writer.close()
        if sys.version_info >= (3, 7):
            await writer.wait_closed()
    except ConnectionRefusedError:
        print("Could not connect to server %s on port %i" % (host, port))


if __name__ == '__main__':
    asyncio.run(initialization())

