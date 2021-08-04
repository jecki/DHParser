
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Union, List, Tuple, Optional, Dict, Any, Generic, TypeVar

integer = float

uinteger = float

decimal = float


@dataclass
class Message:
    jsonrpc: str


@dataclass
class RequestMessage(Message):
    id: Union[int, str]
    method: str
    params: Optional[Union[List, object]]


@dataclass
class ResponseMessage(Message):
    id: Union[int, str, None]
    result: Optional[Union[str, float, bool, object, None]]
    error: Optional['ResponseError']


@dataclass
class ResponseError:
    code: int
    message: str
    data: Optional[Union[str, float, bool, List, object, None]]


@dataclass
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


@dataclass
class NotificationMessage(Message):
    method: str
    params: Optional[Union[List, object]]


@dataclass
class CancelParams:
    id: Union[int, str]

ProgressToken = Union[int, str]

T = TypeVar('T')


@dataclass
class ProgressParams(Generic[T]):
    token: ProgressToken
    value: 'T'

DocumentUri = str

URI = str


@dataclass
class RegularExpressionsClientCapabilities:
    engine: str
    version: Optional[str]

EOL: List[str] = ['\n', '\r\n', '\r']


@dataclass
class Position:
    line: int
    character: int


@dataclass
class Range:
    start: Position
    end: Position


@dataclass
class Location:
    uri: DocumentUri
    range: Range


@dataclass
class LocationLink:
    originSelectionRange: Optional[Range]
    targetUri: DocumentUri
    targetRange: Range
    targetSelectionRange: Range


@dataclass
class Diagnostic:
    range: Range
    severity: Optional['DiagnosticSeverity']
    code: Optional[Union[int, str]]
    codeDescription: Optional['CodeDescription']
    source: Optional[str]
    message: str
    tags: Optional[List['DiagnosticTag']]
    relatedInformation: Optional[List['DiagnosticRelatedInformation']]
    data: Optional[Any]


@dataclass
class DiagnosticSeverity(IntEnum):
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4


@dataclass
class DiagnosticTag(IntEnum):
    Unnecessary = 1
    Deprecated = 2


@dataclass
class DiagnosticRelatedInformation:
    location: Location
    message: str


@dataclass
class CodeDescription:
    href: URI


@dataclass
class Command:
    title: str
    command: str
    arguments: Optional[List[Any]]


@dataclass
class TextEdit:
    range: Range
    newText: str


@dataclass
class ChangeAnnotation:
    label: str
    needsConfirmation: Optional[bool]
    description: Optional[str]

ChangeAnnotationIdentifier = str


@dataclass
class AnnotatedTextEdit(TextEdit):
    annotationId: ChangeAnnotationIdentifier


@dataclass
class TextDocumentEdit:
    textDocument: 'OptionalVersionedTextDocumentIdentifier'
    edits: List[Union[TextEdit, AnnotatedTextEdit]]


@dataclass
class CreateFileOptions:
    overwrite: Optional[bool]
    ignoreIfExists: Optional[bool]


@dataclass
class CreateFile:
    kind: str
    uri: DocumentUri
    options: Optional[CreateFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


@dataclass
class RenameFileOptions:
    overwrite: Optional[bool]
    ignoreIfExists: Optional[bool]


@dataclass
class RenameFile:
    kind: str
    oldUri: DocumentUri
    newUri: DocumentUri
    options: Optional[RenameFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


@dataclass
class DeleteFileOptions:
    recursive: Optional[bool]
    ignoreIfNotExists: Optional[bool]


@dataclass
class DeleteFile:
    kind: str
    uri: DocumentUri
    options: Optional[DeleteFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


@dataclass
class WorkspaceEdit:
    changes: Optional[Dict[DocumentUri, List[TextEdit]]]
    documentChanges: Optional[Union[List[TextDocumentEdit], List[Union[TextDocumentEdit, CreateFile, RenameFile, DeleteFile]]]]
    changeAnnotations: Optional[Dict[str, ChangeAnnotation]]


@dataclass
class ChangeAnnotationSupport_:
    groupsOnLabel: Optional[bool]


@dataclass
class WorkspaceEditClientCapabilities:
    documentChanges: Optional[bool]
    resourceOperations: Optional[List['ResourceOperationKind']]
    failureHandling: Optional['FailureHandlingKind']
    normalizesLineEndings: Optional[bool]
    changeAnnotationSupport: ChangeAnnotationSupport_


@dataclass
class ResourceOperationKind(Enum):
    Create = 'create'
    Rename = 'rename'
    Delete = 'delete'


@dataclass
class FailureHandlingKind(Enum):
    Abort = 'abort'
    Transactional = 'transactional'
    TextOnlyTransactional = 'textOnlyTransactional'
    Undo = 'undo'


@dataclass
class TextDocumentIdentifier:
    uri: DocumentUri


@dataclass
class TextDocumentItem:
    uri: DocumentUri
    languageId: str
    version: int
    text: str


@dataclass
class VersionedTextDocumentIdentifier(TextDocumentIdentifier):
    version: int


@dataclass
class OptionalVersionedTextDocumentIdentifier(TextDocumentIdentifier):
    version: Union[int, None]


@dataclass
class TextDocumentPositionParams:
    textDocument: TextDocumentIdentifier
    position: Position


@dataclass
class DocumentFilter:
    language: Optional[str]
    scheme: Optional[str]
    pattern: Optional[str]

DocumentSelector = List[DocumentFilter]


@dataclass
class StaticRegistrationOptions:
    id: Optional[str]


@dataclass
class TextDocumentRegistrationOptions:
    documentSelector: Union[DocumentSelector, None]


@dataclass
class MarkupKind(Enum):
    PlainText = 'plaintext'
    Markdown = 'markdown'


@dataclass
class MarkupContent:
    kind: MarkupKind
    value: str


@dataclass
class MarkdownClientCapabilities:
    parser: str
    version: Optional[str]


@dataclass
class WorkDoneProgressBegin:
    kind: str
    title: str
    cancellable: Optional[bool]
    message: Optional[str]
    percentage: Optional[int]


@dataclass
class WorkDoneProgressReport:
    kind: str
    cancellable: Optional[bool]
    message: Optional[str]
    percentage: Optional[int]


@dataclass
class WorkDoneProgressEnd:
    kind: str
    message: Optional[str]


@dataclass
class WorkDoneProgressParams:
    workDoneToken: Optional[ProgressToken]


@dataclass
class WorkDoneProgressOptions:
    workDoneProgress: Optional[bool]

window: Optional[Dict]


@dataclass
class PartialResultParams:
    partialResultToken: Optional[ProgressToken]

TraceValue = Union[str]


@dataclass
class ClientInfo_:
    name: str
    version: Optional[str]


@dataclass
class InitializeParams(WorkDoneProgressParams):
    processId: Union[int, None]
    clientInfo: ClientInfo_
    locale: Optional[str]
    rootPath: Optional[Union[str, None]]
    rootUri: Union[DocumentUri, None]
    initializationOptions: Optional[Any]
    capabilities: 'ClientCapabilities'
    trace: Optional[TraceValue]
    workspaceFolders: Optional[Union[List['WorkspaceFolder'], None]]


@dataclass
class TextDocumentClientCapabilities:
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


@dataclass
class FileOperations_:
    dynamicRegistration: Optional[bool]
    didCreate: Optional[bool]
    willCreate: Optional[bool]
    didRename: Optional[bool]
    willRename: Optional[bool]
    didDelete: Optional[bool]
    willDelete: Optional[bool]


@dataclass
class Workspace_:
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
    fileOperations: FileOperations_


@dataclass
class Window_:
    workDoneProgress: Optional[bool]
    showMessage: Optional['ShowMessageRequestClientCapabilities']
    showDocument: Optional['ShowDocumentClientCapabilities']


@dataclass
class General_:
    regularExpressions: Optional[RegularExpressionsClientCapabilities]
    markdown: Optional[MarkdownClientCapabilities]


@dataclass
class ClientCapabilities:
    workspace: Workspace_
    textDocument: Optional[TextDocumentClientCapabilities]
    window: Window_
    general: General_
    experimental: Optional[Any]


@dataclass
class ServerInfo_:
    name: str
    version: Optional[str]


@dataclass
class InitializeResult:
    capabilities: 'ServerCapabilities'
    serverInfo: ServerInfo_


@dataclass
class InitializeError(IntEnum):
    unknownProtocolVersion = 1


@dataclass
class InitializeError:
    retry: bool


@dataclass
class FileOperations_:
    didCreate: Optional['FileOperationRegistrationOptions']
    willCreate: Optional['FileOperationRegistrationOptions']
    didRename: Optional['FileOperationRegistrationOptions']
    willRename: Optional['FileOperationRegistrationOptions']
    didDelete: Optional['FileOperationRegistrationOptions']
    willDelete: Optional['FileOperationRegistrationOptions']


@dataclass
class Workspace_:
    workspaceFolders: Optional['WorkspaceFoldersServerCapabilities']
    fileOperations: FileOperations_


@dataclass
class ServerCapabilities:
    textDocumentSync: Optional[Union['TextDocumentSyncOptions', 'TextDocumentSyncKind']]
    completionProvider: Optional['CompletionOptions']
    hoverProvider: Optional[Union[bool, 'HoverOptions']]
    signatureHelpProvider: Optional['SignatureHelpOptions']
    declarationProvider: Optional[Union[bool, 'DeclarationOptions', 'DeclarationRegistrationOptions']]
    definitionProvider: Optional[Union[bool, 'DefinitionOptions']]
    typeDefinitionProvider: Optional[Union[bool, 'TypeDefinitionOptions', 'TypeDefinitionRegistrationOptions']]
    implementationProvider: Optional[Union[bool, 'ImplementationOptions', 'ImplementationRegistrationOptions']]
    referencesProvider: Optional[Union[bool, 'ReferenceOptions']]
    documentHighlightProvider: Optional[Union[bool, 'DocumentHighlightOptions']]
    documentSymbolProvider: Optional[Union[bool, 'DocumentSymbolOptions']]
    codeActionProvider: Optional[Union[bool, 'CodeActionOptions']]
    codeLensProvider: Optional['CodeLensOptions']
    documentLinkProvider: Optional['DocumentLinkOptions']
    colorProvider: Optional[Union[bool, 'DocumentColorOptions', 'DocumentColorRegistrationOptions']]
    documentFormattingProvider: Optional[Union[bool, 'DocumentFormattingOptions']]
    documentRangeFormattingProvider: Optional[Union[bool, 'DocumentRangeFormattingOptions']]
    documentOnTypeFormattingProvider: Optional['DocumentOnTypeFormattingOptions']
    renameProvider: Optional[Union[bool, 'RenameOptions']]
    foldingRangeProvider: Optional[Union[bool, 'FoldingRangeOptions', 'FoldingRangeRegistrationOptions']]
    executeCommandProvider: Optional['ExecuteCommandOptions']
    selectionRangeProvider: Optional[Union[bool, 'SelectionRangeOptions', 'SelectionRangeRegistrationOptions']]
    linkedEditingRangeProvider: Optional[Union[bool, 'LinkedEditingRangeOptions', 'LinkedEditingRangeRegistrationOptions']]
    callHierarchyProvider: Optional[Union[bool, 'CallHierarchyOptions', 'CallHierarchyRegistrationOptions']]
    semanticTokensProvider: Optional[Union['SemanticTokensOptions', 'SemanticTokensRegistrationOptions']]
    monikerProvider: Optional[Union[bool, 'MonikerOptions', 'MonikerRegistrationOptions']]
    workspaceSymbolProvider: Optional[Union[bool, 'WorkspaceSymbolOptions']]
    workspace: Workspace_
    experimental: Optional[Any]


@dataclass
class InitializedParams:
    pass


@dataclass
class LogTraceParams:
    message: str
    verbose: Optional[str]


@dataclass
class SetTraceParams:
    value: TraceValue


@dataclass
class ShowMessageParams:
    type: 'MessageType'
    message: str


@dataclass
class MessageType(IntEnum):
    Error = 1
    Warning = 2
    Info = 3
    Log = 4


@dataclass
class MessageActionItem_:
    additionalPropertiesSupport: Optional[bool]


@dataclass
class ShowMessageRequestClientCapabilities:
    messageActionItem: MessageActionItem_


@dataclass
class ShowMessageRequestParams:
    type: MessageType
    message: str
    actions: Optional[List['MessageActionItem']]


@dataclass
class MessageActionItem:
    title: str


@dataclass
class ShowDocumentClientCapabilities:
    support: bool


@dataclass
class ShowDocumentParams:
    uri: URI
    external: Optional[bool]
    takeFocus: Optional[bool]
    selection: Optional[Range]


@dataclass
class ShowDocumentResult:
    success: bool


@dataclass
class LogMessageParams:
    type: MessageType
    message: str


@dataclass
class WorkDoneProgressCreateParams:
    token: ProgressToken


@dataclass
class WorkDoneProgressCancelParams:
    token: ProgressToken


@dataclass
class Registration:
    id: str
    method: str
    registerOptions: Optional[Any]


@dataclass
class RegistrationParams:
    registrations: List[Registration]


@dataclass
class Unregistration:
    id: str
    method: str


@dataclass
class UnregistrationParams:
    unregisterations: List[Unregistration]


@dataclass
class WorkspaceFoldersServerCapabilities:
    supported: Optional[bool]
    changeNotifications: Optional[Union[str, bool]]


@dataclass
class WorkspaceFolder:
    uri: DocumentUri
    name: str


@dataclass
class DidChangeWorkspaceFoldersParams:
    event: 'WorkspaceFoldersChangeEvent'


@dataclass
class WorkspaceFoldersChangeEvent:
    added: List[WorkspaceFolder]
    removed: List[WorkspaceFolder]


@dataclass
class DidChangeConfigurationClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class DidChangeConfigurationParams:
    settings: Any


@dataclass
class ConfigurationParams:
    items: List['ConfigurationItem']


@dataclass
class ConfigurationItem:
    scopeUri: Optional[DocumentUri]
    section: Optional[str]


@dataclass
class DidChangeWatchedFilesClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class DidChangeWatchedFilesRegistrationOptions:
    watchers: List['FileSystemWatcher']


@dataclass
class FileSystemWatcher:
    globPattern: str
    kind: Optional[int]


@dataclass
class WatchKind(IntEnum):
    Create = 1
    Change = 2
    Delete = 4


@dataclass
class DidChangeWatchedFilesParams:
    changes: List['FileEvent']


@dataclass
class FileEvent:
    uri: DocumentUri
    type: int


@dataclass
class FileChangeType(IntEnum):
    Created = 1
    Changed = 2
    Deleted = 3


@dataclass
class SymbolKind_:
    valueSet: Optional[List['SymbolKind']]


@dataclass
class TagSupport_:
    valueSet: List['SymbolTag']


@dataclass
class WorkspaceSymbolClientCapabilities:
    dynamicRegistration: Optional[bool]
    symbolKind: SymbolKind_
    tagSupport: TagSupport_


@dataclass
class WorkspaceSymbolOptions(WorkDoneProgressOptions):
    pass


@dataclass
class WorkspaceSymbolRegistrationOptions(WorkspaceSymbolOptions):
    pass


@dataclass
class WorkspaceSymbolParams(WorkDoneProgressParams, PartialResultParams):
    query: str


@dataclass
class ExecuteCommandClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class ExecuteCommandOptions(WorkDoneProgressOptions):
    commands: List[str]


@dataclass
class ExecuteCommandRegistrationOptions(ExecuteCommandOptions):
    pass


@dataclass
class ExecuteCommandParams(WorkDoneProgressParams):
    command: str
    arguments: Optional[List[Any]]


@dataclass
class ApplyWorkspaceEditParams:
    label: Optional[str]
    edit: WorkspaceEdit


@dataclass
class ApplyWorkspaceEditResponse:
    applied: bool
    failureReason: Optional[str]
    failedChange: Optional[int]


@dataclass
class FileOperationRegistrationOptions:
    filters: List['FileOperationFilter']


@dataclass
class FileOperationPatternKind(Enum):
    file = 'file'
    folder = 'folder'


@dataclass
class FileOperationPatternOptions:
    ignoreCase: Optional[bool]


@dataclass
class FileOperationPattern:
    glob: str
    matches: Optional[FileOperationPatternKind]
    options: Optional[FileOperationPatternOptions]


@dataclass
class FileOperationFilter:
    scheme: Optional[str]
    pattern: FileOperationPattern


@dataclass
class CreateFilesParams:
    files: List['FileCreate']


@dataclass
class FileCreate:
    uri: str


@dataclass
class RenameFilesParams:
    files: List['FileRename']


@dataclass
class FileRename:
    oldUri: str
    newUri: str


@dataclass
class DeleteFilesParams:
    files: List['FileDelete']


@dataclass
class FileDelete:
    uri: str


@dataclass
class TextDocumentSyncKind(IntEnum):
    None_ = 0
    Full = 1
    Incremental = 2


@dataclass
class TextDocumentSyncOptions:
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]


@dataclass
class DidOpenTextDocumentParams:
    textDocument: TextDocumentItem


@dataclass
class TextDocumentChangeRegistrationOptions(TextDocumentRegistrationOptions):
    syncKind: TextDocumentSyncKind


@dataclass
class DidChangeTextDocumentParams:
    textDocument: VersionedTextDocumentIdentifier
    contentChanges: List['TextDocumentContentChangeEvent']


@dataclass
class TextDocumentContentChangeEvent_0:
    range: Range
    rangeLength: Optional[int]
    text: str


@dataclass
class TextDocumentContentChangeEvent_1:
    text: str

TextDocumentContentChangeEvent = Union[TextDocumentContentChangeEvent_0, TextDocumentContentChangeEvent_1]


@dataclass
class WillSaveTextDocumentParams:
    textDocument: TextDocumentIdentifier
    reason: 'TextDocumentSaveReason'


@dataclass
class TextDocumentSaveReason(IntEnum):
    Manual = 1
    AfterDelay = 2
    FocusOut = 3


@dataclass
class SaveOptions:
    includeText: Optional[bool]


@dataclass
class TextDocumentSaveRegistrationOptions(TextDocumentRegistrationOptions):
    includeText: Optional[bool]


@dataclass
class DidSaveTextDocumentParams:
    textDocument: TextDocumentIdentifier
    text: Optional[str]


@dataclass
class DidCloseTextDocumentParams:
    textDocument: TextDocumentIdentifier


@dataclass
class TextDocumentSyncClientCapabilities:
    dynamicRegistration: Optional[bool]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    didSave: Optional[bool]


@dataclass
class TextDocumentSyncKind(IntEnum):
    None_ = 0
    Full = 1
    Incremental = 2


@dataclass
class TextDocumentSyncOptions:
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    save: Optional[Union[bool, SaveOptions]]


@dataclass
class TagSupport_:
    valueSet: List[DiagnosticTag]


@dataclass
class PublishDiagnosticsClientCapabilities:
    relatedInformation: Optional[bool]
    tagSupport: TagSupport_
    versionSupport: Optional[bool]
    codeDescriptionSupport: Optional[bool]
    dataSupport: Optional[bool]


@dataclass
class PublishDiagnosticsParams:
    uri: DocumentUri
    version: Optional[int]
    diagnostics: List[Diagnostic]


@dataclass
class TagSupport_:
    valueSet: List['CompletionItemTag']


@dataclass
class ResolveSupport_:
    properties: List[str]


@dataclass
class InsertTextModeSupport_:
    valueSet: List['InsertTextMode']


@dataclass
class CompletionItem_:
    snippetSupport: Optional[bool]
    commitCharactersSupport: Optional[bool]
    documentationFormat: Optional[List[MarkupKind]]
    deprecatedSupport: Optional[bool]
    preselectSupport: Optional[bool]
    tagSupport: TagSupport_
    insertReplaceSupport: Optional[bool]
    resolveSupport: ResolveSupport_
    insertTextModeSupport: InsertTextModeSupport_


@dataclass
class CompletionItemKind_:
    valueSet: Optional[List['CompletionItemKind']]


@dataclass
class CompletionClientCapabilities:
    dynamicRegistration: Optional[bool]
    completionItem: CompletionItem_
    completionItemKind: CompletionItemKind_
    contextSupport: Optional[bool]


@dataclass
class CompletionOptions(WorkDoneProgressOptions):
    triggerCharacters: Optional[List[str]]
    allCommitCharacters: Optional[List[str]]
    resolveProvider: Optional[bool]


@dataclass
class CompletionRegistrationOptions(TextDocumentRegistrationOptions, CompletionOptions):
    pass


@dataclass
class CompletionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    context: Optional['CompletionContext']


@dataclass
class CompletionTriggerKind(IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    TriggerForIncompleteCompletions = 3


@dataclass
class CompletionContext:
    triggerKind: CompletionTriggerKind
    triggerCharacter: Optional[str]


@dataclass
class CompletionList:
    isIncomplete: bool
    items: List['CompletionItem']


@dataclass
class InsertTextFormat(IntEnum):
    PlainText = 1
    Snippet = 2


@dataclass
class CompletionItemTag(IntEnum):
    Deprecated = 1


@dataclass
class InsertReplaceEdit:
    newText: str
    insert: Range
    replace: Range


@dataclass
class InsertTextMode(IntEnum):
    asIs = 1
    adjustIndentation = 2


@dataclass
class CompletionItem:
    label: str
    kind: Optional['CompletionItemKind']
    tags: Optional[List[CompletionItemTag]]
    detail: Optional[str]
    documentation: Optional[Union[str, MarkupContent]]
    deprecated: Optional[bool]
    preselect: Optional[bool]
    sortText: Optional[str]
    filterText: Optional[str]
    insertText: Optional[str]
    insertTextFormat: Optional[InsertTextFormat]
    insertTextMode: Optional[InsertTextMode]
    textEdit: Optional[Union[TextEdit, InsertReplaceEdit]]
    additionalTextEdits: Optional[List[TextEdit]]
    commitCharacters: Optional[List[str]]
    command: Optional[Command]
    data: Optional[Any]


@dataclass
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


@dataclass
class HoverClientCapabilities:
    dynamicRegistration: Optional[bool]
    contentFormat: Optional[List[MarkupKind]]


@dataclass
class HoverOptions(WorkDoneProgressOptions):
    pass


@dataclass
class HoverRegistrationOptions(TextDocumentRegistrationOptions, HoverOptions):
    pass


@dataclass
class HoverParams(TextDocumentPositionParams, WorkDoneProgressParams):
    pass


@dataclass
class Hover:
    contents: Union['MarkedString', List['MarkedString'], MarkupContent]
    range: Optional[Range]


@dataclass
class MarkedString_1:
    language: str
    value: str

MarkedString = Union[str, MarkedString_1]


@dataclass
class ParameterInformation_:
    labelOffsetSupport: Optional[bool]


@dataclass
class SignatureInformation_:
    documentationFormat: Optional[List[MarkupKind]]
    parameterInformation: ParameterInformation_
    activeParameterSupport: Optional[bool]


@dataclass
class SignatureHelpClientCapabilities:
    dynamicRegistration: Optional[bool]
    signatureInformation: SignatureInformation_
    contextSupport: Optional[bool]


@dataclass
class SignatureHelpOptions(WorkDoneProgressOptions):
    triggerCharacters: Optional[List[str]]
    retriggerCharacters: Optional[List[str]]


@dataclass
class SignatureHelpRegistrationOptions(TextDocumentRegistrationOptions, SignatureHelpOptions):
    pass


@dataclass
class SignatureHelpParams(TextDocumentPositionParams, WorkDoneProgressParams):
    context: Optional['SignatureHelpContext']


@dataclass
class SignatureHelpTriggerKind(IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    ContentChange = 3


@dataclass
class SignatureHelpContext:
    triggerKind: SignatureHelpTriggerKind
    triggerCharacter: Optional[str]
    isRetrigger: bool
    activeSignatureHelp: Optional['SignatureHelp']


@dataclass
class SignatureHelp:
    signatures: List['SignatureInformation']
    activeSignature: Optional[int]
    activeParameter: Optional[int]


@dataclass
class SignatureInformation:
    label: str
    documentation: Optional[Union[str, MarkupContent]]
    parameters: Optional[List['ParameterInformation']]
    activeParameter: Optional[int]


@dataclass
class ParameterInformation:
    label: Union[str, Tuple[int, int]]
    documentation: Optional[Union[str, MarkupContent]]


@dataclass
class DeclarationClientCapabilities:
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


@dataclass
class DeclarationOptions(WorkDoneProgressOptions):
    pass


@dataclass
class DeclarationRegistrationOptions(DeclarationOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions):
    pass


@dataclass
class DeclarationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


@dataclass
class DefinitionClientCapabilities:
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


@dataclass
class DefinitionOptions(WorkDoneProgressOptions):
    pass


@dataclass
class DefinitionRegistrationOptions(TextDocumentRegistrationOptions, DefinitionOptions):
    pass


@dataclass
class DefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


@dataclass
class TypeDefinitionClientCapabilities:
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


@dataclass
class TypeDefinitionOptions(WorkDoneProgressOptions):
    pass


@dataclass
class TypeDefinitionRegistrationOptions(TextDocumentRegistrationOptions, TypeDefinitionOptions, StaticRegistrationOptions):
    pass


@dataclass
class TypeDefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


@dataclass
class ImplementationClientCapabilities:
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


@dataclass
class ImplementationOptions(WorkDoneProgressOptions):
    pass


@dataclass
class ImplementationRegistrationOptions(TextDocumentRegistrationOptions, ImplementationOptions, StaticRegistrationOptions):
    pass


@dataclass
class ImplementationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


@dataclass
class ReferenceClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class ReferenceOptions(WorkDoneProgressOptions):
    pass


@dataclass
class ReferenceRegistrationOptions(TextDocumentRegistrationOptions, ReferenceOptions):
    pass


@dataclass
class ReferenceParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    context: 'ReferenceContext'


@dataclass
class ReferenceContext:
    includeDeclaration: bool


@dataclass
class DocumentHighlightClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class DocumentHighlightOptions(WorkDoneProgressOptions):
    pass


@dataclass
class DocumentHighlightRegistrationOptions(TextDocumentRegistrationOptions, DocumentHighlightOptions):
    pass


@dataclass
class DocumentHighlightParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


@dataclass
class DocumentHighlight:
    range: Range
    kind: Optional['DocumentHighlightKind']


@dataclass
class DocumentHighlightKind(IntEnum):
    Text = 1
    Read = 2
    Write = 3


@dataclass
class SymbolKind_:
    valueSet: Optional[List['SymbolKind']]


@dataclass
class TagSupport_:
    valueSet: List['SymbolTag']


@dataclass
class DocumentSymbolClientCapabilities:
    dynamicRegistration: Optional[bool]
    symbolKind: SymbolKind_
    hierarchicalDocumentSymbolSupport: Optional[bool]
    tagSupport: TagSupport_
    labelSupport: Optional[bool]


@dataclass
class DocumentSymbolOptions(WorkDoneProgressOptions):
    label: Optional[str]


@dataclass
class DocumentSymbolRegistrationOptions(TextDocumentRegistrationOptions, DocumentSymbolOptions):
    pass


@dataclass
class DocumentSymbolParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier


@dataclass
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


@dataclass
class SymbolTag(IntEnum):
    Deprecated = 1


@dataclass
class DocumentSymbol:
    name: str
    detail: Optional[str]
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    deprecated: Optional[bool]
    range: Range
    selectionRange: Range
    children: Optional[List['DocumentSymbol']]


@dataclass
class SymbolInformation:
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    deprecated: Optional[bool]
    location: Location
    containerName: Optional[str]


@dataclass
class CodeActionKind_:
    valueSet: List['CodeActionKind']


@dataclass
class CodeActionLiteralSupport_:
    codeActionKind: CodeActionKind_


@dataclass
class ResolveSupport_:
    properties: List[str]


@dataclass
class CodeActionClientCapabilities:
    dynamicRegistration: Optional[bool]
    codeActionLiteralSupport: CodeActionLiteralSupport_
    isPreferredSupport: Optional[bool]
    disabledSupport: Optional[bool]
    dataSupport: Optional[bool]
    resolveSupport: ResolveSupport_
    honorsChangeAnnotations: Optional[bool]


@dataclass
class CodeActionOptions(WorkDoneProgressOptions):
    codeActionKinds: Optional[List['CodeActionKind']]
    resolveProvider: Optional[bool]


@dataclass
class CodeActionRegistrationOptions(TextDocumentRegistrationOptions, CodeActionOptions):
    pass


@dataclass
class CodeActionParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier
    range: Range
    context: 'CodeActionContext'


@dataclass
class CodeActionKind(Enum):
    Empty = ''
    QuickFix = 'quickfix'
    Refactor = 'refactor'
    RefactorExtract = 'refactor.extract'
    RefactorInline = 'refactor.inline'
    RefactorRewrite = 'refactor.rewrite'
    Source = 'source'
    SourceOrganizeImports = 'source.organizeImports'


@dataclass
class CodeActionContext:
    diagnostics: List[Diagnostic]
    only: Optional[List[CodeActionKind]]


@dataclass
class Disabled_:
    reason: str


@dataclass
class CodeAction:
    title: str
    kind: Optional[CodeActionKind]
    diagnostics: Optional[List[Diagnostic]]
    isPreferred: Optional[bool]
    disabled: Disabled_
    edit: Optional[WorkspaceEdit]
    command: Optional[Command]
    data: Optional[Any]


@dataclass
class CodeLensClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class CodeLensOptions(WorkDoneProgressOptions):
    resolveProvider: Optional[bool]


@dataclass
class CodeLensRegistrationOptions(TextDocumentRegistrationOptions, CodeLensOptions):
    pass


@dataclass
class CodeLensParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier


@dataclass
class CodeLens:
    range: Range
    command: Optional[Command]
    data: Optional[Any]


@dataclass
class CodeLensWorkspaceClientCapabilities:
    refreshSupport: Optional[bool]


@dataclass
class DocumentLinkClientCapabilities:
    dynamicRegistration: Optional[bool]
    tooltipSupport: Optional[bool]


@dataclass
class DocumentLinkOptions(WorkDoneProgressOptions):
    resolveProvider: Optional[bool]


@dataclass
class DocumentLinkRegistrationOptions(TextDocumentRegistrationOptions, DocumentLinkOptions):
    pass


@dataclass
class DocumentLinkParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier


@dataclass
class DocumentLink:
    range: Range
    target: Optional[DocumentUri]
    tooltip: Optional[str]
    data: Optional[Any]


@dataclass
class DocumentColorClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class DocumentColorOptions(WorkDoneProgressOptions):
    pass


@dataclass
class DocumentColorRegistrationOptions(TextDocumentRegistrationOptions, StaticRegistrationOptions, DocumentColorOptions):
    pass


@dataclass
class DocumentColorParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier


@dataclass
class ColorInformation:
    range: Range
    color: 'Color'


@dataclass
class Color:
    red: float
    green: float
    blue: float
    alpha: float


@dataclass
class ColorPresentationParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier
    color: Color
    range: Range


@dataclass
class ColorPresentation:
    label: str
    textEdit: Optional[TextEdit]
    additionalTextEdits: Optional[List[TextEdit]]


@dataclass
class DocumentFormattingClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class DocumentFormattingOptions(WorkDoneProgressOptions):
    pass


@dataclass
class DocumentFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentFormattingOptions):
    pass


@dataclass
class DocumentFormattingParams(WorkDoneProgressParams):
    textDocument: TextDocumentIdentifier
    options: 'FormattingOptions'


@dataclass
class FormattingOptions:
    tabSize: int
    insertSpaces: bool
    trimTrailingWhitespace: Optional[bool]
    insertFinalNewline: Optional[bool]
    trimFinalNewlines: Optional[bool]


@dataclass
class DocumentRangeFormattingClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class DocumentRangeFormattingOptions(WorkDoneProgressOptions):
    pass


@dataclass
class DocumentRangeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentRangeFormattingOptions):
    pass


@dataclass
class DocumentRangeFormattingParams(WorkDoneProgressParams):
    textDocument: TextDocumentIdentifier
    range: Range
    options: FormattingOptions


@dataclass
class DocumentOnTypeFormattingClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class DocumentOnTypeFormattingOptions:
    firstTriggerCharacter: str
    moreTriggerCharacter: Optional[List[str]]


@dataclass
class DocumentOnTypeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentOnTypeFormattingOptions):
    pass


@dataclass
class DocumentOnTypeFormattingParams(TextDocumentPositionParams):
    ch: str
    options: FormattingOptions


@dataclass
class PrepareSupportDefaultBehavior(IntEnum):
    Identifier = 1


@dataclass
class RenameClientCapabilities:
    dynamicRegistration: Optional[bool]
    prepareSupport: Optional[bool]
    prepareSupportDefaultBehavior: Optional[PrepareSupportDefaultBehavior]
    honorsChangeAnnotations: Optional[bool]


@dataclass
class RenameOptions(WorkDoneProgressOptions):
    prepareProvider: Optional[bool]


@dataclass
class RenameRegistrationOptions(TextDocumentRegistrationOptions, RenameOptions):
    pass


@dataclass
class RenameParams(TextDocumentPositionParams, WorkDoneProgressParams):
    newName: str


@dataclass
class PrepareRenameParams(TextDocumentPositionParams):
    pass


@dataclass
class FoldingRangeClientCapabilities:
    dynamicRegistration: Optional[bool]
    rangeLimit: Optional[int]
    lineFoldingOnly: Optional[bool]


@dataclass
class FoldingRangeOptions(WorkDoneProgressOptions):
    pass


@dataclass
class FoldingRangeRegistrationOptions(TextDocumentRegistrationOptions, FoldingRangeOptions, StaticRegistrationOptions):
    pass


@dataclass
class FoldingRangeParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier


@dataclass
class FoldingRangeKind(Enum):
    Comment = 'comment'
    Imports = 'imports'
    Region = 'region'


@dataclass
class FoldingRange:
    startLine: int
    startCharacter: Optional[int]
    endLine: int
    endCharacter: Optional[int]
    kind: Optional[str]


@dataclass
class SelectionRangeClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class SelectionRangeOptions(WorkDoneProgressOptions):
    pass


@dataclass
class SelectionRangeRegistrationOptions(SelectionRangeOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions):
    pass


@dataclass
class SelectionRangeParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier
    positions: List[Position]


@dataclass
class SelectionRange:
    range: Range
    parent: Optional['SelectionRange']


@dataclass
class CallHierarchyClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class CallHierarchyOptions(WorkDoneProgressOptions):
    pass


@dataclass
class CallHierarchyRegistrationOptions(TextDocumentRegistrationOptions, CallHierarchyOptions, StaticRegistrationOptions):
    pass


@dataclass
class CallHierarchyPrepareParams(TextDocumentPositionParams, WorkDoneProgressParams):
    pass


@dataclass
class CallHierarchyItem:
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    detail: Optional[str]
    uri: DocumentUri
    range: Range
    selectionRange: Range
    data: Optional[Any]


@dataclass
class CallHierarchyIncomingCallsParams(WorkDoneProgressParams, PartialResultParams):
    item: CallHierarchyItem


@dataclass
class CallHierarchyIncomingCall:
    from_: CallHierarchyItem
    fromRanges: List[Range]


@dataclass
class CallHierarchyOutgoingCallsParams(WorkDoneProgressParams, PartialResultParams):
    item: CallHierarchyItem


@dataclass
class CallHierarchyOutgoingCall:
    to: CallHierarchyItem
    fromRanges: List[Range]


@dataclass
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


@dataclass
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


@dataclass
class TokenFormat(Enum):
    Relative = 'relative'


@dataclass
class SemanticTokensLegend:
    tokenTypes: List[str]
    tokenModifiers: List[str]


@dataclass
class Range_1:
    pass


@dataclass
class Full_1:
    delta: Optional[bool]


@dataclass
class Requests_:
    range: Union[bool, Range_1]
    full: Union[bool, Full_1]


@dataclass
class SemanticTokensClientCapabilities:
    dynamicRegistration: Optional[bool]
    requests: Requests_
    tokenTypes: List[str]
    tokenModifiers: List[str]
    formats: List[TokenFormat]
    overlappingTokenSupport: Optional[bool]
    multilineTokenSupport: Optional[bool]


@dataclass
class Range_1:
    pass


@dataclass
class Full_1:
    delta: Optional[bool]


@dataclass
class SemanticTokensOptions(WorkDoneProgressOptions):
    legend: SemanticTokensLegend
    range: Union[bool, Range_1]
    full: Union[bool, Full_1]


@dataclass
class SemanticTokensRegistrationOptions(TextDocumentRegistrationOptions, SemanticTokensOptions, StaticRegistrationOptions):
    pass


@dataclass
class SemanticTokensParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier


@dataclass
class SemanticTokens:
    resultId: Optional[str]
    data: List[int]


@dataclass
class SemanticTokensPartialResult:
    data: List[int]


@dataclass
class SemanticTokensDeltaParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier
    previousResultId: str


@dataclass
class SemanticTokensDelta:
    resultId: Optional[str]
    edits: List['SemanticTokensEdit']


@dataclass
class SemanticTokensEdit:
    start: int
    deleteCount: int
    data: Optional[List[int]]


@dataclass
class SemanticTokensDeltaPartialResult:
    edits: List[SemanticTokensEdit]


@dataclass
class SemanticTokensRangeParams(WorkDoneProgressParams, PartialResultParams):
    textDocument: TextDocumentIdentifier
    range: Range


@dataclass
class SemanticTokensWorkspaceClientCapabilities:
    refreshSupport: Optional[bool]


@dataclass
class LinkedEditingRangeClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class LinkedEditingRangeOptions(WorkDoneProgressOptions):
    pass


@dataclass
class LinkedEditingRangeRegistrationOptions(TextDocumentRegistrationOptions, LinkedEditingRangeOptions, StaticRegistrationOptions):
    pass


@dataclass
class LinkedEditingRangeParams(TextDocumentPositionParams, WorkDoneProgressParams):
    pass


@dataclass
class LinkedEditingRanges:
    ranges: List[Range]
    wordPattern: Optional[str]


@dataclass
class MonikerClientCapabilities:
    dynamicRegistration: Optional[bool]


@dataclass
class MonikerOptions(WorkDoneProgressOptions):
    pass


@dataclass
class MonikerRegistrationOptions(TextDocumentRegistrationOptions, MonikerOptions):
    pass


@dataclass
class MonikerParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


@dataclass
class UniquenessLevel(Enum):
    document = 'document'
    project = 'project'
    group = 'group'
    scheme = 'scheme'
    global_ = 'global'


@dataclass
class MonikerKind(Enum):
    import_ = 'import'
    export = 'export'
    local = 'local'


@dataclass
class Moniker:
    scheme: str
    identifier: str
    unique: UniquenessLevel
    kind: Optional[MonikerKind]
