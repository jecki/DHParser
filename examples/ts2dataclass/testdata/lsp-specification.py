
from collections import ChainMap
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Union, List, Tuple, Optional, Dict, Any, Generic, TypeVar, TypedDict


integer = float


uinteger = float


decimal = float


class Message(TypedDict):
    jsonrpc: str


class RequestMessage(Message, TypedDict):
    id: Union[int, str]
    method: str
    params: Union[List, object, None]


class ResponseMessage(Message, TypedDict):
    id: Union[int, str, None]
    result: Union[str, float, bool, object, None]
    error: Optional['ResponseError']


class ResponseError(TypedDict):
    code: int
    message: str
    data: Union[str, float, bool, List, object, None]


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
    ContentModified = -32801
    RequestCancelled = -32800
    lspReservedErrorRangeEnd = -32800


class NotificationMessage(Message, TypedDict):
    method: str
    params: Union[List, object, None]


class CancelParams(TypedDict):
    id: Union[int, str]


ProgressToken = Union[int, str]


T = TypeVar('T')


class ProgressParams(Generic[T]):
    token: ProgressToken
    value: 'T'


DocumentUri = str


URI = str


class RegularExpressionsClientCapabilities(TypedDict):
    engine: str
    version: Optional[str]


EOL: List[str] = ['\n', '\r\n', '\r']


class Position(TypedDict):
    line: int
    character: int


class Range(TypedDict):
    start: Position
    end: Position


class Location(TypedDict):
    uri: DocumentUri
    range: Range


class LocationLink(TypedDict):
    originSelectionRange: Optional[Range]
    targetUri: DocumentUri
    targetRange: Range
    targetSelectionRange: Range


class Diagnostic(TypedDict):
    range: Range
    severity: Optional['DiagnosticSeverity']
    code: Union[int, str, None]
    codeDescription: Optional['CodeDescription']
    source: Optional[str]
    message: str
    tags: Optional[List['DiagnosticTag']]
    relatedInformation: Optional[List['DiagnosticRelatedInformation']]
    data: Optional[Any]


class DiagnosticSeverity(IntEnum):
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4


class DiagnosticTag(IntEnum):
    Unnecessary = 1
    Deprecated = 2


class DiagnosticRelatedInformation(TypedDict):
    location: Location
    message: str


class CodeDescription(TypedDict):
    href: URI


class Command(TypedDict):
    title: str
    command: str
    arguments: Optional[List[Any]]


class TextEdit(TypedDict):
    range: Range
    newText: str


class ChangeAnnotation(TypedDict):
    label: str
    needsConfirmation: Optional[bool]
    description: Optional[str]


ChangeAnnotationIdentifier = str


class AnnotatedTextEdit(TextEdit, TypedDict):
    annotationId: ChangeAnnotationIdentifier


class TextDocumentEdit(TypedDict):
    textDocument: 'OptionalVersionedTextDocumentIdentifier'
    edits: List[Union[TextEdit, AnnotatedTextEdit]]


class CreateFileOptions(TypedDict):
    overwrite: Optional[bool]
    ignoreIfExists: Optional[bool]


class CreateFile(TypedDict):
    kind: str
    uri: DocumentUri
    options: Optional[CreateFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class RenameFileOptions(TypedDict):
    overwrite: Optional[bool]
    ignoreIfExists: Optional[bool]


class RenameFile(TypedDict):
    kind: str
    oldUri: DocumentUri
    newUri: DocumentUri
    options: Optional[RenameFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class DeleteFileOptions(TypedDict):
    recursive: Optional[bool]
    ignoreIfNotExists: Optional[bool]


class DeleteFile(TypedDict):
    kind: str
    uri: DocumentUri
    options: Optional[DeleteFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class WorkspaceEdit(TypedDict):
    changes: Optional[Dict[DocumentUri, List[TextEdit]]]
    documentChanges: Union[List[TextDocumentEdit], List[Union[TextDocumentEdit, CreateFile, RenameFile, DeleteFile]], None]
    changeAnnotations: Optional[Dict[str, ChangeAnnotation]]


class WorkspaceEditClientCapabilities(TypedDict):
    class ChangeAnnotationSupport_(TypedDict):
        groupsOnLabel: Optional[bool]
    documentChanges: Optional[bool]
    resourceOperations: Optional[List['ResourceOperationKind']]
    failureHandling: Optional['FailureHandlingKind']
    normalizesLineEndings: Optional[bool]
    changeAnnotationSupport: Optional[ChangeAnnotationSupport_]


class ResourceOperationKind(Enum):
    Create = 'create'
    Rename = 'rename'
    Delete = 'delete'


class FailureHandlingKind(Enum):
    Abort = 'abort'
    Transactional = 'transactional'
    TextOnlyTransactional = 'textOnlyTransactional'
    Undo = 'undo'


class TextDocumentIdentifier(TypedDict):
    uri: DocumentUri


class TextDocumentItem(TypedDict):
    uri: DocumentUri
    languageId: str
    version: int
    text: str


class VersionedTextDocumentIdentifier(TextDocumentIdentifier, TypedDict):
    version: int


class OptionalVersionedTextDocumentIdentifier(TextDocumentIdentifier, TypedDict):
    version: Union[int, None]


class TextDocumentPositionParams(TypedDict):
    textDocument: TextDocumentIdentifier
    position: Position


class DocumentFilter(TypedDict):
    language: Optional[str]
    scheme: Optional[str]
    pattern: Optional[str]


DocumentSelector = List[DocumentFilter]


class StaticRegistrationOptions(TypedDict):
    id: Optional[str]


class TextDocumentRegistrationOptions(TypedDict):
    documentSelector: Union[DocumentSelector, None]


class MarkupKind(Enum):
    PlainText = 'plaintext'
    Markdown = 'markdown'


class MarkupContent(TypedDict):
    kind: MarkupKind
    value: str


class MarkdownClientCapabilities(TypedDict):
    parser: str
    version: Optional[str]


class WorkDoneProgressBegin(TypedDict):
    kind: str
    title: str
    cancellable: Optional[bool]
    message: Optional[str]
    percentage: Optional[int]


class WorkDoneProgressReport(TypedDict):
    kind: str
    cancellable: Optional[bool]
    message: Optional[str]
    percentage: Optional[int]


class WorkDoneProgressEnd(TypedDict):
    kind: str
    message: Optional[str]


class WorkDoneProgressParams(TypedDict):
    workDoneToken: Optional[ProgressToken]


class WorkDoneProgressOptions(TypedDict):
    workDoneProgress: Optional[bool]


class PartialResultParams(TypedDict):
    partialResultToken: Optional[ProgressToken]


TraceValue = str


class InitializeParams(WorkDoneProgressParams, TypedDict):
    class ClientInfo_(TypedDict):
        name: str
        version: Optional[str]
    processId: Union[int, None]
    clientInfo: Optional[ClientInfo_]
    locale: Optional[str]
    rootPath: Union[str, None]
    rootUri: Union[DocumentUri, None]
    initializationOptions: Optional[Any]
    capabilities: 'ClientCapabilities'
    trace: Optional[TraceValue]
    workspaceFolders: Union[List['WorkspaceFolder'], None]


class TextDocumentClientCapabilities(TypedDict):
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


class ClientCapabilities(TypedDict):
    class Workspace_(TypedDict):
        class FileOperations_(TypedDict):
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
        fileOperations: Optional[FileOperations_]
    class Window_(TypedDict):
        workDoneProgress: Optional[bool]
        showMessage: Optional['ShowMessageRequestClientCapabilities']
        showDocument: Optional['ShowDocumentClientCapabilities']
    class General_(TypedDict):
        regularExpressions: Optional[RegularExpressionsClientCapabilities]
        markdown: Optional[MarkdownClientCapabilities]
    workspace: Optional[Workspace_]
    textDocument: Optional[TextDocumentClientCapabilities]
    window: Optional[Window_]
    general: Optional[General_]
    experimental: Optional[Any]


class InitializeResult(TypedDict):
    class ServerInfo_(TypedDict):
        name: str
        version: Optional[str]
    capabilities: 'ServerCapabilities'
    serverInfo: Optional[ServerInfo_]


class InitializeError(IntEnum):
    unknownProtocolVersion = 1


class InitializeError(TypedDict):
    retry: bool


class ServerCapabilities(TypedDict):
    class Workspace_(TypedDict):
        class FileOperations_(TypedDict):
            didCreate: Optional['FileOperationRegistrationOptions']
            willCreate: Optional['FileOperationRegistrationOptions']
            didRename: Optional['FileOperationRegistrationOptions']
            willRename: Optional['FileOperationRegistrationOptions']
            didDelete: Optional['FileOperationRegistrationOptions']
            willDelete: Optional['FileOperationRegistrationOptions']
        workspaceFolders: Optional['WorkspaceFoldersServerCapabilities']
        fileOperations: Optional[FileOperations_]
    textDocumentSync: Union['TextDocumentSyncOptions', 'TextDocumentSyncKind', None]
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
    workspaceSymbolProvider: Union[bool, 'WorkspaceSymbolOptions', None]
    workspace: Optional[Workspace_]
    experimental: Optional[Any]


class InitializedParams(TypedDict):
    pass


class LogTraceParams(TypedDict):
    message: str
    verbose: Optional[str]


class SetTraceParams(TypedDict):
    value: TraceValue


class ShowMessageParams(TypedDict):
    type: 'MessageType'
    message: str


class MessageType(IntEnum):
    Error = 1
    Warning = 2
    Info = 3
    Log = 4


class ShowMessageRequestClientCapabilities(TypedDict):
    class MessageActionItem_(TypedDict):
        additionalPropertiesSupport: Optional[bool]
    messageActionItem: Optional[MessageActionItem_]


class ShowMessageRequestParams(TypedDict):
    type: MessageType
    message: str
    actions: Optional[List['MessageActionItem']]


class MessageActionItem(TypedDict):
    title: str


class ShowDocumentClientCapabilities(TypedDict):
    support: bool


class ShowDocumentParams(TypedDict):
    uri: URI
    external: Optional[bool]
    takeFocus: Optional[bool]
    selection: Optional[Range]


class ShowDocumentResult(TypedDict):
    success: bool


class LogMessageParams(TypedDict):
    type: MessageType
    message: str


class WorkDoneProgressCreateParams(TypedDict):
    token: ProgressToken


class WorkDoneProgressCancelParams(TypedDict):
    token: ProgressToken


class Registration(TypedDict):
    id: str
    method: str
    registerOptions: Optional[Any]


class RegistrationParams(TypedDict):
    registrations: List[Registration]


class Unregistration(TypedDict):
    id: str
    method: str


class UnregistrationParams(TypedDict):
    unregisterations: List[Unregistration]


class WorkspaceFoldersServerCapabilities(TypedDict):
    supported: Optional[bool]
    changeNotifications: Union[str, bool, None]


class WorkspaceFolder(TypedDict):
    uri: DocumentUri
    name: str


class DidChangeWorkspaceFoldersParams(TypedDict):
    event: 'WorkspaceFoldersChangeEvent'


class WorkspaceFoldersChangeEvent(TypedDict):
    added: List[WorkspaceFolder]
    removed: List[WorkspaceFolder]


class DidChangeConfigurationClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class DidChangeConfigurationParams(TypedDict):
    settings: Any


class ConfigurationParams(TypedDict):
    items: List['ConfigurationItem']


class ConfigurationItem(TypedDict):
    scopeUri: Optional[DocumentUri]
    section: Optional[str]


class DidChangeWatchedFilesClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class DidChangeWatchedFilesRegistrationOptions(TypedDict):
    watchers: List['FileSystemWatcher']


class FileSystemWatcher(TypedDict):
    globPattern: str
    kind: Optional[int]


class WatchKind(IntEnum):
    Create = 1
    Change = 2
    Delete = 4


class DidChangeWatchedFilesParams(TypedDict):
    changes: List['FileEvent']


class FileEvent(TypedDict):
    uri: DocumentUri
    type: int


class FileChangeType(IntEnum):
    Created = 1
    Changed = 2
    Deleted = 3


class WorkspaceSymbolClientCapabilities(TypedDict):
    class SymbolKind_(TypedDict):
        valueSet: Optional[List['SymbolKind']]
    class TagSupport_(TypedDict):
        valueSet: List['SymbolTag']
    dynamicRegistration: Optional[bool]
    symbolKind: Optional[SymbolKind_]
    tagSupport: Optional[TagSupport_]


class WorkspaceSymbolOptions(WorkDoneProgressOptions, TypedDict):
    pass


class WorkspaceSymbolRegistrationOptions(WorkspaceSymbolOptions, TypedDict):
    pass


class WorkspaceSymbolParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    query: str


class ExecuteCommandClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class ExecuteCommandOptions(WorkDoneProgressOptions, TypedDict):
    commands: List[str]


class ExecuteCommandRegistrationOptions(ExecuteCommandOptions, TypedDict):
    pass


class ExecuteCommandParams(WorkDoneProgressParams, TypedDict):
    command: str
    arguments: Optional[List[Any]]


class ApplyWorkspaceEditParams(TypedDict):
    label: Optional[str]
    edit: WorkspaceEdit


class ApplyWorkspaceEditResponse(TypedDict):
    applied: bool
    failureReason: Optional[str]
    failedChange: Optional[int]


class FileOperationRegistrationOptions(TypedDict):
    filters: List['FileOperationFilter']


class FileOperationPatternKind(Enum):
    file = 'file'
    folder = 'folder'


class FileOperationPatternOptions(TypedDict):
    ignoreCase: Optional[bool]


class FileOperationPattern(TypedDict):
    glob: str
    matches: Optional[FileOperationPatternKind]
    options: Optional[FileOperationPatternOptions]


class FileOperationFilter(TypedDict):
    scheme: Optional[str]
    pattern: FileOperationPattern


class CreateFilesParams(TypedDict):
    files: List['FileCreate']


class FileCreate(TypedDict):
    uri: str


class RenameFilesParams(TypedDict):
    files: List['FileRename']


class FileRename(TypedDict):
    oldUri: str
    newUri: str


class DeleteFilesParams(TypedDict):
    files: List['FileDelete']


class FileDelete(TypedDict):
    uri: str


class TextDocumentSyncKind(IntEnum):
    None_ = 0
    Full = 1
    Incremental = 2


class TextDocumentSyncOptions(TypedDict):
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]


class DidOpenTextDocumentParams(TypedDict):
    textDocument: TextDocumentItem


class TextDocumentChangeRegistrationOptions(TextDocumentRegistrationOptions, TypedDict):
    syncKind: TextDocumentSyncKind


class DidChangeTextDocumentParams(TypedDict):
    textDocument: VersionedTextDocumentIdentifier
    contentChanges: List['TextDocumentContentChangeEvent']


class TextDocumentContentChangeEvent_0(TypedDict):
    range: Range
    rangeLength: Optional[int]
    text: str
class TextDocumentContentChangeEvent_1(TypedDict):
    text: str
TextDocumentContentChangeEvent = Union[TextDocumentContentChangeEvent_0, TextDocumentContentChangeEvent_1]


class WillSaveTextDocumentParams(TypedDict):
    textDocument: TextDocumentIdentifier
    reason: 'TextDocumentSaveReason'


class TextDocumentSaveReason(IntEnum):
    Manual = 1
    AfterDelay = 2
    FocusOut = 3


class SaveOptions(TypedDict):
    includeText: Optional[bool]


class TextDocumentSaveRegistrationOptions(TextDocumentRegistrationOptions, TypedDict):
    includeText: Optional[bool]


class DidSaveTextDocumentParams(TypedDict):
    textDocument: TextDocumentIdentifier
    text: Optional[str]


class DidCloseTextDocumentParams(TypedDict):
    textDocument: TextDocumentIdentifier


class TextDocumentSyncClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    didSave: Optional[bool]


class TextDocumentSyncOptions(TypedDict):
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    save: Union[bool, SaveOptions, None]


class PublishDiagnosticsClientCapabilities(TypedDict):
    class TagSupport_(TypedDict):
        valueSet: List[DiagnosticTag]
    relatedInformation: Optional[bool]
    tagSupport: Optional[TagSupport_]
    versionSupport: Optional[bool]
    codeDescriptionSupport: Optional[bool]
    dataSupport: Optional[bool]


class PublishDiagnosticsParams(TypedDict):
    uri: DocumentUri
    version: Optional[int]
    diagnostics: List[Diagnostic]


class CompletionClientCapabilities(TypedDict):
    class CompletionItem_(TypedDict):
        class TagSupport_(TypedDict):
            valueSet: List['CompletionItemTag']
        class ResolveSupport_(TypedDict):
            properties: List[str]
        class InsertTextModeSupport_(TypedDict):
            valueSet: List['InsertTextMode']
        snippetSupport: Optional[bool]
        commitCharactersSupport: Optional[bool]
        documentationFormat: Optional[List[MarkupKind]]
        deprecatedSupport: Optional[bool]
        preselectSupport: Optional[bool]
        tagSupport: Optional[TagSupport_]
        insertReplaceSupport: Optional[bool]
        resolveSupport: Optional[ResolveSupport_]
        insertTextModeSupport: Optional[InsertTextModeSupport_]
    class CompletionItemKind_(TypedDict):
        valueSet: Optional[List['CompletionItemKind']]
    dynamicRegistration: Optional[bool]
    completionItem: Optional[CompletionItem_]
    completionItemKind: Optional[CompletionItemKind_]
    contextSupport: Optional[bool]


class CompletionOptions(WorkDoneProgressOptions, TypedDict):
    triggerCharacters: Optional[List[str]]
    allCommitCharacters: Optional[List[str]]
    resolveProvider: Optional[bool]


class CompletionRegistrationOptions(TextDocumentRegistrationOptions, CompletionOptions, TypedDict):
    pass


class CompletionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict):
    context: Optional['CompletionContext']


class CompletionTriggerKind(IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    TriggerForIncompleteCompletions = 3


class CompletionContext(TypedDict):
    triggerKind: CompletionTriggerKind
    triggerCharacter: Optional[str]


class CompletionList(TypedDict):
    isIncomplete: bool
    items: List['CompletionItem']


class InsertTextFormat(IntEnum):
    PlainText = 1
    Snippet = 2


class CompletionItemTag(IntEnum):
    Deprecated = 1


class InsertReplaceEdit(TypedDict):
    newText: str
    insert: Range
    replace: Range


class InsertTextMode(IntEnum):
    asIs = 1
    adjustIndentation = 2


class CompletionItem(TypedDict):
    label: str
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
    additionalTextEdits: Optional[List[TextEdit]]
    commitCharacters: Optional[List[str]]
    command: Optional[Command]
    data: Optional[Any]


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


class HoverClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    contentFormat: Optional[List[MarkupKind]]


class HoverOptions(WorkDoneProgressOptions, TypedDict):
    pass


class HoverRegistrationOptions(TextDocumentRegistrationOptions, HoverOptions, TypedDict):
    pass


class HoverParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict):
    pass


class Hover(TypedDict):
    contents: Union['MarkedString', List['MarkedString'], MarkupContent]
    range: Optional[Range]


class MarkedString_1(TypedDict):
    language: str
    value: str
MarkedString = Union[str, MarkedString_1]


class SignatureHelpClientCapabilities(TypedDict):
    class SignatureInformation_(TypedDict):
        class ParameterInformation_(TypedDict):
            labelOffsetSupport: Optional[bool]
        documentationFormat: Optional[List[MarkupKind]]
        parameterInformation: Optional[ParameterInformation_]
        activeParameterSupport: Optional[bool]
    dynamicRegistration: Optional[bool]
    signatureInformation: Optional[SignatureInformation_]
    contextSupport: Optional[bool]


class SignatureHelpOptions(WorkDoneProgressOptions, TypedDict):
    triggerCharacters: Optional[List[str]]
    retriggerCharacters: Optional[List[str]]


class SignatureHelpRegistrationOptions(TextDocumentRegistrationOptions, SignatureHelpOptions, TypedDict):
    pass


class SignatureHelpParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict):
    context: Optional['SignatureHelpContext']


class SignatureHelpTriggerKind(IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    ContentChange = 3


class SignatureHelpContext(TypedDict):
    triggerKind: SignatureHelpTriggerKind
    triggerCharacter: Optional[str]
    isRetrigger: bool
    activeSignatureHelp: Optional['SignatureHelp']


class SignatureHelp(TypedDict):
    signatures: List['SignatureInformation']
    activeSignature: Optional[int]
    activeParameter: Optional[int]


class SignatureInformation(TypedDict):
    label: str
    documentation: Union[str, MarkupContent, None]
    parameters: Optional[List['ParameterInformation']]
    activeParameter: Optional[int]


class ParameterInformation(TypedDict):
    label: Union[str, Tuple[int, int]]
    documentation: Union[str, MarkupContent, None]


class DeclarationClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class DeclarationOptions(WorkDoneProgressOptions, TypedDict):
    pass


class DeclarationRegistrationOptions(DeclarationOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TypedDict):
    pass


class DeclarationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict):
    pass


class DefinitionClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class DefinitionOptions(WorkDoneProgressOptions, TypedDict):
    pass


class DefinitionRegistrationOptions(TextDocumentRegistrationOptions, DefinitionOptions, TypedDict):
    pass


class DefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict):
    pass


class TypeDefinitionClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class TypeDefinitionOptions(WorkDoneProgressOptions, TypedDict):
    pass


class TypeDefinitionRegistrationOptions(TextDocumentRegistrationOptions, TypeDefinitionOptions, StaticRegistrationOptions, TypedDict):
    pass


class TypeDefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict):
    pass


class ImplementationClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class ImplementationOptions(WorkDoneProgressOptions, TypedDict):
    pass


class ImplementationRegistrationOptions(TextDocumentRegistrationOptions, ImplementationOptions, StaticRegistrationOptions, TypedDict):
    pass


class ImplementationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict):
    pass


class ReferenceClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class ReferenceOptions(WorkDoneProgressOptions, TypedDict):
    pass


class ReferenceRegistrationOptions(TextDocumentRegistrationOptions, ReferenceOptions, TypedDict):
    pass


class ReferenceParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict):
    context: 'ReferenceContext'


class ReferenceContext(TypedDict):
    includeDeclaration: bool


class DocumentHighlightClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class DocumentHighlightOptions(WorkDoneProgressOptions, TypedDict):
    pass


class DocumentHighlightRegistrationOptions(TextDocumentRegistrationOptions, DocumentHighlightOptions, TypedDict):
    pass


class DocumentHighlightParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict):
    pass


class DocumentHighlight(TypedDict):
    range: Range
    kind: Optional['DocumentHighlightKind']


class DocumentHighlightKind(IntEnum):
    Text = 1
    Read = 2
    Write = 3


class DocumentSymbolClientCapabilities(TypedDict):
    class SymbolKind_(TypedDict):
        valueSet: Optional[List['SymbolKind']]
    class TagSupport_(TypedDict):
        valueSet: List['SymbolTag']
    dynamicRegistration: Optional[bool]
    symbolKind: Optional[SymbolKind_]
    hierarchicalDocumentSymbolSupport: Optional[bool]
    tagSupport: Optional[TagSupport_]
    labelSupport: Optional[bool]


class DocumentSymbolOptions(WorkDoneProgressOptions, TypedDict):
    label: Optional[str]


class DocumentSymbolRegistrationOptions(TextDocumentRegistrationOptions, DocumentSymbolOptions, TypedDict):
    pass


class DocumentSymbolParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
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


class SymbolTag(IntEnum):
    Deprecated = 1


class DocumentSymbol(TypedDict):
    name: str
    detail: Optional[str]
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    deprecated: Optional[bool]
    range: Range
    selectionRange: Range
    children: Optional[List['DocumentSymbol']]


class SymbolInformation(TypedDict):
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    deprecated: Optional[bool]
    location: Location
    containerName: Optional[str]


class CodeActionClientCapabilities(TypedDict):
    class CodeActionLiteralSupport_(TypedDict):
        class CodeActionKind_(TypedDict):
            valueSet: List['CodeActionKind']
        codeActionKind: CodeActionKind_
    class ResolveSupport_(TypedDict):
        properties: List[str]
    dynamicRegistration: Optional[bool]
    codeActionLiteralSupport: Optional[CodeActionLiteralSupport_]
    isPreferredSupport: Optional[bool]
    disabledSupport: Optional[bool]
    dataSupport: Optional[bool]
    resolveSupport: Optional[ResolveSupport_]
    honorsChangeAnnotations: Optional[bool]


class CodeActionOptions(WorkDoneProgressOptions, TypedDict):
    codeActionKinds: Optional[List['CodeActionKind']]
    resolveProvider: Optional[bool]


class CodeActionRegistrationOptions(TextDocumentRegistrationOptions, CodeActionOptions, TypedDict):
    pass


class CodeActionParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier
    range: Range
    context: 'CodeActionContext'


class CodeActionKind(Enum):
    Empty = ''
    QuickFix = 'quickfix'
    Refactor = 'refactor'
    RefactorExtract = 'refactor.extract'
    RefactorInline = 'refactor.inline'
    RefactorRewrite = 'refactor.rewrite'
    Source = 'source'
    SourceOrganizeImports = 'source.organizeImports'


class CodeActionContext(TypedDict):
    diagnostics: List[Diagnostic]
    only: Optional[List[CodeActionKind]]


class CodeAction(TypedDict):
    class Disabled_(TypedDict):
        reason: str
    title: str
    kind: Optional[CodeActionKind]
    diagnostics: Optional[List[Diagnostic]]
    isPreferred: Optional[bool]
    disabled: Optional[Disabled_]
    edit: Optional[WorkspaceEdit]
    command: Optional[Command]
    data: Optional[Any]


class CodeLensClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class CodeLensOptions(WorkDoneProgressOptions, TypedDict):
    resolveProvider: Optional[bool]


class CodeLensRegistrationOptions(TextDocumentRegistrationOptions, CodeLensOptions, TypedDict):
    pass


class CodeLensParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier


class CodeLens(TypedDict):
    range: Range
    command: Optional[Command]
    data: Optional[Any]


class CodeLensWorkspaceClientCapabilities(TypedDict):
    refreshSupport: Optional[bool]


class DocumentLinkClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    tooltipSupport: Optional[bool]


class DocumentLinkOptions(WorkDoneProgressOptions, TypedDict):
    resolveProvider: Optional[bool]


class DocumentLinkRegistrationOptions(TextDocumentRegistrationOptions, DocumentLinkOptions, TypedDict):
    pass


class DocumentLinkParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier


class DocumentLink(TypedDict):
    range: Range
    target: Optional[DocumentUri]
    tooltip: Optional[str]
    data: Optional[Any]


class DocumentColorClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class DocumentColorOptions(WorkDoneProgressOptions, TypedDict):
    pass


class DocumentColorRegistrationOptions(TextDocumentRegistrationOptions, StaticRegistrationOptions, DocumentColorOptions, TypedDict):
    pass


class DocumentColorParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier


class ColorInformation(TypedDict):
    range: Range
    color: 'Color'


class Color(TypedDict):
    red: float
    green: float
    blue: float
    alpha: float


class ColorPresentationParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier
    color: Color
    range: Range


class ColorPresentation(TypedDict):
    label: str
    textEdit: Optional[TextEdit]
    additionalTextEdits: Optional[List[TextEdit]]


class DocumentFormattingClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class DocumentFormattingOptions(WorkDoneProgressOptions, TypedDict):
    pass


class DocumentFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentFormattingOptions, TypedDict):
    pass


class DocumentFormattingParams(WorkDoneProgressParams, TypedDict):
    textDocument: TextDocumentIdentifier
    options: 'FormattingOptions'


class FormattingOptions(TypedDict):
    tabSize: int
    insertSpaces: bool
    trimTrailingWhitespace: Optional[bool]
    insertFinalNewline: Optional[bool]
    trimFinalNewlines: Optional[bool]


class DocumentRangeFormattingClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class DocumentRangeFormattingOptions(WorkDoneProgressOptions, TypedDict):
    pass


class DocumentRangeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentRangeFormattingOptions, TypedDict):
    pass


class DocumentRangeFormattingParams(WorkDoneProgressParams, TypedDict):
    textDocument: TextDocumentIdentifier
    range: Range
    options: FormattingOptions


class DocumentOnTypeFormattingClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class DocumentOnTypeFormattingOptions(TypedDict):
    firstTriggerCharacter: str
    moreTriggerCharacter: Optional[List[str]]


class DocumentOnTypeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentOnTypeFormattingOptions, TypedDict):
    pass


class DocumentOnTypeFormattingParams(TextDocumentPositionParams, TypedDict):
    ch: str
    options: FormattingOptions


class PrepareSupportDefaultBehavior(IntEnum):
    Identifier = 1


class RenameClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    prepareSupport: Optional[bool]
    prepareSupportDefaultBehavior: Optional[PrepareSupportDefaultBehavior]
    honorsChangeAnnotations: Optional[bool]


class RenameOptions(WorkDoneProgressOptions, TypedDict):
    prepareProvider: Optional[bool]


class RenameRegistrationOptions(TextDocumentRegistrationOptions, RenameOptions, TypedDict):
    pass


class RenameParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict):
    newName: str


class PrepareRenameParams(TextDocumentPositionParams, TypedDict):
    pass


class FoldingRangeClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]
    rangeLimit: Optional[int]
    lineFoldingOnly: Optional[bool]


class FoldingRangeOptions(WorkDoneProgressOptions, TypedDict):
    pass


class FoldingRangeRegistrationOptions(TextDocumentRegistrationOptions, FoldingRangeOptions, StaticRegistrationOptions, TypedDict):
    pass


class FoldingRangeParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier


class FoldingRangeKind(Enum):
    Comment = 'comment'
    Imports = 'imports'
    Region = 'region'


class FoldingRange(TypedDict):
    startLine: int
    startCharacter: Optional[int]
    endLine: int
    endCharacter: Optional[int]
    kind: Optional[str]


class SelectionRangeClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class SelectionRangeOptions(WorkDoneProgressOptions, TypedDict):
    pass


class SelectionRangeRegistrationOptions(SelectionRangeOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TypedDict):
    pass


class SelectionRangeParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier
    positions: List[Position]


class SelectionRange(TypedDict):
    range: Range
    parent: Optional['SelectionRange']


class CallHierarchyClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class CallHierarchyOptions(WorkDoneProgressOptions, TypedDict):
    pass


class CallHierarchyRegistrationOptions(TextDocumentRegistrationOptions, CallHierarchyOptions, StaticRegistrationOptions, TypedDict):
    pass


class CallHierarchyPrepareParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict):
    pass


class CallHierarchyItem(TypedDict):
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    detail: Optional[str]
    uri: DocumentUri
    range: Range
    selectionRange: Range
    data: Optional[Any]


class CallHierarchyIncomingCallsParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    item: CallHierarchyItem


class CallHierarchyIncomingCall(TypedDict):
    from_: CallHierarchyItem
    fromRanges: List[Range]


class CallHierarchyOutgoingCallsParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    item: CallHierarchyItem


class CallHierarchyOutgoingCall(TypedDict):
    to: CallHierarchyItem
    fromRanges: List[Range]


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


class SemanticTokensLegend(TypedDict):
    tokenTypes: List[str]
    tokenModifiers: List[str]


class SemanticTokensClientCapabilities(TypedDict):
    class Requests_(TypedDict):
        class Range_1(TypedDict):
            pass
        class Full_1(TypedDict):
            delta: Optional[bool]
        range: Union[bool, Range_1, None]
        full: Union[bool, Full_1, None]
    dynamicRegistration: Optional[bool]
    requests: Requests_
    tokenTypes: List[str]
    tokenModifiers: List[str]
    formats: List[TokenFormat]
    overlappingTokenSupport: Optional[bool]
    multilineTokenSupport: Optional[bool]


class SemanticTokensOptions(WorkDoneProgressOptions, TypedDict):
    class Range_1(TypedDict):
        pass
    class Full_1(TypedDict):
        delta: Optional[bool]
    legend: SemanticTokensLegend
    range: Union[bool, Range_1, None]
    full: Union[bool, Full_1, None]


class SemanticTokensRegistrationOptions(TextDocumentRegistrationOptions, SemanticTokensOptions, StaticRegistrationOptions, TypedDict):
    pass


class SemanticTokensParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier


class SemanticTokens(TypedDict):
    resultId: Optional[str]
    data: List[int]


class SemanticTokensPartialResult(TypedDict):
    data: List[int]


class SemanticTokensDeltaParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier
    previousResultId: str


class SemanticTokensDelta(TypedDict):
    resultId: Optional[str]
    edits: List['SemanticTokensEdit']


class SemanticTokensEdit(TypedDict):
    start: int
    deleteCount: int
    data: Optional[List[int]]


class SemanticTokensDeltaPartialResult(TypedDict):
    edits: List[SemanticTokensEdit]


class SemanticTokensRangeParams(WorkDoneProgressParams, PartialResultParams, TypedDict):
    textDocument: TextDocumentIdentifier
    range: Range


class SemanticTokensWorkspaceClientCapabilities(TypedDict):
    refreshSupport: Optional[bool]


class LinkedEditingRangeClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class LinkedEditingRangeOptions(WorkDoneProgressOptions, TypedDict):
    pass


class LinkedEditingRangeRegistrationOptions(TextDocumentRegistrationOptions, LinkedEditingRangeOptions, StaticRegistrationOptions, TypedDict):
    pass


class LinkedEditingRangeParams(TextDocumentPositionParams, WorkDoneProgressParams, TypedDict):
    pass


class LinkedEditingRanges(TypedDict):
    ranges: List[Range]
    wordPattern: Optional[str]


class MonikerClientCapabilities(TypedDict):
    dynamicRegistration: Optional[bool]


class MonikerOptions(WorkDoneProgressOptions, TypedDict):
    pass


class MonikerRegistrationOptions(TextDocumentRegistrationOptions, MonikerOptions, TypedDict):
    pass


class MonikerParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TypedDict):
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


class Moniker(TypedDict):
    scheme: str
    identifier: str
    unique: UniquenessLevel
    kind: Optional[MonikerKind]


ResponseMessage.__fieldtypes__ = {
    'error': [ResponseError]
}
ProgressParams.__fieldtypes__ = {
    'value': [T]
}
Range.__fieldtypes__ = {
    'start': [Position],
    'end': [Position]
}
Location.__fieldtypes__ = {
    'range': [Range]
}
LocationLink.__fieldtypes__ = {
    'originSelectionRange': [Range],
    'targetRange': [Range],
    'targetSelectionRange': [Range]
}
Diagnostic.__fieldtypes__ = {
    'range': [Range],
    'codeDescription': [CodeDescription],
    'relatedInformation': [DiagnosticRelatedInformation]
}
DiagnosticRelatedInformation.__fieldtypes__ = {
    'location': [Location]
}
TextEdit.__fieldtypes__ = {
    'range': [Range]
}
TextDocumentEdit.__fieldtypes__ = {
    'textDocument': [OptionalVersionedTextDocumentIdentifier],
    'edits': [AnnotatedTextEdit]
}
CreateFile.__fieldtypes__ = {
    'options': [CreateFileOptions]
}
RenameFile.__fieldtypes__ = {
    'options': [RenameFileOptions]
}
DeleteFile.__fieldtypes__ = {
    'options': [DeleteFileOptions]
}
WorkspaceEdit.__fieldtypes__ = {
    'changes': [TextEdit],
    'documentChanges': [DeleteFile],
    'changeAnnotations': [ChangeAnnotation]
}
WorkspaceEditClientCapabilities.__fieldtypes__ = {
    'changeAnnotationSupport': [WorkspaceEditClientCapabilities.ChangeAnnotationSupport_]
}
TextDocumentPositionParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier],
    'position': [Position]
}
TextDocumentRegistrationOptions.__fieldtypes__ = {
    'documentSelector': [DocumentSelector]
}
InitializeParams.__fieldtypes__ = {
    'clientInfo': [InitializeParams.ClientInfo_],
    'capabilities': [ClientCapabilities],
    'workspaceFolders': [WorkspaceFolder]
}
TextDocumentClientCapabilities.__fieldtypes__ = {
    'synchronization': [TextDocumentSyncClientCapabilities],
    'completion': [CompletionClientCapabilities],
    'hover': [HoverClientCapabilities],
    'signatureHelp': [SignatureHelpClientCapabilities],
    'declaration': [DeclarationClientCapabilities],
    'definition': [DefinitionClientCapabilities],
    'typeDefinition': [TypeDefinitionClientCapabilities],
    'implementation': [ImplementationClientCapabilities],
    'references': [ReferenceClientCapabilities],
    'documentHighlight': [DocumentHighlightClientCapabilities],
    'documentSymbol': [DocumentSymbolClientCapabilities],
    'codeAction': [CodeActionClientCapabilities],
    'codeLens': [CodeLensClientCapabilities],
    'documentLink': [DocumentLinkClientCapabilities],
    'colorProvider': [DocumentColorClientCapabilities],
    'formatting': [DocumentFormattingClientCapabilities],
    'rangeFormatting': [DocumentRangeFormattingClientCapabilities],
    'onTypeFormatting': [DocumentOnTypeFormattingClientCapabilities],
    'rename': [RenameClientCapabilities],
    'publishDiagnostics': [PublishDiagnosticsClientCapabilities],
    'foldingRange': [FoldingRangeClientCapabilities],
    'selectionRange': [SelectionRangeClientCapabilities],
    'linkedEditingRange': [LinkedEditingRangeClientCapabilities],
    'callHierarchy': [CallHierarchyClientCapabilities],
    'semanticTokens': [SemanticTokensClientCapabilities],
    'moniker': [MonikerClientCapabilities]
}
ClientCapabilities.Workspace_.__fieldtypes__ = {
    'workspaceEdit': [WorkspaceEditClientCapabilities],
    'didChangeConfiguration': [DidChangeConfigurationClientCapabilities],
    'didChangeWatchedFiles': [DidChangeWatchedFilesClientCapabilities],
    'symbol': [WorkspaceSymbolClientCapabilities],
    'executeCommand': [ExecuteCommandClientCapabilities],
    'semanticTokens': [SemanticTokensWorkspaceClientCapabilities],
    'codeLens': [CodeLensWorkspaceClientCapabilities],
    'fileOperations': [ClientCapabilities.Workspace_.FileOperations_]
}
ClientCapabilities.__fieldtypes__ = {
    'workspace': [ClientCapabilities.Workspace_],
    'textDocument': [TextDocumentClientCapabilities],
    'window': [ClientCapabilities.Window_],
    'general': [ClientCapabilities.General_]
}
ClientCapabilities.Window_.__fieldtypes__ = {
    'showMessage': [ShowMessageRequestClientCapabilities],
    'showDocument': [ShowDocumentClientCapabilities]
}
ClientCapabilities.General_.__fieldtypes__ = {
    'regularExpressions': [RegularExpressionsClientCapabilities],
    'markdown': [MarkdownClientCapabilities]
}
InitializeResult.__fieldtypes__ = {
    'capabilities': [ServerCapabilities],
    'serverInfo': [InitializeResult.ServerInfo_]
}
ServerCapabilities.__fieldtypes__ = {
    'completionProvider': [CompletionOptions],
    'hoverProvider': [HoverOptions],
    'signatureHelpProvider': [SignatureHelpOptions],
    'declarationProvider': [DeclarationRegistrationOptions],
    'definitionProvider': [DefinitionOptions],
    'typeDefinitionProvider': [TypeDefinitionRegistrationOptions],
    'implementationProvider': [ImplementationRegistrationOptions],
    'referencesProvider': [ReferenceOptions],
    'documentHighlightProvider': [DocumentHighlightOptions],
    'documentSymbolProvider': [DocumentSymbolOptions],
    'codeActionProvider': [CodeActionOptions],
    'codeLensProvider': [CodeLensOptions],
    'documentLinkProvider': [DocumentLinkOptions],
    'colorProvider': [DocumentColorRegistrationOptions],
    'documentFormattingProvider': [DocumentFormattingOptions],
    'documentRangeFormattingProvider': [DocumentRangeFormattingOptions],
    'documentOnTypeFormattingProvider': [DocumentOnTypeFormattingOptions],
    'renameProvider': [RenameOptions],
    'foldingRangeProvider': [FoldingRangeRegistrationOptions],
    'executeCommandProvider': [ExecuteCommandOptions],
    'selectionRangeProvider': [SelectionRangeRegistrationOptions],
    'linkedEditingRangeProvider': [LinkedEditingRangeRegistrationOptions],
    'callHierarchyProvider': [CallHierarchyRegistrationOptions],
    'semanticTokensProvider': [SemanticTokensRegistrationOptions],
    'monikerProvider': [MonikerRegistrationOptions],
    'workspaceSymbolProvider': [WorkspaceSymbolOptions],
    'workspace': [ServerCapabilities.Workspace_]
}
ServerCapabilities.Workspace_.__fieldtypes__ = {
    'workspaceFolders': [WorkspaceFoldersServerCapabilities],
    'fileOperations': [ServerCapabilities.Workspace_.FileOperations_]
}
ServerCapabilities.Workspace_.FileOperations_.__fieldtypes__ = {
    'didCreate': [FileOperationRegistrationOptions],
    'willCreate': [FileOperationRegistrationOptions],
    'didRename': [FileOperationRegistrationOptions],
    'willRename': [FileOperationRegistrationOptions],
    'didDelete': [FileOperationRegistrationOptions],
    'willDelete': [FileOperationRegistrationOptions]
}
ShowMessageRequestClientCapabilities.__fieldtypes__ = {
    'messageActionItem': [ShowMessageRequestClientCapabilities.MessageActionItem_]
}
ShowMessageRequestParams.__fieldtypes__ = {
    'actions': [MessageActionItem]
}
ShowDocumentParams.__fieldtypes__ = {
    'selection': [Range]
}
RegistrationParams.__fieldtypes__ = {
    'registrations': [Registration]
}
UnregistrationParams.__fieldtypes__ = {
    'unregisterations': [Unregistration]
}
DidChangeWorkspaceFoldersParams.__fieldtypes__ = {
    'event': [WorkspaceFoldersChangeEvent]
}
WorkspaceFoldersChangeEvent.__fieldtypes__ = {
    'added': [WorkspaceFolder],
    'removed': [WorkspaceFolder]
}
ConfigurationParams.__fieldtypes__ = {
    'items': [ConfigurationItem]
}
DidChangeWatchedFilesRegistrationOptions.__fieldtypes__ = {
    'watchers': [FileSystemWatcher]
}
DidChangeWatchedFilesParams.__fieldtypes__ = {
    'changes': [FileEvent]
}
WorkspaceSymbolClientCapabilities.SymbolKind_.__fieldtypes__ = {
    'valueSet': [SymbolKind]
}
WorkspaceSymbolClientCapabilities.__fieldtypes__ = {
    'symbolKind': [WorkspaceSymbolClientCapabilities.SymbolKind_],
    'tagSupport': [WorkspaceSymbolClientCapabilities.TagSupport_]
}
ApplyWorkspaceEditParams.__fieldtypes__ = {
    'edit': [WorkspaceEdit]
}
FileOperationRegistrationOptions.__fieldtypes__ = {
    'filters': [FileOperationFilter]
}
FileOperationPattern.__fieldtypes__ = {
    'options': [FileOperationPatternOptions]
}
FileOperationFilter.__fieldtypes__ = {
    'pattern': [FileOperationPattern]
}
CreateFilesParams.__fieldtypes__ = {
    'files': [FileCreate]
}
RenameFilesParams.__fieldtypes__ = {
    'files': [FileRename]
}
DeleteFilesParams.__fieldtypes__ = {
    'files': [FileDelete]
}
TextDocumentSyncOptions.__fieldtypes__ = {
    'save': [SaveOptions]
}
DidOpenTextDocumentParams.__fieldtypes__ = {
    'textDocument': [TextDocumentItem]
}
DidChangeTextDocumentParams.__fieldtypes__ = {
    'textDocument': [VersionedTextDocumentIdentifier],
    'contentChanges': [TextDocumentContentChangeEvent]
}
TextDocumentContentChangeEvent_0.__fieldtypes__ = {
    'range': [Range]
}
WillSaveTextDocumentParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
DidSaveTextDocumentParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
DidCloseTextDocumentParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
PublishDiagnosticsClientCapabilities.__fieldtypes__ = {
    'tagSupport': [PublishDiagnosticsClientCapabilities.TagSupport_]
}
PublishDiagnosticsParams.__fieldtypes__ = {
    'diagnostics': [Diagnostic]
}
CompletionClientCapabilities.CompletionItem_.__fieldtypes__ = {
    'tagSupport': [CompletionClientCapabilities.CompletionItem_.TagSupport_],
    'resolveSupport': [CompletionClientCapabilities.CompletionItem_.ResolveSupport_],
    'insertTextModeSupport': [CompletionClientCapabilities.CompletionItem_.InsertTextModeSupport_]
}
CompletionClientCapabilities.__fieldtypes__ = {
    'completionItem': [CompletionClientCapabilities.CompletionItem_],
    'completionItemKind': [CompletionClientCapabilities.CompletionItemKind_]
}
CompletionClientCapabilities.CompletionItemKind_.__fieldtypes__ = {
    'valueSet': [CompletionItemKind]
}
CompletionParams.__fieldtypes__ = {
    'context': [CompletionContext]
}
CompletionList.__fieldtypes__ = {
    'items': [CompletionItem]
}
InsertReplaceEdit.__fieldtypes__ = {
    'insert': [Range],
    'replace': [Range]
}
CompletionItem.__fieldtypes__ = {
    'kind': [CompletionItemKind],
    'documentation': [MarkupContent],
    'textEdit': [InsertReplaceEdit],
    'additionalTextEdits': [TextEdit],
    'command': [Command]
}
Hover.__fieldtypes__ = {
    'contents': [MarkupContent],
    'range': [Range]
}
SignatureHelpClientCapabilities.SignatureInformation_.__fieldtypes__ = {
    'parameterInformation': [SignatureHelpClientCapabilities.SignatureInformation_.ParameterInformation_]
}
SignatureHelpClientCapabilities.__fieldtypes__ = {
    'signatureInformation': [SignatureHelpClientCapabilities.SignatureInformation_]
}
SignatureHelpParams.__fieldtypes__ = {
    'context': [SignatureHelpContext]
}
SignatureHelpContext.__fieldtypes__ = {
    'activeSignatureHelp': [SignatureHelp]
}
SignatureHelp.__fieldtypes__ = {
    'signatures': [SignatureInformation]
}
SignatureInformation.__fieldtypes__ = {
    'documentation': [MarkupContent],
    'parameters': [ParameterInformation]
}
ParameterInformation.__fieldtypes__ = {
    'documentation': [MarkupContent]
}
ReferenceParams.__fieldtypes__ = {
    'context': [ReferenceContext]
}
DocumentHighlight.__fieldtypes__ = {
    'range': [Range]
}
DocumentSymbolClientCapabilities.SymbolKind_.__fieldtypes__ = {
    'valueSet': [SymbolKind]
}
DocumentSymbolClientCapabilities.__fieldtypes__ = {
    'symbolKind': [DocumentSymbolClientCapabilities.SymbolKind_],
    'tagSupport': [DocumentSymbolClientCapabilities.TagSupport_]
}
DocumentSymbolParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
DocumentSymbol.__fieldtypes__ = {
    'kind': [SymbolKind],
    'range': [Range],
    'selectionRange': [Range],
    'children': [DocumentSymbol]
}
SymbolInformation.__fieldtypes__ = {
    'kind': [SymbolKind],
    'location': [Location]
}
CodeActionClientCapabilities.CodeActionLiteralSupport_.__fieldtypes__ = {
    'codeActionKind': [CodeActionClientCapabilities.CodeActionLiteralSupport_.CodeActionKind_]
}
CodeActionClientCapabilities.__fieldtypes__ = {
    'codeActionLiteralSupport': [CodeActionClientCapabilities.CodeActionLiteralSupport_],
    'resolveSupport': [CodeActionClientCapabilities.ResolveSupport_]
}
CodeActionParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier],
    'range': [Range],
    'context': [CodeActionContext]
}
CodeActionContext.__fieldtypes__ = {
    'diagnostics': [Diagnostic]
}
CodeAction.__fieldtypes__ = {
    'diagnostics': [Diagnostic],
    'disabled': [CodeAction.Disabled_],
    'edit': [WorkspaceEdit],
    'command': [Command]
}
CodeLensParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
CodeLens.__fieldtypes__ = {
    'range': [Range],
    'command': [Command]
}
DocumentLinkParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
DocumentLink.__fieldtypes__ = {
    'range': [Range]
}
DocumentColorParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
ColorInformation.__fieldtypes__ = {
    'range': [Range],
    'color': [Color]
}
ColorPresentationParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier],
    'color': [Color],
    'range': [Range]
}
ColorPresentation.__fieldtypes__ = {
    'textEdit': [TextEdit],
    'additionalTextEdits': [TextEdit]
}
DocumentFormattingParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier],
    'options': [FormattingOptions]
}
DocumentRangeFormattingParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier],
    'range': [Range],
    'options': [FormattingOptions]
}
DocumentOnTypeFormattingParams.__fieldtypes__ = {
    'options': [FormattingOptions]
}
RenameClientCapabilities.__fieldtypes__ = {
    'prepareSupportDefaultBehavior': [PrepareSupportDefaultBehavior]
}
FoldingRangeParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
SelectionRangeParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier],
    'positions': [Position]
}
SelectionRange.__fieldtypes__ = {
    'range': [Range],
    'parent': [SelectionRange]
}
CallHierarchyItem.__fieldtypes__ = {
    'kind': [SymbolKind],
    'range': [Range],
    'selectionRange': [Range]
}
CallHierarchyIncomingCallsParams.__fieldtypes__ = {
    'item': [CallHierarchyItem]
}
CallHierarchyIncomingCall.__fieldtypes__ = {
    'from_': [CallHierarchyItem],
    'fromRanges': [Range]
}
CallHierarchyOutgoingCallsParams.__fieldtypes__ = {
    'item': [CallHierarchyItem]
}
CallHierarchyOutgoingCall.__fieldtypes__ = {
    'to': [CallHierarchyItem],
    'fromRanges': [Range]
}
SemanticTokensClientCapabilities.Requests_.__fieldtypes__ = {
    'range': [SemanticTokensClientCapabilities.Requests_.Range_1],
    'full': [SemanticTokensClientCapabilities.Requests_.Full_1]
}
SemanticTokensClientCapabilities.__fieldtypes__ = {
    'requests': [SemanticTokensClientCapabilities.Requests_]
}
SemanticTokensOptions.__fieldtypes__ = {
    'legend': [SemanticTokensLegend],
    'range': [SemanticTokensOptions.Range_1],
    'full': [SemanticTokensOptions.Full_1]
}
SemanticTokensParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
SemanticTokensDeltaParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier]
}
SemanticTokensDelta.__fieldtypes__ = {
    'edits': [SemanticTokensEdit]
}
SemanticTokensDeltaPartialResult.__fieldtypes__ = {
    'edits': [SemanticTokensEdit]
}
SemanticTokensRangeParams.__fieldtypes__ = {
    'textDocument': [TextDocumentIdentifier],
    'range': [Range]
}
LinkedEditingRanges.__fieldtypes__ = {
    'ranges': [Range]
}
Moniker.__fieldtypes__ = {
    'unique': [UniquenessLevel],
    'kind': [MonikerKind]
}


RequestMessage.__optional_keys__ = {'params'}
ResponseMessage.__optional_keys__ = {'result', 'error'}
ResponseError.__optional_keys__ = {'data'}
NotificationMessage.__optional_keys__ = {'params'}
RegularExpressionsClientCapabilities.__optional_keys__ = {'version'}
LocationLink.__optional_keys__ = {'originSelectionRange'}
Diagnostic.__optional_keys__ = {'severity', 'code', 'codeDescription', 'source', 'tags', 'relatedInformation', 'data'}
Command.__optional_keys__ = {'arguments'}
ChangeAnnotation.__optional_keys__ = {'needsConfirmation', 'description'}
CreateFileOptions.__optional_keys__ = {'overwrite', 'ignoreIfExists'}
CreateFile.__optional_keys__ = {'options', 'annotationId'}
RenameFileOptions.__optional_keys__ = {'overwrite', 'ignoreIfExists'}
RenameFile.__optional_keys__ = {'options', 'annotationId'}
DeleteFileOptions.__optional_keys__ = {'recursive', 'ignoreIfNotExists'}
DeleteFile.__optional_keys__ = {'options', 'annotationId'}
WorkspaceEdit.__optional_keys__ = {'changes', 'documentChanges', 'changeAnnotations'}
WorkspaceEditClientCapabilities.__optional_keys__ = {'documentChanges', 'resourceOperations', 'failureHandling', 'normalizesLineEndings', 'changeAnnotationSupport'}
WorkspaceEditClientCapabilities.ChangeAnnotationSupport_.__optional_keys__ = {'groupsOnLabel'}
DocumentFilter.__optional_keys__ = {'language', 'scheme', 'pattern'}
StaticRegistrationOptions.__optional_keys__ = {'id'}
MarkdownClientCapabilities.__optional_keys__ = {'version'}
WorkDoneProgressBegin.__optional_keys__ = {'cancellable', 'message', 'percentage'}
WorkDoneProgressReport.__optional_keys__ = {'cancellable', 'message', 'percentage'}
WorkDoneProgressEnd.__optional_keys__ = {'message'}
WorkDoneProgressParams.__optional_keys__ = {'workDoneToken'}
WorkDoneProgressOptions.__optional_keys__ = {'workDoneProgress'}
PartialResultParams.__optional_keys__ = {'partialResultToken'}
InitializeParams.ClientInfo_.__optional_keys__ = {'version'}
InitializeParams.__optional_keys__ = {'clientInfo', 'locale', 'rootPath', 'initializationOptions', 'trace', 'workspaceFolders'}
TextDocumentClientCapabilities.__optional_keys__ = {'synchronization', 'completion', 'hover', 'signatureHelp', 'declaration', 'definition', 'typeDefinition', 'implementation', 'references', 'documentHighlight', 'documentSymbol', 'codeAction', 'codeLens', 'documentLink', 'colorProvider', 'formatting', 'rangeFormatting', 'onTypeFormatting', 'rename', 'publishDiagnostics', 'foldingRange', 'selectionRange', 'linkedEditingRange', 'callHierarchy', 'semanticTokens', 'moniker'}
ClientCapabilities.Workspace_.__optional_keys__ = {'applyEdit', 'workspaceEdit', 'didChangeConfiguration', 'didChangeWatchedFiles', 'symbol', 'executeCommand', 'workspaceFolders', 'configuration', 'semanticTokens', 'codeLens', 'fileOperations'}
ClientCapabilities.Workspace_.FileOperations_.__optional_keys__ = {'dynamicRegistration', 'didCreate', 'willCreate', 'didRename', 'willRename', 'didDelete', 'willDelete'}
ClientCapabilities.__optional_keys__ = {'workspace', 'textDocument', 'window', 'general', 'experimental'}
ClientCapabilities.Window_.__optional_keys__ = {'workDoneProgress', 'showMessage', 'showDocument'}
ClientCapabilities.General_.__optional_keys__ = {'regularExpressions', 'markdown'}
InitializeResult.ServerInfo_.__optional_keys__ = {'version'}
InitializeResult.__optional_keys__ = {'serverInfo'}
ServerCapabilities.__optional_keys__ = {'textDocumentSync', 'completionProvider', 'hoverProvider', 'signatureHelpProvider', 'declarationProvider', 'definitionProvider', 'typeDefinitionProvider', 'implementationProvider', 'referencesProvider', 'documentHighlightProvider', 'documentSymbolProvider', 'codeActionProvider', 'codeLensProvider', 'documentLinkProvider', 'colorProvider', 'documentFormattingProvider', 'documentRangeFormattingProvider', 'documentOnTypeFormattingProvider', 'renameProvider', 'foldingRangeProvider', 'executeCommandProvider', 'selectionRangeProvider', 'linkedEditingRangeProvider', 'callHierarchyProvider', 'semanticTokensProvider', 'monikerProvider', 'workspaceSymbolProvider', 'workspace', 'experimental'}
ServerCapabilities.Workspace_.__optional_keys__ = {'workspaceFolders', 'fileOperations'}
ServerCapabilities.Workspace_.FileOperations_.__optional_keys__ = {'didCreate', 'willCreate', 'didRename', 'willRename', 'didDelete', 'willDelete'}
LogTraceParams.__optional_keys__ = {'verbose'}
ShowMessageRequestClientCapabilities.MessageActionItem_.__optional_keys__ = {'additionalPropertiesSupport'}
ShowMessageRequestClientCapabilities.__optional_keys__ = {'messageActionItem'}
ShowMessageRequestParams.__optional_keys__ = {'actions'}
ShowDocumentParams.__optional_keys__ = {'external', 'takeFocus', 'selection'}
Registration.__optional_keys__ = {'registerOptions'}
WorkspaceFoldersServerCapabilities.__optional_keys__ = {'supported', 'changeNotifications'}
DidChangeConfigurationClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
ConfigurationItem.__optional_keys__ = {'scopeUri', 'section'}
DidChangeWatchedFilesClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
FileSystemWatcher.__optional_keys__ = {'kind'}
WorkspaceSymbolClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'symbolKind', 'tagSupport'}
WorkspaceSymbolClientCapabilities.SymbolKind_.__optional_keys__ = {'valueSet'}
ExecuteCommandClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
ExecuteCommandParams.__optional_keys__ = {'arguments'}
ApplyWorkspaceEditParams.__optional_keys__ = {'label'}
ApplyWorkspaceEditResponse.__optional_keys__ = {'failureReason', 'failedChange'}
FileOperationPatternOptions.__optional_keys__ = {'ignoreCase'}
FileOperationPattern.__optional_keys__ = {'matches', 'options'}
FileOperationFilter.__optional_keys__ = {'scheme'}
TextDocumentSyncOptions.__optional_keys__ = {'openClose', 'change', 'willSave', 'willSaveWaitUntil', 'save'}
TextDocumentContentChangeEvent_0.__optional_keys__ = {'rangeLength'}
SaveOptions.__optional_keys__ = {'includeText'}
TextDocumentSaveRegistrationOptions.__optional_keys__ = {'includeText'}
DidSaveTextDocumentParams.__optional_keys__ = {'text'}
TextDocumentSyncClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'willSave', 'willSaveWaitUntil', 'didSave'}
PublishDiagnosticsClientCapabilities.__optional_keys__ = {'relatedInformation', 'tagSupport', 'versionSupport', 'codeDescriptionSupport', 'dataSupport'}
PublishDiagnosticsParams.__optional_keys__ = {'version'}
CompletionClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'completionItem', 'completionItemKind', 'contextSupport'}
CompletionClientCapabilities.CompletionItem_.__optional_keys__ = {'snippetSupport', 'commitCharactersSupport', 'documentationFormat', 'deprecatedSupport', 'preselectSupport', 'tagSupport', 'insertReplaceSupport', 'resolveSupport', 'insertTextModeSupport'}
CompletionClientCapabilities.CompletionItemKind_.__optional_keys__ = {'valueSet'}
CompletionOptions.__optional_keys__ = {'triggerCharacters', 'allCommitCharacters', 'resolveProvider'}
CompletionParams.__optional_keys__ = {'context'}
CompletionContext.__optional_keys__ = {'triggerCharacter'}
CompletionItem.__optional_keys__ = {'kind', 'tags', 'detail', 'documentation', 'deprecated', 'preselect', 'sortText', 'filterText', 'insertText', 'insertTextFormat', 'insertTextMode', 'textEdit', 'additionalTextEdits', 'commitCharacters', 'command', 'data'}
HoverClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'contentFormat'}
Hover.__optional_keys__ = {'range'}
SignatureHelpClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'signatureInformation', 'contextSupport'}
SignatureHelpClientCapabilities.SignatureInformation_.__optional_keys__ = {'documentationFormat', 'parameterInformation', 'activeParameterSupport'}
SignatureHelpClientCapabilities.SignatureInformation_.ParameterInformation_.__optional_keys__ = {'labelOffsetSupport'}
SignatureHelpOptions.__optional_keys__ = {'triggerCharacters', 'retriggerCharacters'}
SignatureHelpParams.__optional_keys__ = {'context'}
SignatureHelpContext.__optional_keys__ = {'triggerCharacter', 'activeSignatureHelp'}
SignatureHelp.__optional_keys__ = {'activeSignature', 'activeParameter'}
SignatureInformation.__optional_keys__ = {'documentation', 'parameters', 'activeParameter'}
ParameterInformation.__optional_keys__ = {'documentation'}
DeclarationClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'linkSupport'}
DefinitionClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'linkSupport'}
TypeDefinitionClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'linkSupport'}
ImplementationClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'linkSupport'}
ReferenceClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
DocumentHighlightClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
DocumentHighlight.__optional_keys__ = {'kind'}
DocumentSymbolClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'symbolKind', 'hierarchicalDocumentSymbolSupport', 'tagSupport', 'labelSupport'}
DocumentSymbolClientCapabilities.SymbolKind_.__optional_keys__ = {'valueSet'}
DocumentSymbolOptions.__optional_keys__ = {'label'}
DocumentSymbol.__optional_keys__ = {'detail', 'tags', 'deprecated', 'children'}
SymbolInformation.__optional_keys__ = {'tags', 'deprecated', 'containerName'}
CodeActionClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'codeActionLiteralSupport', 'isPreferredSupport', 'disabledSupport', 'dataSupport', 'resolveSupport', 'honorsChangeAnnotations'}
CodeActionOptions.__optional_keys__ = {'codeActionKinds', 'resolveProvider'}
CodeActionContext.__optional_keys__ = {'only'}
CodeAction.__optional_keys__ = {'kind', 'diagnostics', 'isPreferred', 'disabled', 'edit', 'command', 'data'}
CodeLensClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
CodeLensOptions.__optional_keys__ = {'resolveProvider'}
CodeLens.__optional_keys__ = {'command', 'data'}
CodeLensWorkspaceClientCapabilities.__optional_keys__ = {'refreshSupport'}
DocumentLinkClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'tooltipSupport'}
DocumentLinkOptions.__optional_keys__ = {'resolveProvider'}
DocumentLink.__optional_keys__ = {'target', 'tooltip', 'data'}
DocumentColorClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
ColorPresentation.__optional_keys__ = {'textEdit', 'additionalTextEdits'}
DocumentFormattingClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
FormattingOptions.__optional_keys__ = {'trimTrailingWhitespace', 'insertFinalNewline', 'trimFinalNewlines'}
DocumentRangeFormattingClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
DocumentOnTypeFormattingClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
DocumentOnTypeFormattingOptions.__optional_keys__ = {'moreTriggerCharacter'}
RenameClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'prepareSupport', 'prepareSupportDefaultBehavior', 'honorsChangeAnnotations'}
RenameOptions.__optional_keys__ = {'prepareProvider'}
FoldingRangeClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'rangeLimit', 'lineFoldingOnly'}
FoldingRange.__optional_keys__ = {'startCharacter', 'endCharacter', 'kind'}
SelectionRangeClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
SelectionRange.__optional_keys__ = {'parent'}
CallHierarchyClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
CallHierarchyItem.__optional_keys__ = {'tags', 'detail', 'data'}
SemanticTokensClientCapabilities.__optional_keys__ = {'dynamicRegistration', 'overlappingTokenSupport', 'multilineTokenSupport'}
SemanticTokensClientCapabilities.Requests_.__optional_keys__ = {'range', 'full'}
SemanticTokensClientCapabilities.Requests_.Full_1.__optional_keys__ = {'delta'}
SemanticTokensOptions.__optional_keys__ = {'range', 'full'}
SemanticTokensOptions.Full_1.__optional_keys__ = {'delta'}
SemanticTokens.__optional_keys__ = {'resultId'}
SemanticTokensDelta.__optional_keys__ = {'resultId'}
SemanticTokensEdit.__optional_keys__ = {'data'}
SemanticTokensWorkspaceClientCapabilities.__optional_keys__ = {'refreshSupport'}
LinkedEditingRangeClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
LinkedEditingRanges.__optional_keys__ = {'wordPattern'}
MonikerClientCapabilities.__optional_keys__ = {'dynamicRegistration'}
Moniker.__optional_keys__ = {'kind'}


def post_fix_classes(classes: set):
    def post_fix(C):
        nonlocal classes
        annotations = getattr(C, '__annotations__', {})
        fieldtypes = getattr(C, '__fieldtypes__', {})
        optional_keys = set(getattr(C, '__optional_keys__', set()))
        for base in C.__bases__:
            if base in classes:
                classes.remove(base)
                post_fix(base)
            annotations.update(getattr(base, '__annotations__', {}))
            fieldtypes.update(getattr(base, '__fieldtypes__', {}))
            optional_keys.update(getattr(base, '__optional_keys__', set()))
        C.__total__ = not bool(optional_keys)
        C.__annotations__ = annotations
        C.__fieldtypes__ = fieldtypes
        C.__optional_keys__ = frozenset(optional_keys)
        C.__required_keys__ = frozenset(annotations.keys() - optional_keys)

    while classes:
        post_fix(classes.pop())


post_fix_classes({
   Message, RequestMessage, ResponseMessage, 
   ResponseError, NotificationMessage, CancelParams, 
   ProgressParams, RegularExpressionsClientCapabilities, Position, 
   Range, Location, LocationLink, 
   Diagnostic, DiagnosticRelatedInformation, CodeDescription, 
   Command, TextEdit, ChangeAnnotation, 
   AnnotatedTextEdit, TextDocumentEdit, CreateFileOptions, 
   CreateFile, RenameFileOptions, RenameFile, 
   DeleteFileOptions, DeleteFile, WorkspaceEdit, 
   WorkspaceEditClientCapabilities, TextDocumentIdentifier, TextDocumentItem, 
   VersionedTextDocumentIdentifier, OptionalVersionedTextDocumentIdentifier, TextDocumentPositionParams, 
   DocumentFilter, StaticRegistrationOptions, TextDocumentRegistrationOptions, 
   MarkupContent, MarkdownClientCapabilities, WorkDoneProgressBegin, 
   WorkDoneProgressReport, WorkDoneProgressEnd, WorkDoneProgressParams, 
   WorkDoneProgressOptions, PartialResultParams, InitializeParams, 
   TextDocumentClientCapabilities, ClientCapabilities, InitializeResult, 
   InitializeError, ServerCapabilities, InitializedParams, 
   LogTraceParams, SetTraceParams, ShowMessageParams, 
   ShowMessageRequestClientCapabilities, ShowMessageRequestParams, MessageActionItem, 
   ShowDocumentClientCapabilities, ShowDocumentParams, ShowDocumentResult, 
   LogMessageParams, WorkDoneProgressCreateParams, WorkDoneProgressCancelParams, 
   Registration, RegistrationParams, Unregistration, 
   UnregistrationParams, WorkspaceFoldersServerCapabilities, WorkspaceFolder, 
   DidChangeWorkspaceFoldersParams, WorkspaceFoldersChangeEvent, DidChangeConfigurationClientCapabilities, 
   DidChangeConfigurationParams, ConfigurationParams, ConfigurationItem, 
   DidChangeWatchedFilesClientCapabilities, DidChangeWatchedFilesRegistrationOptions, FileSystemWatcher, 
   DidChangeWatchedFilesParams, FileEvent, WorkspaceSymbolClientCapabilities, 
   WorkspaceSymbolOptions, WorkspaceSymbolRegistrationOptions, WorkspaceSymbolParams, 
   ExecuteCommandClientCapabilities, ExecuteCommandOptions, ExecuteCommandRegistrationOptions, 
   ExecuteCommandParams, ApplyWorkspaceEditParams, ApplyWorkspaceEditResponse, 
   FileOperationRegistrationOptions, FileOperationPatternOptions, FileOperationPattern, 
   FileOperationFilter, CreateFilesParams, FileCreate, 
   RenameFilesParams, FileRename, DeleteFilesParams, 
   FileDelete, TextDocumentSyncOptions, DidOpenTextDocumentParams, 
   TextDocumentChangeRegistrationOptions, DidChangeTextDocumentParams, WillSaveTextDocumentParams, 
   SaveOptions, TextDocumentSaveRegistrationOptions, DidSaveTextDocumentParams, 
   DidCloseTextDocumentParams, TextDocumentSyncClientCapabilities, PublishDiagnosticsClientCapabilities, 
   PublishDiagnosticsParams, CompletionClientCapabilities, CompletionOptions, 
   CompletionRegistrationOptions, CompletionParams, CompletionContext, 
   CompletionList, InsertReplaceEdit, CompletionItem, 
   HoverClientCapabilities, HoverOptions, HoverRegistrationOptions, 
   HoverParams, Hover, SignatureHelpClientCapabilities, 
   SignatureHelpOptions, SignatureHelpRegistrationOptions, SignatureHelpParams, 
   SignatureHelpContext, SignatureHelp, SignatureInformation, 
   ParameterInformation, DeclarationClientCapabilities, DeclarationOptions, 
   DeclarationRegistrationOptions, DeclarationParams, DefinitionClientCapabilities, 
   DefinitionOptions, DefinitionRegistrationOptions, DefinitionParams, 
   TypeDefinitionClientCapabilities, TypeDefinitionOptions, TypeDefinitionRegistrationOptions, 
   TypeDefinitionParams, ImplementationClientCapabilities, ImplementationOptions, 
   ImplementationRegistrationOptions, ImplementationParams, ReferenceClientCapabilities, 
   ReferenceOptions, ReferenceRegistrationOptions, ReferenceParams, 
   ReferenceContext, DocumentHighlightClientCapabilities, DocumentHighlightOptions, 
   DocumentHighlightRegistrationOptions, DocumentHighlightParams, DocumentHighlight, 
   DocumentSymbolClientCapabilities, DocumentSymbolOptions, DocumentSymbolRegistrationOptions, 
   DocumentSymbolParams, DocumentSymbol, SymbolInformation, 
   CodeActionClientCapabilities, CodeActionOptions, CodeActionRegistrationOptions, 
   CodeActionParams, CodeActionContext, CodeAction, 
   CodeLensClientCapabilities, CodeLensOptions, CodeLensRegistrationOptions, 
   CodeLensParams, CodeLens, CodeLensWorkspaceClientCapabilities, 
   DocumentLinkClientCapabilities, DocumentLinkOptions, DocumentLinkRegistrationOptions, 
   DocumentLinkParams, DocumentLink, DocumentColorClientCapabilities, 
   DocumentColorOptions, DocumentColorRegistrationOptions, DocumentColorParams, 
   ColorInformation, Color, ColorPresentationParams, 
   ColorPresentation, DocumentFormattingClientCapabilities, DocumentFormattingOptions, 
   DocumentFormattingRegistrationOptions, DocumentFormattingParams, FormattingOptions, 
   DocumentRangeFormattingClientCapabilities, DocumentRangeFormattingOptions, DocumentRangeFormattingRegistrationOptions, 
   DocumentRangeFormattingParams, DocumentOnTypeFormattingClientCapabilities, DocumentOnTypeFormattingOptions, 
   DocumentOnTypeFormattingRegistrationOptions, DocumentOnTypeFormattingParams, RenameClientCapabilities, 
   RenameOptions, RenameRegistrationOptions, RenameParams, 
   PrepareRenameParams, FoldingRangeClientCapabilities, FoldingRangeOptions, 
   FoldingRangeRegistrationOptions, FoldingRangeParams, FoldingRange, 
   SelectionRangeClientCapabilities, SelectionRangeOptions, SelectionRangeRegistrationOptions, 
   SelectionRangeParams, SelectionRange, CallHierarchyClientCapabilities, 
   CallHierarchyOptions, CallHierarchyRegistrationOptions, CallHierarchyPrepareParams, 
   CallHierarchyItem, CallHierarchyIncomingCallsParams, CallHierarchyIncomingCall, 
   CallHierarchyOutgoingCallsParams, CallHierarchyOutgoingCall, SemanticTokensLegend, 
   SemanticTokensClientCapabilities, SemanticTokensOptions, SemanticTokensRegistrationOptions, 
   SemanticTokensParams, SemanticTokens, SemanticTokensPartialResult, 
   SemanticTokensDeltaParams, SemanticTokensDelta, SemanticTokensEdit, 
   SemanticTokensDeltaPartialResult, SemanticTokensRangeParams, SemanticTokensWorkspaceClientCapabilities, 
   LinkedEditingRangeClientCapabilities, LinkedEditingRangeOptions, LinkedEditingRangeRegistrationOptions, 
   LinkedEditingRangeParams, LinkedEditingRanges, MonikerClientCapabilities, 
   MonikerOptions, MonikerRegistrationOptions, MonikerParams, 
   Moniker})


if __name__ == "__main__":
    if __name__ == "__main__":
        msg = Message(jsonrpc="test")
        print(msg)
        msg = RequestMessage(jsonrpc="test", id=1, method="gogogo")
        print(msg)
        msg = RequestMessage(jsonrpc="test", id="2", method="gogogo", params="[1, 2, 3]")
        print(msg)
        msg = RequestMessage(jsonrpc="test", method="gogogo")
        print(RequestMessage.__total__)
        print(RequestMessage.__optional_keys__)
        print(RequestMessage.__required_keys__)
        print(RequestMessage.__annotations__)
