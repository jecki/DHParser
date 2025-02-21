# lsp.py - Language Server Protocol data structures and support functions
#
# Copyright 2024  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""Module lsp.py defines (some of) the constants and data structures from
the Language Server Protocol. See:
<https://microsoft.github.io/language-server-protocol/specifications/specification-current/>

EXPERIMENTAL!!!
"""

from __future__ import annotations

from enum import Enum, IntEnum
import sys

assert sys.version_info >= (3, 7), "Python 3.7 or newer is required."

from typing import Union, List, Tuple, Optional, Dict, Any, \
    Iterator, Iterable, Callable

if sys.version_info >= (3, 9, 0):
    from typing import Union, Optional, Any, Generic, TypeVar, Callable, List, Tuple, Dict
    # do not use list, tuple, dict, because contained types won't be forward ref'd
    from collections.abc import Coroutine
else:
    from typing import Union, List, Tuple, Optional, Dict, Any, Generic, TypeVar, Callable, Coroutine


try:
    from DHParser.ts2python.typeddict_shim import TypedDict, GenericTypedDict, NotRequired, Literal
    # Overwrite typing.TypedDict for Runtime-Validation
except ImportError:
    print("Module ts2python.typeddict_shim not found. Only coarse-grained "
          "runtime type-validation of TypedDicts possible")
    try:
        from typing import TypedDict, Literal
    except ImportError:
        try:
            from DHParser.ts2python.typing_extensions import TypedDict, Literal
        except ImportError:
            print(f'Please install the "typing_extensions" module via the shell '
                  f'command "# pip install typing_extensions" before running '
                  f'{__file__} with Python-versions <= 3.11!')

    GenericMeta = type
    class _GenericTypedDictMeta(GenericMeta):
        def __new__(cls, name, bases, ns, total=True):
            return type.__new__(_GenericTypedDictMeta, name, (dict,), ns)
        __call__ = dict
    GenericTypedDict = _GenericTypedDictMeta('TypedDict', (dict,), {})
    GenericTypedDict.__module__ = __name__


try:
    from DHParser.ts2python.singledispatch_shim import singledispatch, singledispatchmethod
except ImportError:
    print("ts2python.singledispatch_shim not found! @singledispatch-annotation"
          " imported from functools may cause NameErrors on forward-referenced"
          " types.")
    try:
        from functools import singledispatch, singledispatchmethod
    except ImportError:
        print(f"functools.singledispatchmethod does not exist in Python Version "
              f"{sys.version}. This module may therefore fail to run if "
              f"singledispatchmethod is needed, anywhere!")

# from DHParser.json_validation import validate_type, type_check, TypedDict


#######################################################################
#
# Language-Server-Protocol functions
#
#######################################################################


# general #############################################################

# def get_lsp_methods(cls: Any, prefix: str= 'lsp_') -> List[str]:
#     """Returns the language-server-protocol-method-names from class ``cls``.
#     Methods are selected based on the prefix and their name converted in
#     accordance with the LSP-specification."""
#     return [gen_lsp_name(fn, prefix) for fn in lsp_candidates(cls, prefix)]


def lsp_candidates(cls: Any, prefix: str = 'lsp_') -> Iterator[str]:
    """Returns an iterator over all method names from a class that either
    have a certain prefix or, if no prefix was given, all non-special and
    non-private-methods of the class."""
    assert not prefix[:1] == '_'
    if prefix:
        # return [fn for fn in dir(cls) if fn.startswith(prefix) and callable(getattr(cls, fn))]
        for fn in dir(cls):
            if fn[:len(prefix)] == prefix and callable(getattr(cls, fn)):
                yield fn
    else:
        # return [fn for fn in dir(cls) if not fn.startswith('_') and callable(getattr(cls, fn))]
        for fn in dir(cls):
            if not fn[:1] == '_' and callable(getattr(cls, fn)):
                yield fn


def gen_lsp_name(func_name: str, prefix: str = 'lsp_') -> str:
    """Generates the name of an lsp-method from a function name,
    e.g. "lsp_S_cancelRequest" -> "$/cancelRequest" """
    assert func_name[:len(prefix)] == prefix
    return func_name[len(prefix):].replace('_', '/').replace('S/', '$/')


def gen_lsp_table(lsp_funcs_or_instance: Union[Iterable[Callable], Any],
                  prefix: str = 'lsp_') -> Dict[str, Callable]:
    """Creates an RPC from a list of functions or from the methods
    of a class that implement the language server protocol.
    The dictionary keys are derived from the function name by replacing an
    underscore _ with a slash / and a single capital S with a $-sign.
    if ``prefix`` is not the empty string only functions or methods that start
    with ``prefix`` will be added to the table. The prefix will be removed
    before converting the functions' name to a dictionary key.

    >>> class LSP:
    ...     def lsp_initialize(self, **kw):
    ...         pass  # return InitializeResult
    ...     def lsp_shutdown(self, **kw):
    ...         pass
    >>> lsp = LSP()
    >>> gen_lsp_table(lsp, 'lsp_').keys()
    dict_keys(['initialize', 'shutdown'])
    """
    if isinstance(lsp_funcs_or_instance, Iterable):
        assert all(callable(func) for func in lsp_funcs_or_instance)
        rpc_table = {gen_lsp_name(func.__name__, prefix): func for func in lsp_funcs_or_instance}
    else:
        # assume lsp_funcs_or_instance is the instance of a class
        cls = lsp_funcs_or_instance
        rpc_table = {gen_lsp_name(fn, prefix): getattr(cls, fn)
                     for fn in lsp_candidates(cls, prefix)}
    return rpc_table


# textDocument/completion #############################################

def shortlist(long_list: List[str], typed: str, lo: int = 0, hi: int = -1) -> Tuple[int, int]:
    if not typed:
        return 0, 0
    if hi < 0:
        hi = len(long_list)
    import bisect
    a = bisect.bisect_left(long_list, typed, lo, hi)
    b = bisect.bisect_left(long_list, typed[:-1] + chr(ord(typed[-1]) + 1), lo, hi)
    return a, b


#######################################################################
#
# Language-Server-Protocol data structures (AUTOGENERATED: Don't edit!)
#
#######################################################################


##### BEGIN OF LSP SPECS



integer = float

uinteger = float

decimal = float

LSPAny = Union['LSPObject', 'LSPArray', str, int, float, bool, None]

LSPObject = Dict[str, LSPAny]

LSPArray = List[LSPAny]


class Message(TypedDict, total=True):
    jsonrpc: str


class RequestMessage(Message, TypedDict, total=False):
    id: Union[int, str]
    method: str
    params: Union[List, Dict, None]


class ResponseMessage(Message, TypedDict, total=False):
    id: Union[int, str, None]
    result: Optional[LSPAny]
    error: Optional['ResponseError']


class ResponseError(TypedDict, total=False):
    code: int
    message: str
    data: Optional[LSPAny]

class ErrorCodes(IntEnum):
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    jsonrpcReservedErrorRangeStart = -32099
    serverErrorStart = jsonrpcReservedErrorRangeStart
    ServerNotInitialized = -32002
    UnknownErrorCode = -32001
    jsonrpcReservedErrorRangeEnd = -32000
    serverErrorEnd = jsonrpcReservedErrorRangeEnd
    lspReservedErrorRangeStart = -32899
    RequestFailed = -32803
    ServerCancelled = -32802
    ContentModified = -32801
    RequestCancelled = -32800
    lspReservedErrorRangeEnd = -32800


class NotificationMessage(Message, TypedDict, total=False):
    method: str
    params: Union[List, Dict, None]


class CancelParams(TypedDict, total=True):
    id: Union[int, str]

ProgressToken = Union[int, str]

T = TypeVar('T')

class ProgressParams(Generic[T], GenericTypedDict, total=True):
    token: ProgressToken
    value: T


class HoverParams(TypedDict, total=True):
    class Position_0(TypedDict, total=True):
        line: int
        character: int
    textDocument: str
    position: Position_0


class HoverResult(TypedDict, total=True):
    value: str

DocumentUri = str

URI = str


class RegularExpressionsClientCapabilities(TypedDict, total=False):
    engine: str
    version: Optional[str]

EOL: List[str] = ['\n', '\r\n', '\r']


class Position(TypedDict, total=True):
    line: int
    character: int

PositionEncodingKind = str

class PositionEncodingKind(Enum):
    UTF8 = 'utf-8'
    UTF16 = 'utf-16'
    UTF32 = 'utf-32'


class Range(TypedDict, total=True):
    start: Position
    end: Position


class TextDocumentItem(TypedDict, total=True):
    uri: DocumentUri
    languageId: str
    version: int
    text: str


class TextDocumentIdentifier(TypedDict, total=True):
    uri: DocumentUri


class VersionedTextDocumentIdentifier(TextDocumentIdentifier, TypedDict, total=True):
    version: int


class OptionalVersionedTextDocumentIdentifier(TextDocumentIdentifier, TypedDict, total=True):
    version: Union[int, None]


class TextDocumentPositionParams(TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    position: Position


class DocumentFilter(TypedDict, total=False):
    language: Optional[str]
    scheme: Optional[str]
    pattern: Optional[str]

DocumentSelector = List[DocumentFilter]


class StringValue(TypedDict, total=True):
    kind: str
    value: str


class TextEdit(TypedDict, total=True):
    range: Range
    newText: str


class ChangeAnnotation(TypedDict, total=False):
    label: str
    needsConfirmation: Optional[bool]
    description: Optional[str]

ChangeAnnotationIdentifier = str


class AnnotatedTextEdit(TextEdit, TypedDict, total=True):
    annotationId: ChangeAnnotationIdentifier


class SnippetTextEdit(TypedDict, total=False):
    range: Range
    snippet: StringValue
    annotationId: Optional[ChangeAnnotationIdentifier]


class TextDocumentEdit(TypedDict, total=True):
    textDocument: OptionalVersionedTextDocumentIdentifier
    edits: List[Union[TextEdit, AnnotatedTextEdit, SnippetTextEdit]]


class Location(TypedDict, total=True):
    uri: DocumentUri
    range: Range


class LocationLink(TypedDict, total=False):
    originSelectionRange: Optional[Range]
    targetUri: DocumentUri
    targetRange: Range
    targetSelectionRange: Range


class Diagnostic(TypedDict, total=False):
    range: Range
    severity: Optional['DiagnosticSeverity']
    code: Union[int, str, None]
    codeDescription: Optional['CodeDescription']
    source: Optional[str]
    message: Union[str, 'MarkupContent']
    tags: Optional[List['DiagnosticTag']]
    relatedInformation: Optional[List['DiagnosticRelatedInformation']]
    data: Optional[LSPAny]

class DiagnosticSeverity(IntEnum):
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4

# commented out, because there is already an enumeration with the same name
# DiagnosticSeverity = int

class DiagnosticTag(IntEnum):
    Unnecessary = 1
    Deprecated = 2

# commented out, because there is already an enumeration with the same name
# DiagnosticTag = int


class DiagnosticRelatedInformation(TypedDict, total=True):
    location: Location
    message: str


class CodeDescription(TypedDict, total=True):
    href: URI


class Command(TypedDict, total=False):
    title: str
    tooltip: Optional[str]
    command: str
    arguments: Optional[List[LSPAny]]

class MarkupKind(Enum):
    PlainText = 'plaintext'
    Markdown = 'markdown'

# commented out, because there is already an enumeration with the same name
# MarkupKind = str


class MarkupContent(TypedDict, total=True):
    kind: MarkupKind
    value: str


class MarkdownClientCapabilities(TypedDict, total=False):
    parser: str
    version: Optional[str]
    allowedTags: Optional[List[str]]


class CreateFileOptions(TypedDict, total=False):
    overwrite: Optional[bool]
    ignoreIfExists: Optional[bool]


class CreateFile(TypedDict, total=False):
    kind: str
    uri: DocumentUri
    options: Optional[CreateFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class RenameFileOptions(TypedDict, total=False):
    overwrite: Optional[bool]
    ignoreIfExists: Optional[bool]


class RenameFile(TypedDict, total=False):
    kind: str
    oldUri: DocumentUri
    newUri: DocumentUri
    options: Optional[RenameFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class DeleteFileOptions(TypedDict, total=False):
    recursive: Optional[bool]
    ignoreIfNotExists: Optional[bool]


class DeleteFile(TypedDict, total=False):
    kind: str
    uri: DocumentUri
    options: Optional[DeleteFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class WorkspaceEdit(TypedDict, total=False):
    changes: Optional[Dict[DocumentUri, List[TextEdit]]]
    documentChanges: Union[List[TextDocumentEdit], List[Union[TextDocumentEdit, CreateFile, RenameFile, DeleteFile]], None]
    changeAnnotations: Optional[Dict[str, ChangeAnnotation]]


class WorkspaceEditClientCapabilities(TypedDict, total=False):
    class ChangeAnnotationSupport_0(TypedDict, total=False):
        groupsOnLabel: Optional[bool]
    documentChanges: Optional[bool]
    resourceOperations: Optional[List['ResourceOperationKind']]
    failureHandling: Optional['FailureHandlingKind']
    normalizesLineEndings: Optional[bool]
    changeAnnotationSupport: Optional[ChangeAnnotationSupport_0]
    metadataSupport: Optional[bool]
    snippetEditSupport: Optional[bool]

ResourceOperationKind = str

class ResourceOperationKind(Enum):
    Create = 'create'
    Rename = 'rename'
    Delete = 'delete'

FailureHandlingKind = str

class FailureHandlingKind(Enum):
    Abort = 'abort'
    Transactional = 'transactional'
    TextOnlyTransactional = 'textOnlyTransactional'
    Undo = 'undo'


class WorkDoneProgressBegin(TypedDict, total=False):
    kind: str
    title: str
    cancellable: Optional[bool]
    message: Optional[str]
    percentage: Optional[int]


class WorkDoneProgressReport(TypedDict, total=False):
    kind: str
    cancellable: Optional[bool]
    message: Optional[str]
    percentage: Optional[int]


class WorkDoneProgressEnd(TypedDict, total=False):
    kind: str
    message: Optional[str]


class WorkDoneProgressParams(TypedDict, total=False):
    workDoneToken: Optional[ProgressToken]


class WorkDoneProgressOptions(TypedDict, total=False):
    workDoneProgress: Optional[bool]


class PartialResultParams(TypedDict, total=False):
    partialResultToken: Optional[ProgressToken]

TraceValue = str


class InitializeParams(WorkDoneProgressParams, TypedDict, total=False):
    class ClientInfo_0(TypedDict, total=False):
        name: str
        version: Optional[str]
    processId: Union[int, None]
    clientInfo: Optional[ClientInfo_0]
    locale: Optional[str]
    rootPath: Union[str, None]
    rootUri: Union[DocumentUri, None]
    initializationOptions: Optional[LSPAny]
    capabilities: 'ClientCapabilities'
    trace: Optional[TraceValue]
    workspaceFolders: Union[List['WorkspaceFolder'], None]


class TextDocumentClientCapabilities(TypedDict, total=False):
    synchronization: Optional['TextDocumentSyncClientCapabilities']
    completion: Optional['CompletionClientCapabilities']
    hover: Optional['HoverClientCapabilities']
    signatureHelp: Optional['SignatureHelpClientCapabilities']
    declaration: Optional['DeclarationClientCapabilities']
    definition: Optional['DefinitionClientCapabilities']
    typeDefinition: Optional['TypeDefinitionClientCapabilities']
    implementation: Optional['ImplementationClientCapabilities']
    references: Optional['ReferenceClientCapabilities']
    documentHighlight: Optional['DocumentHighlightClientCapabilities']
    documentSymbol: Optional['DocumentSymbolClientCapabilities']
    codeAction: Optional['CodeActionClientCapabilities']
    codeLens: Optional['CodeLensClientCapabilities']
    documentLink: Optional['DocumentLinkClientCapabilities']
    colorProvider: Optional['DocumentColorClientCapabilities']
    formatting: Optional['DocumentFormattingClientCapabilities']
    rangeFormatting: Optional['DocumentRangeFormattingClientCapabilities']
    onTypeFormatting: Optional['DocumentOnTypeFormattingClientCapabilities']
    rename: Optional['RenameClientCapabilities']
    publishDiagnostics: Optional['PublishDiagnosticsClientCapabilities']
    foldingRange: Optional['FoldingRangeClientCapabilities']
    selectionRange: Optional['SelectionRangeClientCapabilities']
    linkedEditingRange: Optional['LinkedEditingRangeClientCapabilities']
    callHierarchy: Optional['CallHierarchyClientCapabilities']
    semanticTokens: Optional['SemanticTokensClientCapabilities']
    moniker: Optional['MonikerClientCapabilities']
    typeHierarchy: Optional['TypeHierarchyClientCapabilities']
    inlineValue: Optional['InlineValueClientCapabilities']
    inlayHint: Optional['InlayHintClientCapabilities']
    diagnostic: Optional['DiagnosticClientCapabilities']
    inlineCompletion: Optional['InlineCompletionClientCapabilities']


class NotebookDocumentClientCapabilities(TypedDict, total=True):
    synchronization: 'NotebookDocumentSyncClientCapabilities'


class ClientCapabilities(TypedDict, total=False):
    class Workspace_0(TypedDict, total=False):
        class FileOperations_0(TypedDict, total=False):
            dynamicRegistration: Optional[bool]
            didCreate: Optional[bool]
            willCreate: Optional[bool]
            didRename: Optional[bool]
            willRename: Optional[bool]
            didDelete: Optional[bool]
            willDelete: Optional[bool]
        applyEdit: Optional[bool]
        workspaceEdit: Optional[WorkspaceEditClientCapabilities]
        didChangeConfiguration: Optional['DidChangeConfigurationClientCapabilities']
        didChangeWatchedFiles: Optional['DidChangeWatchedFilesClientCapabilities']
        symbol: Optional['WorkspaceSymbolClientCapabilities']
        executeCommand: Optional['ExecuteCommandClientCapabilities']
        workspaceFolders: Optional[bool]
        configuration: Optional[bool]
        semanticTokens: Optional['SemanticTokensWorkspaceClientCapabilities']
        codeLens: Optional['CodeLensWorkspaceClientCapabilities']
        fileOperations: Optional[FileOperations_0]
        inlineValue: Optional['InlineValueWorkspaceClientCapabilities']
        inlayHint: Optional['InlayHintWorkspaceClientCapabilities']
        diagnostics: Optional['DiagnosticWorkspaceClientCapabilities']
    class Window_0(TypedDict, total=False):
        workDoneProgress: Optional[bool]
        showMessage: Optional['ShowMessageRequestClientCapabilities']
        showDocument: Optional['ShowDocumentClientCapabilities']
    class General_0(TypedDict, total=False):
        class StaleRequestSupport_0(TypedDict, total=True):
            cancel: bool
            retryOnContentModified: List[str]
        staleRequestSupport: Optional[StaleRequestSupport_0]
        regularExpressions: Optional[RegularExpressionsClientCapabilities]
        markdown: Optional[MarkdownClientCapabilities]
        positionEncodings: Optional[List[PositionEncodingKind]]
    workspace: Optional[Workspace_0]
    textDocument: Optional[TextDocumentClientCapabilities]
    notebookDocument: Optional[NotebookDocumentClientCapabilities]
    window: Optional[Window_0]
    general: Optional[General_0]
    experimental: Optional[LSPAny]


class InitializeResult(TypedDict, total=False):
    class ServerInfo_0(TypedDict, total=False):
        name: str
        version: Optional[str]
    capabilities: 'ServerCapabilities'
    serverInfo: Optional[ServerInfo_0]

class InitializeErrorCodes(IntEnum):
    unknownProtocolVersion = 1

# commented out, because there is already an enumeration with the same name
# InitializeErrorCodes = int


class InitializeError(TypedDict, total=True):
    retry: bool


class ServerCapabilities(TypedDict, total=False):
    class TextDocument_0(TypedDict, total=False):
        class Diagnostic_0(TypedDict, total=False):
            markupMessageSupport: Optional[bool]
        diagnostic: Optional[Diagnostic_0]
    class Workspace_0(TypedDict, total=False):
        class FileOperations_0(TypedDict, total=False):
            didCreate: Optional['FileOperationRegistrationOptions']
            willCreate: Optional['FileOperationRegistrationOptions']
            didRename: Optional['FileOperationRegistrationOptions']
            willRename: Optional['FileOperationRegistrationOptions']
            didDelete: Optional['FileOperationRegistrationOptions']
            willDelete: Optional['FileOperationRegistrationOptions']
        workspaceFolders: Optional['WorkspaceFoldersServerCapabilities']
        fileOperations: Optional[FileOperations_0]
    positionEncoding: Optional[PositionEncodingKind]
    textDocumentSync: Union['TextDocumentSyncOptions', 'TextDocumentSyncKind', None]
    notebookDocumentSync: Union['NotebookDocumentSyncOptions', 'NotebookDocumentSyncRegistrationOptions', None]
    completionProvider: Optional['CompletionOptions']
    hoverProvider: Union[bool, 'HoverOptions', None]
    signatureHelpProvider: Optional['SignatureHelpOptions']
    declarationProvider: Union[bool, 'DeclarationOptions', 'DeclarationRegistrationOptions', None]
    definitionProvider: Union[bool, 'DefinitionOptions', None]
    typeDefinitionProvider: Union[bool, 'TypeDefinitionOptions', 'TypeDefinitionRegistrationOptions', None]
    implementationProvider: Union[bool, 'ImplementationOptions', 'ImplementationRegistrationOptions', None]
    referencesProvider: Union[bool, 'ReferenceOptions', None]
    documentHighlightProvider: Union[bool, 'DocumentHighlightOptions', None]
    documentSymbolProvider: Union[bool, 'DocumentSymbolOptions', None]
    codeActionProvider: Union[bool, 'CodeActionOptions', None]
    codeLensProvider: Optional['CodeLensOptions']
    documentLinkProvider: Optional['DocumentLinkOptions']
    colorProvider: Union[bool, 'DocumentColorOptions', 'DocumentColorRegistrationOptions', None]
    documentFormattingProvider: Union[bool, 'DocumentFormattingOptions', None]
    documentRangeFormattingProvider: Union[bool, 'DocumentRangeFormattingOptions', None]
    documentOnTypeFormattingProvider: Optional['DocumentOnTypeFormattingOptions']
    renameProvider: Union[bool, 'RenameOptions', None]
    foldingRangeProvider: Union[bool, 'FoldingRangeOptions', 'FoldingRangeRegistrationOptions', None]
    executeCommandProvider: Optional['ExecuteCommandOptions']
    selectionRangeProvider: Union[bool, 'SelectionRangeOptions', 'SelectionRangeRegistrationOptions', None]
    linkedEditingRangeProvider: Union[bool, 'LinkedEditingRangeOptions', 'LinkedEditingRangeRegistrationOptions', None]
    callHierarchyProvider: Union[bool, 'CallHierarchyOptions', 'CallHierarchyRegistrationOptions', None]
    semanticTokensProvider: Union['SemanticTokensOptions', 'SemanticTokensRegistrationOptions', None]
    monikerProvider: Union[bool, 'MonikerOptions', 'MonikerRegistrationOptions', None]
    typeHierarchyProvider: Union[bool, 'TypeHierarchyOptions', 'TypeHierarchyRegistrationOptions', None]
    inlineValueProvider: Union[bool, 'InlineValueOptions', 'InlineValueRegistrationOptions', None]
    inlayHintProvider: Union[bool, 'InlayHintOptions', 'InlayHintRegistrationOptions', None]
    diagnosticProvider: Union['DiagnosticOptions', 'DiagnosticRegistrationOptions', None]
    workspaceSymbolProvider: Union[bool, 'WorkspaceSymbolOptions', None]
    inlineCompletionProvider: Union[bool, 'InlineCompletionOptions', None]
    textDocument: Optional[TextDocument_0]
    workspace: Optional[Workspace_0]
    experimental: Optional[LSPAny]


class InitializedParams(TypedDict, total=True):
    pass


class Registration(TypedDict, total=False):
    id: str
    method: str
    registerOptions: Optional[LSPAny]


class RegistrationParams(TypedDict, total=True):
    registrations: List[Registration]


class StaticRegistrationOptions(TypedDict, total=False):
    id: Optional[str]


class TextDocumentRegistrationOptions(TypedDict, total=True):
    documentSelector: Union[DocumentSelector, None]


class Unregistration(TypedDict, total=True):
    id: str
    method: str


class UnregistrationParams(TypedDict, total=True):
    unregisterations: List[Unregistration]


class SetTraceParams(TypedDict, total=True):
    value: TraceValue


class LogTraceParams(TypedDict, total=False):
    message: str
    verbose: Optional[str]

class TextDocumentSyncKind(IntEnum):
    None_ = 0
    Full = 1
    Incremental = 2

# commented out, because there is already an enumeration with the same name
# TextDocumentSyncKind = int


class TextDocumentSyncOptions(TypedDict, total=False):
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]


class DidOpenTextDocumentParams(TypedDict, total=True):
    textDocument: TextDocumentItem


class TextDocumentChangeRegistrationOptions(TextDocumentRegistrationOptions, TypedDict, total=True):
    syncKind: TextDocumentSyncKind


class DidChangeTextDocumentParams(TypedDict, total=True):
    textDocument: VersionedTextDocumentIdentifier
    contentChanges: List['TextDocumentContentChangeEvent']

class TextDocumentContentChangeEvent_0(TypedDict, total=False):
    range: Range
    rangeLength: Optional[int]
    text: str
class TextDocumentContentChangeEvent_1(TypedDict, total=True):
    text: str
TextDocumentContentChangeEvent = Union[TextDocumentContentChangeEvent_0, TextDocumentContentChangeEvent_1]


class WillSaveTextDocumentParams(TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    reason: 'TextDocumentSaveReason'

class TextDocumentSaveReason(IntEnum):
    Manual = 1
    AfterDelay = 2
    FocusOut = 3

# commented out, because there is already an enumeration with the same name
# TextDocumentSaveReason = int


class SaveOptions(TypedDict, total=False):
    includeText: Optional[bool]


class TextDocumentSaveRegistrationOptions(TextDocumentRegistrationOptions, TypedDict, total=False):
    includeText: Optional[bool]


class DidSaveTextDocumentParams(TypedDict, total=False):
    textDocument: TextDocumentIdentifier
    text: Optional[str]


class DidCloseTextDocumentParams(TypedDict, total=True):
    textDocument: TextDocumentIdentifier


class TextDocumentSyncClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    didSave: Optional[bool]


class TextDocumentSyncOptions(TypedDict, total=False):
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    save: Union[bool, SaveOptions, None]


class NotebookDocument(TypedDict, total=False):
    uri: URI
    notebookType: str
    version: int
    metadata: Optional[LSPObject]
    cells: List['NotebookCell']


class NotebookCell(TypedDict, total=False):
    kind: 'NotebookCellKind'
    document: DocumentUri
    metadata: Optional[LSPObject]
    executionSummary: Optional['ExecutionSummary']

class NotebookCellKind(IntEnum):
    Markup = 1
    Code = 2


class ExecutionSummary(TypedDict, total=False):
    executionOrder: int
    success: Optional[bool]


class NotebookCellTextDocumentFilter(TypedDict, total=False):
    notebook: Union[str, 'NotebookDocumentFilter']
    language: Optional[str]

class NotebookDocumentFilter_0(TypedDict, total=False):
    notebookType: str
    scheme: Optional[str]
    pattern: Optional[str]
class NotebookDocumentFilter_1(TypedDict, total=False):
    notebookType: Optional[str]
    scheme: str
    pattern: Optional[str]
class NotebookDocumentFilter_2(TypedDict, total=False):
    notebookType: Optional[str]
    scheme: Optional[str]
    pattern: str
NotebookDocumentFilter = Union[NotebookDocumentFilter_0, NotebookDocumentFilter_1, NotebookDocumentFilter_2]


class NotebookDocumentSyncClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    executionSummarySupport: Optional[bool]


class NotebookDocumentSyncOptions(TypedDict, total=False):
    class NotebookSelector_0(TypedDict, total=False):
        class Cells_0(TypedDict, total=True):
            language: str
        notebook: Union[str, NotebookDocumentFilter]
        cells: Optional[List[Cells_0]]
    class NotebookSelector_1(TypedDict, total=False):
        class Cells_0(TypedDict, total=True):
            language: str
        notebook: Union[str, NotebookDocumentFilter, None]
        cells: List[Cells_0]
    notebookSelector: List[Union[NotebookSelector_0, NotebookSelector_1]]
    save: Optional[bool]


class NotebookDocumentSyncRegistrationOptions(NotebookDocumentSyncOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class DidOpenNotebookDocumentParams(TypedDict, total=True):
    notebookDocument: NotebookDocument
    cellTextDocuments: List[TextDocumentItem]


class DidChangeNotebookDocumentParams(TypedDict, total=True):
    notebookDocument: 'VersionedNotebookDocumentIdentifier'
    change: 'NotebookDocumentChangeEvent'


class VersionedNotebookDocumentIdentifier(TypedDict, total=True):
    version: int
    uri: URI


class NotebookDocumentChangeEvent(TypedDict, total=False):
    class Cells_0(TypedDict, total=False):
        class Structure_0(TypedDict, total=False):
            array: 'NotebookCellArrayChange'
            didOpen: Optional[List[TextDocumentItem]]
            didClose: Optional[List[TextDocumentIdentifier]]
        class TextContent_0(TypedDict, total=True):
            document: VersionedTextDocumentIdentifier
            changes: List[TextDocumentContentChangeEvent]
        structure: Optional[Structure_0]
        data: Optional[List[NotebookCell]]
        textContent: Optional[List[TextContent_0]]
    metadata: Optional[LSPObject]
    cells: Optional[Cells_0]


class NotebookCellArrayChange(TypedDict, total=False):
    start: int
    deleteCount: int
    cells: Optional[List[NotebookCell]]


class DidSaveNotebookDocumentParams(TypedDict, total=True):
    notebookDocument: 'NotebookDocumentIdentifier'


class DidCloseNotebookDocumentParams(TypedDict, total=True):
    notebookDocument: 'NotebookDocumentIdentifier'
    cellTextDocuments: List[TextDocumentIdentifier]


class NotebookDocumentIdentifier(TypedDict, total=True):
    uri: URI


class DeclarationClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class DeclarationOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class DeclarationRegistrationOptions(DeclarationOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class DeclarationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    pass


class DefinitionClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class DefinitionOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class DefinitionRegistrationOptions(TextDocumentRegistrationOptions, DefinitionOptions, TypedDict, total=True):
    pass


class DefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    pass


class TypeDefinitionClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class TypeDefinitionOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class TypeDefinitionRegistrationOptions(TextDocumentRegistrationOptions, TypeDefinitionOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class TypeDefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    pass


class ImplementationClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class ImplementationOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class ImplementationRegistrationOptions(TextDocumentRegistrationOptions, ImplementationOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class ImplementationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    pass


class ReferenceClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class ReferenceOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class ReferenceRegistrationOptions(TextDocumentRegistrationOptions, ReferenceOptions, TypedDict, total=True):
    pass


class ReferenceParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    context: 'ReferenceContext'


class ReferenceContext(TypedDict, total=True):
    includeDeclaration: bool


class CallHierarchyClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class CallHierarchyOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class CallHierarchyRegistrationOptions(TextDocumentRegistrationOptions, CallHierarchyOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class CallHierarchyPrepareParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict, total=True):
    pass


class CallHierarchyItem(TypedDict, total=False):
    name: str
    kind: 'SymbolKind'
    tags: Optional[List['SymbolTag']]
    detail: Optional[str]
    uri: DocumentUri
    range: Range
    selectionRange: Range
    data: Optional[LSPAny]


class CallHierarchyIncomingCallsParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    item: CallHierarchyItem


class CallHierarchyIncomingCall(TypedDict, total=True):
    from_: CallHierarchyItem
    fromRanges: List[Range]


class CallHierarchyOutgoingCallsParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    item: CallHierarchyItem


class CallHierarchyOutgoingCall(TypedDict, total=True):
    to: CallHierarchyItem
    fromRanges: List[Range]

class TypeHierarchyClientCapabilities_0(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
TypeHierarchyClientCapabilities = TypeHierarchyClientCapabilities_0


class TypeHierarchyOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class TypeHierarchyRegistrationOptions(TextDocumentRegistrationOptions, TypeHierarchyOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class TypeHierarchyPrepareParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict, total=True):
    pass


class TypeHierarchyItem(TypedDict, total=False):
    name: str
    kind: 'SymbolKind'
    tags: Optional[List['SymbolTag']]
    detail: Optional[str]
    uri: DocumentUri
    range: Range
    selectionRange: Range
    data: Optional[LSPAny]


class TypeHierarchySupertypesParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    item: TypeHierarchyItem


class TypeHierarchySubtypesParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    item: TypeHierarchyItem


class DocumentHighlightClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class DocumentHighlightOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class DocumentHighlightRegistrationOptions(TextDocumentRegistrationOptions, DocumentHighlightOptions, TypedDict, total=True):
    pass


class DocumentHighlightParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    pass


class DocumentHighlight(TypedDict, total=False):
    range: Range
    kind: Optional['DocumentHighlightKind']

class DocumentHighlightKind(IntEnum):
    Text = 1
    Read = 2
    Write = 3

# commented out, because there is already an enumeration with the same name
# DocumentHighlightKind = int


class DocumentLinkClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    tooltipSupport: Optional[bool]


class DocumentLinkOptions(WorkDoneProgressOptions, TypedDict, total=False):
    resolveProvider: Optional[bool]


class DocumentLinkRegistrationOptions(TextDocumentRegistrationOptions, DocumentLinkOptions, TypedDict, total=True):
    pass


class DocumentLinkParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier


class DocumentLink(TypedDict, total=False):
    range: Range
    target: Optional[URI]
    tooltip: Optional[str]
    data: Optional[LSPAny]


class HoverClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    contentFormat: Optional[List[MarkupKind]]


class HoverOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class HoverRegistrationOptions(TextDocumentRegistrationOptions, HoverOptions, TypedDict, total=True):
    pass


class HoverParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict, total=True):
    pass


class Hover(TypedDict, total=False):
    contents: Union['MarkedString', List['MarkedString'], MarkupContent]
    range: Optional[Range]

class MarkedString_1(TypedDict, total=True):
    language: str
    value: str
MarkedString = Union[str, MarkedString_1]


class CodeLensClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    resolveSupport: Optional['ClientCodeLensResolveOptions']

class ClientCodeLensResolveOptions_0(TypedDict, total=True):
    properties: List[str]
ClientCodeLensResolveOptions = ClientCodeLensResolveOptions_0


class CodeLensOptions(WorkDoneProgressOptions, TypedDict, total=False):
    resolveProvider: Optional[bool]


class CodeLensRegistrationOptions(TextDocumentRegistrationOptions, CodeLensOptions, TypedDict, total=True):
    pass


class CodeLensParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier


class CodeLens(TypedDict, total=False):
    range: Range
    command: Optional[Command]
    data: Optional[LSPAny]


class CodeLensWorkspaceClientCapabilities(TypedDict, total=False):
    refreshSupport: Optional[bool]


class FoldingRangeClientCapabilities(TypedDict, total=False):
    class FoldingRangeKind_0(TypedDict, total=False):
        valueSet: Optional[List['FoldingRangeKind']]
    class FoldingRange_0(TypedDict, total=False):
        collapsedText: Optional[bool]
    dynamicRegistration: Optional[bool]
    rangeLimit: Optional[int]
    lineFoldingOnly: Optional[bool]
    foldingRangeKind: Optional[FoldingRangeKind_0]
    foldingRange: Optional[FoldingRange_0]


class FoldingRangeOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class FoldingRangeRegistrationOptions(TextDocumentRegistrationOptions, FoldingRangeOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class FoldingRangeParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier

class FoldingRangeKind(Enum):
    Comment = 'comment'
    Imports = 'imports'
    Region = 'region'

# commented out, because there is already an enumeration with the same name
# FoldingRangeKind = str


class FoldingRange(TypedDict, total=False):
    startLine: int
    startCharacter: Optional[int]
    endLine: int
    endCharacter: Optional[int]
    kind: Optional[FoldingRangeKind]
    collapsedText: Optional[str]


class FoldingRangeWorkspaceClientCapabilities(TypedDict, total=False):
    refreshSupport: Optional[bool]


class SelectionRangeClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class SelectionRangeOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class SelectionRangeRegistrationOptions(SelectionRangeOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class SelectionRangeParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    positions: List[Position]


class SelectionRange(TypedDict, total=False):
    range: Range
    parent: Optional['SelectionRange']


class DocumentSymbolClientCapabilities(TypedDict, total=False):
    class SymbolKind_0(TypedDict, total=False):
        valueSet: Optional[List['SymbolKind']]
    class TagSupport_0(TypedDict, total=True):
        valueSet: List['SymbolTag']
    dynamicRegistration: Optional[bool]
    symbolKind: Optional[SymbolKind_0]
    hierarchicalDocumentSymbolSupport: Optional[bool]
    tagSupport: Optional[TagSupport_0]
    labelSupport: Optional[bool]


class DocumentSymbolOptions(WorkDoneProgressOptions, TypedDict, total=False):
    label: Optional[str]


class DocumentSymbolRegistrationOptions(TextDocumentRegistrationOptions, DocumentSymbolOptions, TypedDict, total=True):
    pass


class DocumentSymbolParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier

class SymbolKind(IntEnum):
    File = 1
    Module = 2
    Namespace = 3
    Package = 4
    Class = 5
    Method = 6
    Property = 7
    Field = 8
    Constructor = 9
    Enum = 10
    Interface = 11
    Function = 12
    Variable = 13
    Constant = 14
    String = 15
    Number = 16
    Boolean = 17
    Array = 18
    Object = 19
    Key = 20
    Null = 21
    EnumMember = 22
    Struct = 23
    Event = 24
    Operator = 25
    TypeParameter = 26

# commented out, because there is already an enumeration with the same name
# SymbolKind = int

class SymbolTag(IntEnum):
    Deprecated = 1

# commented out, because there is already an enumeration with the same name
# SymbolTag = int


class DocumentSymbol(TypedDict, total=False):
    name: str
    detail: Optional[str]
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    deprecated: Optional[bool]
    range: Range
    selectionRange: Range
    children: Optional[List['DocumentSymbol']]


class SymbolInformation(TypedDict, total=False):
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    deprecated: Optional[bool]
    location: Location
    containerName: Optional[str]

class SemanticTokenTypes(Enum):
    namespace = 'namespace'
    type = 'type'
    class_ = 'class'
    enum = 'enum'
    interface = 'interface'
    struct = 'struct'
    typeParameter = 'typeParameter'
    parameter = 'parameter'
    variable = 'variable'
    property = 'property'
    enumMember = 'enumMember'
    event = 'event'
    function = 'function'
    method = 'method'
    macro = 'macro'
    keyword = 'keyword'
    modifier = 'modifier'
    comment = 'comment'
    string = 'string'
    number = 'number'
    regexp = 'regexp'
    operator = 'operator'
    decorator = 'decorator'

class SemanticTokenModifiers(Enum):
    declaration = 'declaration'
    definition = 'definition'
    readonly = 'readonly'
    static = 'static'
    deprecated = 'deprecated'
    abstract = 'abstract'
    async_ = 'async'
    modification = 'modification'
    documentation = 'documentation'
    defaultLibrary = 'defaultLibrary'

class TokenFormat(Enum):
    Relative = 'relative'

# commented out, because there is already an enumeration with the same name
# TokenFormat = str


class SemanticTokensLegend(TypedDict, total=True):
    tokenTypes: List[str]
    tokenModifiers: List[str]


class SemanticTokensClientCapabilities(TypedDict, total=False):
    class Requests_0(TypedDict, total=False):
        class Range_1(TypedDict, total=True):
            pass
        class Full_1(TypedDict, total=False):
            delta: Optional[bool]
        range: Union[bool, Range_1, None]
        full: Union[bool, Full_1, None]
    dynamicRegistration: Optional[bool]
    requests: Requests_0
    tokenTypes: List[str]
    tokenModifiers: List[str]
    formats: List[TokenFormat]
    overlappingTokenSupport: Optional[bool]
    multilineTokenSupport: Optional[bool]
    serverCancelSupport: Optional[bool]
    augmentsSyntaxTokens: Optional[bool]


class SemanticTokensOptions(WorkDoneProgressOptions, TypedDict, total=False):
    class Range_1(TypedDict, total=True):
        pass
    class Full_1(TypedDict, total=False):
        delta: Optional[bool]
    legend: SemanticTokensLegend
    range: Union[bool, Range_1, None]
    full: Union[bool, Full_1, None]


class SemanticTokensRegistrationOptions(TextDocumentRegistrationOptions, SemanticTokensOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class SemanticTokensParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier


class SemanticTokens(TypedDict, total=False):
    resultId: Optional[str]
    data: List[int]


class SemanticTokensPartialResult(TypedDict, total=True):
    data: List[int]


class SemanticTokensDeltaParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    previousResultId: str


class SemanticTokensDelta(TypedDict, total=False):
    resultId: Optional[str]
    edits: List['SemanticTokensEdit']


class SemanticTokensEdit(TypedDict, total=False):
    start: int
    deleteCount: int
    data: Optional[List[int]]


class SemanticTokensDeltaPartialResult(TypedDict, total=True):
    edits: List[SemanticTokensEdit]


class SemanticTokensRangeParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    range: Range


class SemanticTokensWorkspaceClientCapabilities(TypedDict, total=False):
    refreshSupport: Optional[bool]


class InlayHintClientCapabilities(TypedDict, total=False):
    class ResolveSupport_0(TypedDict, total=True):
        properties: List[str]
    dynamicRegistration: Optional[bool]
    resolveSupport: Optional[ResolveSupport_0]


class InlayHintOptions(WorkDoneProgressOptions, TypedDict, total=False):
    resolveProvider: Optional[bool]


class InlayHintRegistrationOptions(InlayHintOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class InlayHintParams(WorkDoneProgressParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    range: Range


class InlayHint(TypedDict, total=False):
    position: Position
    label: Union[str, List['InlayHintLabelPart']]
    kind: Optional['InlayHintKind']
    textEdits: Optional[List[TextEdit]]
    tooltip: Union[str, MarkupContent, None]
    paddingLeft: Optional[bool]
    paddingRight: Optional[bool]
    data: Optional[LSPAny]


class InlayHintLabelPart(TypedDict, total=False):
    value: str
    tooltip: Union[str, MarkupContent, None]
    location: Optional[Location]
    command: Optional[Command]

class InlayHintKind(IntEnum):
    Type = 1
    Parameter = 2

# commented out, because there is already an enumeration with the same name
# InlayHintKind = int


class InlayHintWorkspaceClientCapabilities(TypedDict, total=False):
    refreshSupport: Optional[bool]


class InlineValueClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class InlineValueOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class InlineValueRegistrationOptions(InlineValueOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class InlineValueParams(WorkDoneProgressParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    range: Range
    context: 'InlineValueContext'


class InlineValueContext(TypedDict, total=True):
    frameId: int
    stoppedLocation: Range


class InlineValueText(TypedDict, total=True):
    range: Range
    text: str


class InlineValueVariableLookup(TypedDict, total=False):
    range: Range
    iableName: Optional[str]
    caseSensitiveLookup: bool


class InlineValueEvaluatableExpression(TypedDict, total=False):
    range: Range
    expression: Optional[str]

InlineValue = Union[InlineValueText, InlineValueVariableLookup, InlineValueEvaluatableExpression]


class InlineValueWorkspaceClientCapabilities(TypedDict, total=False):
    refreshSupport: Optional[bool]


class MonikerClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class MonikerOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class MonikerRegistrationOptions(TextDocumentRegistrationOptions, MonikerOptions, TypedDict, total=True):
    pass


class MonikerParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    pass

class UniquenessLevel(Enum):
    document = 'document'
    project = 'project'
    group = 'group'
    scheme = 'scheme'
    global_ = 'global'

class MonikerKind(Enum):
    import_ = 'import'
    export = 'export'
    local = 'local'


class Moniker(TypedDict, total=False):
    scheme: str
    identifier: str
    unique: UniquenessLevel
    kind: Optional[MonikerKind]


class CompletionClientCapabilities(TypedDict, total=False):
    class CompletionItem_0(TypedDict, total=False):
        class TagSupport_0(TypedDict, total=True):
            valueSet: List['CompletionItemTag']
        class ResolveSupport_0(TypedDict, total=True):
            properties: List[str]
        class InsertTextModeSupport_0(TypedDict, total=True):
            valueSet: List['InsertTextMode']
        snippetSupport: Optional[bool]
        commitCharactersSupport: Optional[bool]
        documentationFormat: Optional[List[MarkupKind]]
        deprecatedSupport: Optional[bool]
        preselectSupport: Optional[bool]
        tagSupport: Optional[TagSupport_0]
        insertReplaceSupport: Optional[bool]
        resolveSupport: Optional[ResolveSupport_0]
        insertTextModeSupport: Optional[InsertTextModeSupport_0]
        labelDetailsSupport: Optional[bool]
    class CompletionItemKind_0(TypedDict, total=False):
        valueSet: Optional[List['CompletionItemKind']]
    class CompletionList_0(TypedDict, total=False):
        itemDefaults: Optional[List[str]]
    dynamicRegistration: Optional[bool]
    completionItem: Optional[CompletionItem_0]
    completionItemKind: Optional[CompletionItemKind_0]
    contextSupport: Optional[bool]
    insertTextMode: Optional['InsertTextMode']
    completionList: Optional[CompletionList_0]


class CompletionOptions(WorkDoneProgressOptions, TypedDict, total=False):
    class CompletionItem_0(TypedDict, total=False):
        labelDetailsSupport: Optional[bool]
    triggerCharacters: Optional[List[str]]
    allCommitCharacters: Optional[List[str]]
    resolveProvider: Optional[bool]
    completionItem: Optional[CompletionItem_0]


class CompletionRegistrationOptions(TextDocumentRegistrationOptions, CompletionOptions, TypedDict, total=True):
    pass


class CompletionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict, total=False):
    context: Optional['CompletionContext']

class CompletionTriggerKind(IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    TriggerForIncompleteCompletions = 3

# commented out, because there is already an enumeration with the same name
# CompletionTriggerKind = int


class CompletionContext(TypedDict, total=False):
    triggerKind: CompletionTriggerKind
    triggerCharacter: Optional[str]


class CompletionList(TypedDict, total=False):
    class ItemDefaults_0(TypedDict, total=False):
        class EditRange_1(TypedDict, total=True):
            insert: Range
            replace: Range
        commitCharacters: Optional[List[str]]
        editRange: Union[Range, EditRange_1, None]
        insertTextFormat: Optional['InsertTextFormat']
        insertTextMode: Optional['InsertTextMode']
        data: Optional[LSPAny]
    isIncomplete: bool
    itemDefaults: Optional[ItemDefaults_0]
    items: List['CompletionItem']

class InsertTextFormat(IntEnum):
    PlainText = 1
    Snippet = 2

# commented out, because there is already an enumeration with the same name
# InsertTextFormat = int

class CompletionItemTag(IntEnum):
    Deprecated = 1

# commented out, because there is already an enumeration with the same name
# CompletionItemTag = int


class InsertReplaceEdit(TypedDict, total=True):
    newText: str
    insert: Range
    replace: Range

class InsertTextMode(IntEnum):
    asIs = 1
    adjustIndentation = 2

# commented out, because there is already an enumeration with the same name
# InsertTextMode = int


class CompletionItemLabelDetails(TypedDict, total=False):
    detail: Optional[str]
    description: Optional[str]


class CompletionItem(TypedDict, total=False):
    label: str
    labelDetails: Optional[CompletionItemLabelDetails]
    kind: Optional['CompletionItemKind']
    tags: Optional[List[CompletionItemTag]]
    detail: Optional[str]
    documentation: Union[str, MarkupContent, None]
    deprecated: Optional[bool]
    preselect: Optional[bool]
    sortText: Optional[str]
    filterText: Optional[str]
    insertText: Optional[str]
    insertTextFormat: Optional[InsertTextFormat]
    insertTextMode: Optional[InsertTextMode]
    textEdit: Union[TextEdit, InsertReplaceEdit, None]
    textEditText: Optional[str]
    additionalTextEdits: Optional[List[TextEdit]]
    commitCharacters: Optional[List[str]]
    command: Optional[Command]
    data: Optional[LSPAny]

class CompletionItemKind(IntEnum):
    Text = 1
    Method = 2
    Function = 3
    Constructor = 4
    Field = 5
    Variable = 6
    Class = 7
    Interface = 8
    Module = 9
    Property = 10
    Unit = 11
    Value = 12
    Enum = 13
    Keyword = 14
    Snippet = 15
    Color = 16
    File = 17
    Reference = 18
    Folder = 19
    EnumMember = 20
    Constant = 21
    Struct = 22
    Event = 23
    Operator = 24
    TypeParameter = 25

# commented out, because there is already an enumeration with the same name
# CompletionItemKind = int


class PublishDiagnosticsClientCapabilities(TypedDict, total=False):
    class TagSupport_0(TypedDict, total=True):
        valueSet: List[DiagnosticTag]
    relatedInformation: Optional[bool]
    tagSupport: Optional[TagSupport_0]
    versionSupport: Optional[bool]
    codeDescriptionSupport: Optional[bool]
    dataSupport: Optional[bool]


class PublishDiagnosticsParams(TypedDict, total=False):
    uri: DocumentUri
    version: Optional[int]
    diagnostics: List[Diagnostic]


class DiagnosticClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    relatedDocumentSupport: Optional[bool]
    markupMessageSupport: Optional[bool]


class DiagnosticOptions(WorkDoneProgressOptions, TypedDict, total=False):
    identifier: Optional[str]
    interFileDependencies: bool
    workspaceDiagnostics: bool


class DiagnosticRegistrationOptions(TextDocumentRegistrationOptions, DiagnosticOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class DocumentDiagnosticParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=False):
    textDocument: TextDocumentIdentifier
    identifier: Optional[str]
    previousResultId: Optional[str]

DocumentDiagnosticReport = Union['RelatedFullDocumentDiagnosticReport', 'RelatedUnchangedDocumentDiagnosticReport']

class DocumentDiagnosticReportKind(Enum):
    Full = 'full'
    Unchanged = 'unchanged'

# commented out, because there is already an enumeration with the same name
# DocumentDiagnosticReportKind = str


class FullDocumentDiagnosticReport(TypedDict, total=False):
    kind: 'DocumentDiagnosticReportKind.Full'
    resultId: Optional[str]
    items: List[Diagnostic]


class UnchangedDocumentDiagnosticReport(TypedDict, total=True):
    kind: 'DocumentDiagnosticReportKind.Unchanged'
    resultId: str


class RelatedFullDocumentDiagnosticReport(FullDocumentDiagnosticReport, TypedDict, total=False):
    relatedDocuments: Optional[Dict[str, Union[FullDocumentDiagnosticReport, UnchangedDocumentDiagnosticReport]]]


class RelatedUnchangedDocumentDiagnosticReport(UnchangedDocumentDiagnosticReport, TypedDict, total=False):
    relatedDocuments: Optional[Dict[str, Union[FullDocumentDiagnosticReport, UnchangedDocumentDiagnosticReport]]]


class DocumentDiagnosticReportPartialResult(TypedDict, total=True):
    relatedDocuments: Dict[str, Union[FullDocumentDiagnosticReport, UnchangedDocumentDiagnosticReport]]


class DiagnosticServerCancellationData(TypedDict, total=True):
    retriggerRequest: bool


class WorkspaceDiagnosticParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=False):
    identifier: Optional[str]
    previousResultIds: List['PreviousResultId']


class PreviousResultId(TypedDict, total=True):
    uri: DocumentUri
    value: str


class WorkspaceDiagnosticReport(TypedDict, total=True):
    items: List['WorkspaceDocumentDiagnosticReport']


class WorkspaceFullDocumentDiagnosticReport(FullDocumentDiagnosticReport, TypedDict, total=True):
    uri: DocumentUri
    version: Union[int, None]


class WorkspaceUnchangedDocumentDiagnosticReport(UnchangedDocumentDiagnosticReport, TypedDict, total=True):
    uri: DocumentUri
    version: Union[int, None]

WorkspaceDocumentDiagnosticReport = Union[WorkspaceFullDocumentDiagnosticReport, WorkspaceUnchangedDocumentDiagnosticReport]


class WorkspaceDiagnosticReportPartialResult(TypedDict, total=True):
    items: List[WorkspaceDocumentDiagnosticReport]


class DiagnosticWorkspaceClientCapabilities(TypedDict, total=False):
    refreshSupport: Optional[bool]


class SignatureHelpClientCapabilities(TypedDict, total=False):
    class SignatureInformation_0(TypedDict, total=False):
        class ParameterInformation_0(TypedDict, total=False):
            labelOffsetSupport: Optional[bool]
        documentationFormat: Optional[List[MarkupKind]]
        parameterInformation: Optional[ParameterInformation_0]
        activeParameterSupport: Optional[bool]
        noActiveParameterSupport: Optional[bool]
    dynamicRegistration: Optional[bool]
    signatureInformation: Optional[SignatureInformation_0]
    contextSupport: Optional[bool]


class SignatureHelpOptions(WorkDoneProgressOptions, TypedDict, total=False):
    triggerCharacters: Optional[List[str]]
    retriggerCharacters: Optional[List[str]]


class SignatureHelpRegistrationOptions(TextDocumentRegistrationOptions, SignatureHelpOptions, TypedDict, total=True):
    pass


class SignatureHelpParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict, total=False):
    context: Optional['SignatureHelpContext']

class SignatureHelpTriggerKind(IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    ContentChange = 3

# commented out, because there is already an enumeration with the same name
# SignatureHelpTriggerKind = int


class SignatureHelpContext(TypedDict, total=False):
    triggerKind: SignatureHelpTriggerKind
    triggerCharacter: Optional[str]
    isRetrigger: bool
    activeSignatureHelp: Optional['SignatureHelp']


class SignatureHelp(TypedDict, total=False):
    signatures: List['SignatureInformation']
    activeSignature: Optional[int]
    activeParameter: Union[int, None]


class SignatureInformation(TypedDict, total=False):
    label: str
    documentation: Union[str, MarkupContent, None]
    parameters: Optional[List['ParameterInformation']]
    activeParameter: Union[int, None]


class ParameterInformation(TypedDict, total=False):
    label: Union[str, Tuple[int, int]]
    documentation: Union[str, MarkupContent, None]


class CodeActionClientCapabilities(TypedDict, total=False):
    class CodeActionLiteralSupport_0(TypedDict, total=True):
        class CodeActionKind_0(TypedDict, total=True):
            valueSet: List['CodeActionKind']
        codeActionKind: CodeActionKind_0
    class ResolveSupport_0(TypedDict, total=True):
        properties: List[str]
    dynamicRegistration: Optional[bool]
    codeActionLiteralSupport: Optional[CodeActionLiteralSupport_0]
    isPreferredSupport: Optional[bool]
    disabledSupport: Optional[bool]
    dataSupport: Optional[bool]
    resolveSupport: Optional[ResolveSupport_0]
    honorsChangeAnnotations: Optional[bool]
    documentationSupport: Optional[bool]


class CodeActionKindDocumentation(TypedDict, total=True):
    kind: 'CodeActionKind'
    command: Command


class CodeActionOptions(WorkDoneProgressOptions, TypedDict, total=False):
    codeActionKinds: Optional[List['CodeActionKind']]
    documentation: Optional[List[CodeActionKindDocumentation]]
    resolveProvider: Optional[bool]


class CodeActionRegistrationOptions(TextDocumentRegistrationOptions, CodeActionOptions, TypedDict, total=True):
    pass


class CodeActionParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    range: Range
    context: 'CodeActionContext'

CodeActionKind = str

class CodeActionKind(Enum):
    Empty = ''
    QuickFix = 'quickfix'
    Refactor = 'refactor'
    RefactorExtract = 'refactor.extract'
    RefactorInline = 'refactor.inline'
    RefactorMove = 'refactor.move'
    RefactorRewrite = 'refactor.rewrite'
    Source = 'source'
    SourceOrganizeImports = 'source.organizeImports'
    SourceFixAll = 'source.fixAll'
    Notebook = 'notebook'


class CodeActionContext(TypedDict, total=False):
    diagnostics: List[Diagnostic]
    only: Optional[List[CodeActionKind]]
    triggerKind: Optional['CodeActionTriggerKind']

class CodeActionTriggerKind(IntEnum):
    Invoked = 1
    Automatic = 2

# commented out, because there is already an enumeration with the same name
# CodeActionTriggerKind = int


class CodeAction(TypedDict, total=False):
    class Disabled_0(TypedDict, total=True):
        reason: str
    title: str
    kind: Optional[CodeActionKind]
    diagnostics: Optional[List[Diagnostic]]
    isPreferred: Optional[bool]
    disabled: Optional[Disabled_0]
    edit: Optional[WorkspaceEdit]
    command: Optional[Command]
    data: Optional[LSPAny]


class DocumentColorClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class DocumentColorOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class DocumentColorRegistrationOptions(TextDocumentRegistrationOptions, StaticRegistrationOptions, DocumentColorOptions, TypedDict, total=True):
    pass


class DocumentColorParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier


class ColorInformation(TypedDict, total=True):
    range: Range
    color: 'Color'


class Color(TypedDict, total=True):
    red: float
    green: float
    blue: float
    alpha: float


class ColorPresentationParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    color: Color
    range: Range


class ColorPresentation(TypedDict, total=False):
    label: str
    textEdit: Optional[TextEdit]
    additionalTextEdits: Optional[List[TextEdit]]


class DocumentFormattingClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class DocumentFormattingOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class DocumentFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentFormattingOptions, TypedDict, total=True):
    pass


class DocumentFormattingParams(WorkDoneProgressParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    options: 'FormattingOptions'


class FormattingOptions(TypedDict, total=False):
    tabSize: int
    insertSpaces: bool
    trimTrailingWhitespace: Optional[bool]
    insertFinalNewline: Optional[bool]
    trimFinalNewlines: Optional[bool]


class DocumentRangeFormattingClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    rangesSupport: Optional[bool]


class DocumentRangeFormattingOptions(WorkDoneProgressOptions, TypedDict, total=False):
    rangesSupport: Optional[bool]


class DocumentRangeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentRangeFormattingOptions, TypedDict, total=True):
    pass


class DocumentRangeFormattingParams(WorkDoneProgressParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    range: Range
    options: FormattingOptions


class DocumentRangesFormattingParams(WorkDoneProgressParams, TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    ranges: List[Range]
    options: FormattingOptions


class DocumentOnTypeFormattingClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class DocumentOnTypeFormattingOptions(TypedDict, total=False):
    firstTriggerCharacter: str
    moreTriggerCharacter: Optional[List[str]]


class DocumentOnTypeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentOnTypeFormattingOptions, TypedDict, total=True):
    pass


class DocumentOnTypeFormattingParams(TypedDict, total=True):
    textDocument: TextDocumentIdentifier
    position: Position
    ch: str
    options: FormattingOptions

class PrepareSupportDefaultBehavior(IntEnum):
    Identifier = 1

# commented out, because there is already an enumeration with the same name
# PrepareSupportDefaultBehavior = int


class RenameClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    prepareSupport: Optional[bool]
    prepareSupportDefaultBehavior: Optional[PrepareSupportDefaultBehavior]
    honorsChangeAnnotations: Optional[bool]


class RenameOptions(WorkDoneProgressOptions, TypedDict, total=False):
    prepareProvider: Optional[bool]


class RenameRegistrationOptions(TextDocumentRegistrationOptions, RenameOptions, TypedDict, total=True):
    pass


class RenameParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict, total=True):
    newName: str


class PrepareRenameParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict, total=True):
    pass


class LinkedEditingRangeClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class LinkedEditingRangeOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class LinkedEditingRangeRegistrationOptions(TextDocumentRegistrationOptions, LinkedEditingRangeOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class LinkedEditingRangeParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict, total=True):
    pass


class LinkedEditingRanges(TypedDict, total=False):
    ranges: List[Range]
    wordPattern: Optional[str]


class InlineCompletionClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class InlineCompletionOptions(WorkDoneProgressOptions, TypedDict, total=True):
    pass


class InlineCompletionRegistrationOptions(InlineCompletionOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TypedDict, total=True):
    pass


class InlineCompletionParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict, total=True):
    context: 'InlineCompletionContext'


class InlineCompletionContext(TypedDict, total=False):
    triggerKind: 'InlineCompletionTriggerKind'
    selectedCompletionInfo: Optional['SelectedCompletionInfo']

class InlineCompletionTriggerKind(IntEnum):
    Invoked = 1
    Automatic = 2

# commented out, because there is already an enumeration with the same name
# InlineCompletionTriggerKind = int


class SelectedCompletionInfo(TypedDict, total=True):
    range: Range
    text: str


class InlineCompletionList(TypedDict, total=True):
    items: List['InlineCompletionItem']


class InlineCompletionItem(TypedDict, total=False):
    insertText: Union[str, StringValue]
    filterText: Optional[str]
    range: Optional[Range]
    command: Optional[Command]


class WorkspaceSymbolClientCapabilities(TypedDict, total=False):
    class SymbolKind_0(TypedDict, total=False):
        valueSet: Optional[List[SymbolKind]]
    class TagSupport_0(TypedDict, total=True):
        valueSet: List[SymbolTag]
    class ResolveSupport_0(TypedDict, total=True):
        properties: List[str]
    dynamicRegistration: Optional[bool]
    symbolKind: Optional[SymbolKind_0]
    tagSupport: Optional[TagSupport_0]
    resolveSupport: Optional[ResolveSupport_0]


class WorkspaceSymbolOptions(WorkDoneProgressOptions, TypedDict, total=False):
    resolveProvider: Optional[bool]


class WorkspaceSymbolRegistrationOptions(WorkspaceSymbolOptions, TypedDict, total=True):
    pass


class WorkspaceSymbolParams(WorkDoneProgressParams, PartialResultParams, TypedDict, total=True):
    query: str


class WorkspaceSymbol(TypedDict, total=False):
    class Location_1(TypedDict, total=True):
        uri: DocumentUri
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    containerName: Optional[str]
    location: Union[Location, Location_1]
    data: Optional[LSPAny]


class ConfigurationParams(TypedDict, total=True):
    items: List['ConfigurationItem']


class ConfigurationItem(TypedDict, total=False):
    scopeUri: Optional[URI]
    section: Optional[str]


class DidChangeConfigurationClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class DidChangeConfigurationParams(TypedDict, total=True):
    settings: LSPAny


class WorkspaceFoldersServerCapabilities(TypedDict, total=False):
    supported: Optional[bool]
    changeNotifications: Union[str, bool, None]


class WorkspaceFolder(TypedDict, total=True):
    uri: URI
    name: str


class DidChangeWorkspaceFoldersParams(TypedDict, total=True):
    event: 'WorkspaceFoldersChangeEvent'


class WorkspaceFoldersChangeEvent(TypedDict, total=True):
    added: List[WorkspaceFolder]
    removed: List[WorkspaceFolder]


class FileOperationRegistrationOptions(TypedDict, total=True):
    filters: List['FileOperationFilter']

class FileOperationPatternKind(Enum):
    file = 'file'
    folder = 'folder'

# commented out, because there is already an enumeration with the same name
# FileOperationPatternKind = str


class FileOperationPatternOptions(TypedDict, total=False):
    ignoreCase: Optional[bool]


class FileOperationPattern(TypedDict, total=False):
    glob: str
    matches: Optional[FileOperationPatternKind]
    options: Optional[FileOperationPatternOptions]


class FileOperationFilter(TypedDict, total=False):
    scheme: Optional[str]
    pattern: FileOperationPattern


class CreateFilesParams(TypedDict, total=True):
    files: List['FileCreate']


class FileCreate(TypedDict, total=True):
    uri: str


class RenameFilesParams(TypedDict, total=True):
    files: List['FileRename']


class FileRename(TypedDict, total=True):
    oldUri: str
    newUri: str


class DeleteFilesParams(TypedDict, total=True):
    files: List['FileDelete']


class FileDelete(TypedDict, total=True):
    uri: str


class DidChangeWatchedFilesClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]
    relativePatternSupport: Optional[bool]


class DidChangeWatchedFilesRegistrationOptions(TypedDict, total=True):
    watchers: List['FileSystemWatcher']

Pattern = str


class RelativePattern(TypedDict, total=True):
    baseUri: Union[WorkspaceFolder, URI]
    pattern: Pattern

GlobPattern = Union[Pattern, RelativePattern]


class FileSystemWatcher(TypedDict, total=False):
    globPattern: GlobPattern
    kind: Optional['WatchKind']

class WatchKind(IntEnum):
    Create = 1
    Change = 2
    Delete = 4

# commented out, because there is already an enumeration with the same name
# WatchKind = int


class DidChangeWatchedFilesParams(TypedDict, total=True):
    changes: List['FileEvent']


class FileEvent(TypedDict, total=True):
    uri: DocumentUri
    type: 'FileChangeType'

class FileChangeType(IntEnum):
    Created = 1
    Changed = 2
    Deleted = 3

# commented out, because there is already an enumeration with the same name
# FileChangeType = int


class ExecuteCommandClientCapabilities(TypedDict, total=False):
    dynamicRegistration: Optional[bool]


class ExecuteCommandOptions(WorkDoneProgressOptions, TypedDict, total=True):
    commands: List[str]


class ExecuteCommandRegistrationOptions(ExecuteCommandOptions, TypedDict, total=True):
    pass


class ExecuteCommandParams(WorkDoneProgressParams, TypedDict, total=False):
    command: str
    arguments: Optional[List[LSPAny]]


class ApplyWorkspaceEditParams(TypedDict, total=False):
    label: Optional[str]
    edit: WorkspaceEdit
    metadata: Optional['WorkspaceEditMetadata']


class WorkspaceEditMetadata(TypedDict, total=False):
    isRefactoring: Optional[bool]


class ApplyWorkspaceEditResult(TypedDict, total=False):
    applied: bool
    failureReason: Optional[str]
    failedChange: Optional[int]


class ShowMessageParams(TypedDict, total=True):
    type: 'MessageType'
    message: str

class MessageType(IntEnum):
    Error = 1
    Warning = 2
    Info = 3
    Log = 4
    Debug = 5

# commented out, because there is already an enumeration with the same name
# MessageType = int


class ShowMessageRequestClientCapabilities(TypedDict, total=False):
    class MessageActionItem_0(TypedDict, total=False):
        additionalPropertiesSupport: Optional[bool]
    messageActionItem: Optional[MessageActionItem_0]


class ShowMessageRequestParams(TypedDict, total=False):
    type: MessageType
    message: str
    actions: Optional[List['MessageActionItem']]


class MessageActionItem(TypedDict, total=True):
    title: str


class ShowDocumentClientCapabilities(TypedDict, total=True):
    support: bool


class ShowDocumentParams(TypedDict, total=False):
    uri: URI
    external: Optional[bool]
    takeFocus: Optional[bool]
    selection: Optional[Range]


class ShowDocumentResult(TypedDict, total=True):
    success: bool


class LogMessageParams(TypedDict, total=True):
    type: MessageType
    message: str


class WorkDoneProgressCreateParams(TypedDict, total=True):
    token: ProgressToken


class WorkDoneProgressCancelParams(TypedDict, total=True):
    token: ProgressToken



##### END OF LSP SPECS


#######################################################################
#
# Language-Server-Protocol methods
#
#######################################################################

class LSPTasks:
    def __init__(self, lsp_data: dict):
        self.lsp_data = lsp_data
        self.lsp_table = gen_lsp_table([], prefix='lsp_')

NO_TASKS = LSPTasks({})

class LSPBase:
    def __init__(self, cpu_bound: LSPTasks=NO_TASKS, blocking: LSPTasks=NO_TASKS):
        self.lsp_data = {
            'processId': 0,
            'rootUri': '',
            'clientCapabilities': {},
            'serverInfo': {"name": self.__class__.__name__, "version": "0.1"},
            'serverCapabilities': {
            }
        }
        self.connection = None
        self.cpu_bound = cpu_bound
        self.blocking = blocking
        self.lsp_table = gen_lsp_table(self, prefix='lsp_')
        self.lsp_fulltable = self.lsp_table.copy()
        assert self.lsp_fulltable.keys().isdisjoint(self.cpu_bound.lsp_table.keys())
        self.lsp_fulltable.update(self.cpu_bound.lsp_table)
        assert self.lsp_fulltable.keys().isdisjoint(self.blocking.lsp_table.keys())
        self.lsp_fulltable.update(self.blocking.lsp_table)

    def connect(self, connection):
        self.connection = connection

    def lsp_initialize(self, **kwargs) -> Dict:
        # InitializeParams -> InitializeResult
        self.lsp_data['processId'] = kwargs['processId']
        self.lsp_data['rootUri'] = kwargs['rootUri']
        self.lsp_data['clientCapabilities'] = kwargs['capabilities']
        return {'capabilities': self.lsp_data['serverCapabilities'],
                'serverInfo': self.lsp_data['serverInfo']}

    def lsp_initialized(self, params: InitializedParams) -> None:
        pass

    def lsp_shutdown(self) -> Dict:
        self.lsp_data['processId'] = 0
        self.lsp_data['rootUri'] = ''
        self.lsp_data['clientCapabilities'] = dict()
        return {}


if __name__ == "__main__":
    print("A small self-test of DHParser.lsp")
    print(DocumentSymbol.__required_keys__)
