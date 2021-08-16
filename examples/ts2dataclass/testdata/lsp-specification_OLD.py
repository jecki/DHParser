
from collections import ChainMap
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Union, List, Tuple, Optional, Dict, Any, Generic, TypeVar


class TSICheckLevel(IntEnum):
    NO_CHECK = 0        # No checks when instantiating a Type Script Interface
    ARG_CHECK = 1       # Check whether the named arguments match the given arguments
    TYPE_CHECK = 2      # In addition, check the types of the given arguments as well


TSI_DYNAMIC_CHECK = TSICheckLevel.TYPE_CHECK


def derive_types(annotation) -> List:
    types = []
    if isinstance(annotation, str):
        annotation = eval(annotation)
    try:
        origin = annotation.__origin__
        if origin in ('Union', 'typing.Union'):
            for t_anno in annotation.__args__:
                types.extend(derive_types(t_anno))
        else:
            _ = annotation.__args__
            types.append(annotation.__origin__)
    except AttributeError:
        types.append(annotation)
    print(types)
    return types


class TSInterface:
    __annotations__ = {}
    arg_types__ = {}

    def derive_arg_types(self):
        cls = self.__class__
        assert not cls.arg_types__
        for param, param_type in cls.__annotations__.items():
            arg_types__[param] =

    def typecheck__(self, level: TSICheckLevel):
        if level <= TSICheckLevel.NO_CHECK:  return
        # level is at least TSIContract.ARG_CHECK
        cls = self.__class__
        fields = ChainMap(cls.__annotations__, *(base.__annotations__ for base in cls.__bases__))
        if fields.keys() != self.__dict__.keys():
            missing = fields.keys() - self.__dict__.keys()
            wrong = self.__dict__.keys() - fields.keys()
            msgs = [f'{cls.__name__} ']
            if missing:
                msgs.append(f'missing required arguments: {", ".join(missing)}!')
            if wrong:
                msgs.append(f'got unexpected parameters: {", ".join(wrong)}!')
            raise TypeError(' '.join(msgs))
        if level >= TSICheckLevel.TYPE_CHECK:
            if not cls.arg_types__:
                cls.arg_types__ = {}

            type_errors = []
            for param, param_type in cls.__annotations__.items():
                if isinstance(param_type, str):

                    if hasattr(param_type,  '__args__'):

                    flag = isinstance(self.__dict__[param], param_type)
                except TypeError as e:
                    print('TypeError', e, type(param_type), param_type.__dict__)
                    assert isinstance(param_type, str), f'{param}, {param_type}'
                    param_type = eval(param_type)
                    cls.__annotations__[param] = param_type
                    flag = isinstance(self.__dict__[param], param_type)
                if not flag:
                    type_errors.append(f'{param} is not of expected type {param_type}')
            if type_errors:
                raise TypeError(f'{cls.__name__}' + ' '.join(type_errors))

    def __init__(self, *args, **kwargs):
        assert not args, "Presently only keyword-arguments are allowed " \
                         "when instantiating a descendant of TSInterface."
        self.__dict__.update(ChainMap(kwargs, getattr(self.__class__, 'optional__', {})))
        self.typecheck__(TSI_DYNAMIC_CHECK)

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            raise ValueError(f'No field named "{key}" in {self.__class__.__name__}')


integer = float


uinteger = float


decimal = float


class Message(TSInterface):
    jsonrpc: str


class RequestMessage(Message, TSInterface):
    id: Union[int, str]
    method: str
    params: Union[List, object, None]


class ResponseMessage(Message, TSInterface):
    id: Union[int, str, None]
    result: Union[str, float, bool, object, None]
    error: Optional['ResponseError']


class ResponseError(TSInterface):
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


class NotificationMessage(Message, TSInterface):
    method: str
    params: Union[List, object, None]


class CancelParams(TSInterface):
    id: Union[int, str]


ProgressToken = Union[int, str]


T = TypeVar('T')


class ProgressParams(Generic[T], TSInterface):
    token: ProgressToken
    value: 'T'


DocumentUri = str


URI = str


class RegularExpressionsClientCapabilities(TSInterface):
    engine: str
    version: Optional[str]


EOL: List[str] = ['\n', '\r\n', '\r']


class Position(TSInterface):
    line: int
    character: int


class Range(TSInterface):
    start: Position
    end: Position


class Location(TSInterface):
    uri: DocumentUri
    range: Range


class LocationLink(TSInterface):
    originSelectionRange: Optional[Range]
    targetUri: DocumentUri
    targetRange: Range
    targetSelectionRange: Range


class Diagnostic(TSInterface):
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


class DiagnosticRelatedInformation(TSInterface):
    location: Location
    message: str


class CodeDescription(TSInterface):
    href: URI


class Command(TSInterface):
    title: str
    command: str
    arguments: Optional[List[Any]]


class TextEdit(TSInterface):
    range: Range
    newText: str


class ChangeAnnotation(TSInterface):
    label: str
    needsConfirmation: Optional[bool]
    description: Optional[str]


ChangeAnnotationIdentifier = str


class AnnotatedTextEdit(TextEdit, TSInterface):
    annotationId: ChangeAnnotationIdentifier


class TextDocumentEdit(TSInterface):
    textDocument: 'OptionalVersionedTextDocumentIdentifier'
    edits: List[Union[TextEdit, AnnotatedTextEdit]]


class CreateFileOptions(TSInterface):
    overwrite: Optional[bool]
    ignoreIfExists: Optional[bool]


class CreateFile(TSInterface):
    kind: str
    uri: DocumentUri
    options: Optional[CreateFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class RenameFileOptions(TSInterface):
    overwrite: Optional[bool]
    ignoreIfExists: Optional[bool]


class RenameFile(TSInterface):
    kind: str
    oldUri: DocumentUri
    newUri: DocumentUri
    options: Optional[RenameFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class DeleteFileOptions(TSInterface):
    recursive: Optional[bool]
    ignoreIfNotExists: Optional[bool]


class DeleteFile(TSInterface):
    kind: str
    uri: DocumentUri
    options: Optional[DeleteFileOptions]
    annotationId: Optional[ChangeAnnotationIdentifier]


class WorkspaceEdit(TSInterface):
    changes: Optional[Dict[DocumentUri, List[TextEdit]]]
    documentChanges: Union[List[TextDocumentEdit], List[Union[TextDocumentEdit, CreateFile, RenameFile, DeleteFile]], None]
    changeAnnotations: Optional[Dict[str, ChangeAnnotation]]


class WorkspaceEditClientCapabilities(TSInterface):
    class ChangeAnnotationSupport_(TSInterface):
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


class TextDocumentIdentifier(TSInterface):
    uri: DocumentUri


class TextDocumentItem(TSInterface):
    uri: DocumentUri
    languageId: str
    version: int
    text: str


class VersionedTextDocumentIdentifier(TextDocumentIdentifier, TSInterface):
    version: int


class OptionalVersionedTextDocumentIdentifier(TextDocumentIdentifier, TSInterface):
    version: Union[int, None]


class TextDocumentPositionParams(TSInterface):
    textDocument: TextDocumentIdentifier
    position: Position


class DocumentFilter(TSInterface):
    language: Optional[str]
    scheme: Optional[str]
    pattern: Optional[str]


DocumentSelector = List[DocumentFilter]


class StaticRegistrationOptions(TSInterface):
    id: Optional[str]


class TextDocumentRegistrationOptions(TSInterface):
    documentSelector: Union[DocumentSelector, None]


class MarkupKind(Enum):
    PlainText = 'plaintext'
    Markdown = 'markdown'


class MarkupContent(TSInterface):
    kind: MarkupKind
    value: str


class MarkdownClientCapabilities(TSInterface):
    parser: str
    version: Optional[str]


class WorkDoneProgressBegin(TSInterface):
    kind: str
    title: str
    cancellable: Optional[bool]
    message: Optional[str]
    percentage: Optional[int]


class WorkDoneProgressReport(TSInterface):
    kind: str
    cancellable: Optional[bool]
    message: Optional[str]
    percentage: Optional[int]


class WorkDoneProgressEnd(TSInterface):
    kind: str
    message: Optional[str]


class WorkDoneProgressParams(TSInterface):
    workDoneToken: Optional[ProgressToken]


class WorkDoneProgressOptions(TSInterface):
    workDoneProgress: Optional[bool]


class PartialResultParams(TSInterface):
    partialResultToken: Optional[ProgressToken]


TraceValue = str


class InitializeParams(WorkDoneProgressParams, TSInterface):
    class ClientInfo_(TSInterface):
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


class TextDocumentClientCapabilities(TSInterface):
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


class ClientCapabilities(TSInterface):
    class Workspace_(TSInterface):
        class FileOperations_(TSInterface):
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
    class Window_(TSInterface):
        workDoneProgress: Optional[bool]
        showMessage: Optional['ShowMessageRequestClientCapabilities']
        showDocument: Optional['ShowDocumentClientCapabilities']
    class General_(TSInterface):
        regularExpressions: Optional[RegularExpressionsClientCapabilities]
        markdown: Optional[MarkdownClientCapabilities]
    workspace: Optional[Workspace_]
    textDocument: Optional[TextDocumentClientCapabilities]
    window: Optional[Window_]
    general: Optional[General_]
    experimental: Optional[Any]


class InitializeResult(TSInterface):
    class ServerInfo_(TSInterface):
        name: str
        version: Optional[str]
    capabilities: 'ServerCapabilities'
    serverInfo: Optional[ServerInfo_]


class InitializeError(IntEnum):
    unknownProtocolVersion = 1


class InitializeError(TSInterface):
    retry: bool


class ServerCapabilities(TSInterface):
    class Workspace_(TSInterface):
        class FileOperations_(TSInterface):
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


class InitializedParams(TSInterface):
    pass


class LogTraceParams(TSInterface):
    message: str
    verbose: Optional[str]


class SetTraceParams(TSInterface):
    value: TraceValue


class ShowMessageParams(TSInterface):
    type: 'MessageType'
    message: str


class MessageType(IntEnum):
    Error = 1
    Warning = 2
    Info = 3
    Log = 4


class ShowMessageRequestClientCapabilities(TSInterface):
    class MessageActionItem_(TSInterface):
        additionalPropertiesSupport: Optional[bool]
    messageActionItem: Optional[MessageActionItem_]


class ShowMessageRequestParams(TSInterface):
    type: MessageType
    message: str
    actions: Optional[List['MessageActionItem']]


class MessageActionItem(TSInterface):
    title: str


class ShowDocumentClientCapabilities(TSInterface):
    support: bool


class ShowDocumentParams(TSInterface):
    uri: URI
    external: Optional[bool]
    takeFocus: Optional[bool]
    selection: Optional[Range]


class ShowDocumentResult(TSInterface):
    success: bool


class LogMessageParams(TSInterface):
    type: MessageType
    message: str


class WorkDoneProgressCreateParams(TSInterface):
    token: ProgressToken


class WorkDoneProgressCancelParams(TSInterface):
    token: ProgressToken


class Registration(TSInterface):
    id: str
    method: str
    registerOptions: Optional[Any]


class RegistrationParams(TSInterface):
    registrations: List[Registration]


class Unregistration(TSInterface):
    id: str
    method: str


class UnregistrationParams(TSInterface):
    unregisterations: List[Unregistration]


class WorkspaceFoldersServerCapabilities(TSInterface):
    supported: Optional[bool]
    changeNotifications: Union[str, bool, None]


class WorkspaceFolder(TSInterface):
    uri: DocumentUri
    name: str


class DidChangeWorkspaceFoldersParams(TSInterface):
    event: 'WorkspaceFoldersChangeEvent'


class WorkspaceFoldersChangeEvent(TSInterface):
    added: List[WorkspaceFolder]
    removed: List[WorkspaceFolder]


class DidChangeConfigurationClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class DidChangeConfigurationParams(TSInterface):
    settings: Any


class ConfigurationParams(TSInterface):
    items: List['ConfigurationItem']


class ConfigurationItem(TSInterface):
    scopeUri: Optional[DocumentUri]
    section: Optional[str]


class DidChangeWatchedFilesClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class DidChangeWatchedFilesRegistrationOptions(TSInterface):
    watchers: List['FileSystemWatcher']


class FileSystemWatcher(TSInterface):
    globPattern: str
    kind: Optional[int]


class WatchKind(IntEnum):
    Create = 1
    Change = 2
    Delete = 4


class DidChangeWatchedFilesParams(TSInterface):
    changes: List['FileEvent']


class FileEvent(TSInterface):
    uri: DocumentUri
    type: int


class FileChangeType(IntEnum):
    Created = 1
    Changed = 2
    Deleted = 3


class WorkspaceSymbolClientCapabilities(TSInterface):
    class SymbolKind_(TSInterface):
        valueSet: Optional[List['SymbolKind']]
    class TagSupport_(TSInterface):
        valueSet: List['SymbolTag']
    dynamicRegistration: Optional[bool]
    symbolKind: Optional[SymbolKind_]
    tagSupport: Optional[TagSupport_]


class WorkspaceSymbolOptions(WorkDoneProgressOptions, TSInterface):
    pass


class WorkspaceSymbolRegistrationOptions(WorkspaceSymbolOptions, TSInterface):
    pass


class WorkspaceSymbolParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    query: str


class ExecuteCommandClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class ExecuteCommandOptions(WorkDoneProgressOptions, TSInterface):
    commands: List[str]


class ExecuteCommandRegistrationOptions(ExecuteCommandOptions, TSInterface):
    pass


class ExecuteCommandParams(WorkDoneProgressParams, TSInterface):
    command: str
    arguments: Optional[List[Any]]


class ApplyWorkspaceEditParams(TSInterface):
    label: Optional[str]
    edit: WorkspaceEdit


class ApplyWorkspaceEditResponse(TSInterface):
    applied: bool
    failureReason: Optional[str]
    failedChange: Optional[int]


class FileOperationRegistrationOptions(TSInterface):
    filters: List['FileOperationFilter']


class FileOperationPatternKind(Enum):
    file = 'file'
    folder = 'folder'


class FileOperationPatternOptions(TSInterface):
    ignoreCase: Optional[bool]


class FileOperationPattern(TSInterface):
    glob: str
    matches: Optional[FileOperationPatternKind]
    options: Optional[FileOperationPatternOptions]


class FileOperationFilter(TSInterface):
    scheme: Optional[str]
    pattern: FileOperationPattern


class CreateFilesParams(TSInterface):
    files: List['FileCreate']


class FileCreate(TSInterface):
    uri: str


class RenameFilesParams(TSInterface):
    files: List['FileRename']


class FileRename(TSInterface):
    oldUri: str
    newUri: str


class DeleteFilesParams(TSInterface):
    files: List['FileDelete']


class FileDelete(TSInterface):
    uri: str


class TextDocumentSyncKind(IntEnum):
    None_ = 0
    Full = 1
    Incremental = 2


class TextDocumentSyncOptions(TSInterface):
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]


class DidOpenTextDocumentParams(TSInterface):
    textDocument: TextDocumentItem


class TextDocumentChangeRegistrationOptions(TextDocumentRegistrationOptions, TSInterface):
    syncKind: TextDocumentSyncKind


class DidChangeTextDocumentParams(TSInterface):
    textDocument: VersionedTextDocumentIdentifier
    contentChanges: List['TextDocumentContentChangeEvent']


class TextDocumentContentChangeEvent_0(TSInterface):
    range: Range
    rangeLength: Optional[int]
    text: str
class TextDocumentContentChangeEvent_1(TSInterface):
    text: str
TextDocumentContentChangeEvent = Union[TextDocumentContentChangeEvent_0, TextDocumentContentChangeEvent_1]


class WillSaveTextDocumentParams(TSInterface):
    textDocument: TextDocumentIdentifier
    reason: 'TextDocumentSaveReason'


class TextDocumentSaveReason(IntEnum):
    Manual = 1
    AfterDelay = 2
    FocusOut = 3


class SaveOptions(TSInterface):
    includeText: Optional[bool]


class TextDocumentSaveRegistrationOptions(TextDocumentRegistrationOptions, TSInterface):
    includeText: Optional[bool]


class DidSaveTextDocumentParams(TSInterface):
    textDocument: TextDocumentIdentifier
    text: Optional[str]


class DidCloseTextDocumentParams(TSInterface):
    textDocument: TextDocumentIdentifier


class TextDocumentSyncClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    didSave: Optional[bool]


class TextDocumentSyncOptions(TSInterface):
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    save: Union[bool, SaveOptions, None]


class PublishDiagnosticsClientCapabilities(TSInterface):
    class TagSupport_(TSInterface):
        valueSet: List[DiagnosticTag]
    relatedInformation: Optional[bool]
    tagSupport: Optional[TagSupport_]
    versionSupport: Optional[bool]
    codeDescriptionSupport: Optional[bool]
    dataSupport: Optional[bool]


class PublishDiagnosticsParams(TSInterface):
    uri: DocumentUri
    version: Optional[int]
    diagnostics: List[Diagnostic]


class CompletionClientCapabilities(TSInterface):
    class CompletionItem_(TSInterface):
        class TagSupport_(TSInterface):
            valueSet: List['CompletionItemTag']
        class ResolveSupport_(TSInterface):
            properties: List[str]
        class InsertTextModeSupport_(TSInterface):
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
    class CompletionItemKind_(TSInterface):
        valueSet: Optional[List['CompletionItemKind']]
    dynamicRegistration: Optional[bool]
    completionItem: Optional[CompletionItem_]
    completionItemKind: Optional[CompletionItemKind_]
    contextSupport: Optional[bool]


class CompletionOptions(WorkDoneProgressOptions, TSInterface):
    triggerCharacters: Optional[List[str]]
    allCommitCharacters: Optional[List[str]]
    resolveProvider: Optional[bool]


class CompletionRegistrationOptions(TextDocumentRegistrationOptions, CompletionOptions, TSInterface):
    pass


class CompletionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TSInterface):
    context: Optional['CompletionContext']


class CompletionTriggerKind(IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    TriggerForIncompleteCompletions = 3


class CompletionContext(TSInterface):
    triggerKind: CompletionTriggerKind
    triggerCharacter: Optional[str]


class CompletionList(TSInterface):
    isIncomplete: bool
    items: List['CompletionItem']


class InsertTextFormat(IntEnum):
    PlainText = 1
    Snippet = 2


class CompletionItemTag(IntEnum):
    Deprecated = 1


class InsertReplaceEdit(TSInterface):
    newText: str
    insert: Range
    replace: Range


class InsertTextMode(IntEnum):
    asIs = 1
    adjustIndentation = 2


class CompletionItem(TSInterface):
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


class HoverClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    contentFormat: Optional[List[MarkupKind]]


class HoverOptions(WorkDoneProgressOptions, TSInterface):
    pass


class HoverRegistrationOptions(TextDocumentRegistrationOptions, HoverOptions, TSInterface):
    pass


class HoverParams(TextDocumentPositionParams, WorkDoneProgressParams, TSInterface):
    pass


class Hover(TSInterface):
    contents: Union['MarkedString', List['MarkedString'], MarkupContent]
    range: Optional[Range]


class MarkedString_1(TSInterface):
    language: str
    value: str
MarkedString = Union[str, MarkedString_1]


class SignatureHelpClientCapabilities(TSInterface):
    class SignatureInformation_(TSInterface):
        class ParameterInformation_(TSInterface):
            labelOffsetSupport: Optional[bool]
        documentationFormat: Optional[List[MarkupKind]]
        parameterInformation: Optional[ParameterInformation_]
        activeParameterSupport: Optional[bool]
    dynamicRegistration: Optional[bool]
    signatureInformation: Optional[SignatureInformation_]
    contextSupport: Optional[bool]


class SignatureHelpOptions(WorkDoneProgressOptions, TSInterface):
    triggerCharacters: Optional[List[str]]
    retriggerCharacters: Optional[List[str]]


class SignatureHelpRegistrationOptions(TextDocumentRegistrationOptions, SignatureHelpOptions, TSInterface):
    pass


class SignatureHelpParams(TextDocumentPositionParams, WorkDoneProgressParams, TSInterface):
    context: Optional['SignatureHelpContext']


class SignatureHelpTriggerKind(IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    ContentChange = 3


class SignatureHelpContext(TSInterface):
    triggerKind: SignatureHelpTriggerKind
    triggerCharacter: Optional[str]
    isRetrigger: bool
    activeSignatureHelp: Optional['SignatureHelp']


class SignatureHelp(TSInterface):
    signatures: List['SignatureInformation']
    activeSignature: Optional[int]
    activeParameter: Optional[int]


class SignatureInformation(TSInterface):
    label: str
    documentation: Union[str, MarkupContent, None]
    parameters: Optional[List['ParameterInformation']]
    activeParameter: Optional[int]


class ParameterInformation(TSInterface):
    label: Union[str, Tuple[int, int]]
    documentation: Union[str, MarkupContent, None]


class DeclarationClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class DeclarationOptions(WorkDoneProgressOptions, TSInterface):
    pass


class DeclarationRegistrationOptions(DeclarationOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TSInterface):
    pass


class DeclarationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TSInterface):
    pass


class DefinitionClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class DefinitionOptions(WorkDoneProgressOptions, TSInterface):
    pass


class DefinitionRegistrationOptions(TextDocumentRegistrationOptions, DefinitionOptions, TSInterface):
    pass


class DefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TSInterface):
    pass


class TypeDefinitionClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class TypeDefinitionOptions(WorkDoneProgressOptions, TSInterface):
    pass


class TypeDefinitionRegistrationOptions(TextDocumentRegistrationOptions, TypeDefinitionOptions, StaticRegistrationOptions, TSInterface):
    pass


class TypeDefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TSInterface):
    pass


class ImplementationClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    linkSupport: Optional[bool]


class ImplementationOptions(WorkDoneProgressOptions, TSInterface):
    pass


class ImplementationRegistrationOptions(TextDocumentRegistrationOptions, ImplementationOptions, StaticRegistrationOptions, TSInterface):
    pass


class ImplementationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TSInterface):
    pass


class ReferenceClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class ReferenceOptions(WorkDoneProgressOptions, TSInterface):
    pass


class ReferenceRegistrationOptions(TextDocumentRegistrationOptions, ReferenceOptions, TSInterface):
    pass


class ReferenceParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TSInterface):
    context: 'ReferenceContext'


class ReferenceContext(TSInterface):
    includeDeclaration: bool


class DocumentHighlightClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class DocumentHighlightOptions(WorkDoneProgressOptions, TSInterface):
    pass


class DocumentHighlightRegistrationOptions(TextDocumentRegistrationOptions, DocumentHighlightOptions, TSInterface):
    pass


class DocumentHighlightParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TSInterface):
    pass


class DocumentHighlight(TSInterface):
    range: Range
    kind: Optional['DocumentHighlightKind']


class DocumentHighlightKind(IntEnum):
    Text = 1
    Read = 2
    Write = 3


class DocumentSymbolClientCapabilities(TSInterface):
    class SymbolKind_(TSInterface):
        valueSet: Optional[List['SymbolKind']]
    class TagSupport_(TSInterface):
        valueSet: List['SymbolTag']
    dynamicRegistration: Optional[bool]
    symbolKind: Optional[SymbolKind_]
    hierarchicalDocumentSymbolSupport: Optional[bool]
    tagSupport: Optional[TagSupport_]
    labelSupport: Optional[bool]


class DocumentSymbolOptions(WorkDoneProgressOptions, TSInterface):
    label: Optional[str]


class DocumentSymbolRegistrationOptions(TextDocumentRegistrationOptions, DocumentSymbolOptions, TSInterface):
    pass


class DocumentSymbolParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
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


class DocumentSymbol(TSInterface):
    name: str
    detail: Optional[str]
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    deprecated: Optional[bool]
    range: Range
    selectionRange: Range
    children: Optional[List['DocumentSymbol']]


class SymbolInformation(TSInterface):
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    deprecated: Optional[bool]
    location: Location
    containerName: Optional[str]


class CodeActionClientCapabilities(TSInterface):
    class CodeActionLiteralSupport_(TSInterface):
        class CodeActionKind_(TSInterface):
            valueSet: List['CodeActionKind']
        codeActionKind: CodeActionKind_
    class ResolveSupport_(TSInterface):
        properties: List[str]
    dynamicRegistration: Optional[bool]
    codeActionLiteralSupport: Optional[CodeActionLiteralSupport_]
    isPreferredSupport: Optional[bool]
    disabledSupport: Optional[bool]
    dataSupport: Optional[bool]
    resolveSupport: Optional[ResolveSupport_]
    honorsChangeAnnotations: Optional[bool]


class CodeActionOptions(WorkDoneProgressOptions, TSInterface):
    codeActionKinds: Optional[List['CodeActionKind']]
    resolveProvider: Optional[bool]


class CodeActionRegistrationOptions(TextDocumentRegistrationOptions, CodeActionOptions, TSInterface):
    pass


class CodeActionParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
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


class CodeActionContext(TSInterface):
    diagnostics: List[Diagnostic]
    only: Optional[List[CodeActionKind]]


class CodeAction(TSInterface):
    class Disabled_(TSInterface):
        reason: str
    title: str
    kind: Optional[CodeActionKind]
    diagnostics: Optional[List[Diagnostic]]
    isPreferred: Optional[bool]
    disabled: Optional[Disabled_]
    edit: Optional[WorkspaceEdit]
    command: Optional[Command]
    data: Optional[Any]


class CodeLensClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class CodeLensOptions(WorkDoneProgressOptions, TSInterface):
    resolveProvider: Optional[bool]


class CodeLensRegistrationOptions(TextDocumentRegistrationOptions, CodeLensOptions, TSInterface):
    pass


class CodeLensParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier


class CodeLens(TSInterface):
    range: Range
    command: Optional[Command]
    data: Optional[Any]


class CodeLensWorkspaceClientCapabilities(TSInterface):
    refreshSupport: Optional[bool]


class DocumentLinkClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    tooltipSupport: Optional[bool]


class DocumentLinkOptions(WorkDoneProgressOptions, TSInterface):
    resolveProvider: Optional[bool]


class DocumentLinkRegistrationOptions(TextDocumentRegistrationOptions, DocumentLinkOptions, TSInterface):
    pass


class DocumentLinkParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier


class DocumentLink(TSInterface):
    range: Range
    target: Optional[DocumentUri]
    tooltip: Optional[str]
    data: Optional[Any]


class DocumentColorClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class DocumentColorOptions(WorkDoneProgressOptions, TSInterface):
    pass


class DocumentColorRegistrationOptions(TextDocumentRegistrationOptions, StaticRegistrationOptions, DocumentColorOptions, TSInterface):
    pass


class DocumentColorParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier


class ColorInformation(TSInterface):
    range: Range
    color: 'Color'


class Color(TSInterface):
    red: float
    green: float
    blue: float
    alpha: float


class ColorPresentationParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier
    color: Color
    range: Range


class ColorPresentation(TSInterface):
    label: str
    textEdit: Optional[TextEdit]
    additionalTextEdits: Optional[List[TextEdit]]


class DocumentFormattingClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class DocumentFormattingOptions(WorkDoneProgressOptions, TSInterface):
    pass


class DocumentFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentFormattingOptions, TSInterface):
    pass


class DocumentFormattingParams(WorkDoneProgressParams, TSInterface):
    textDocument: TextDocumentIdentifier
    options: 'FormattingOptions'


class FormattingOptions(TSInterface):
    tabSize: int
    insertSpaces: bool
    trimTrailingWhitespace: Optional[bool]
    insertFinalNewline: Optional[bool]
    trimFinalNewlines: Optional[bool]


class DocumentRangeFormattingClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class DocumentRangeFormattingOptions(WorkDoneProgressOptions, TSInterface):
    pass


class DocumentRangeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentRangeFormattingOptions, TSInterface):
    pass


class DocumentRangeFormattingParams(WorkDoneProgressParams, TSInterface):
    textDocument: TextDocumentIdentifier
    range: Range
    options: FormattingOptions


class DocumentOnTypeFormattingClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class DocumentOnTypeFormattingOptions(TSInterface):
    firstTriggerCharacter: str
    moreTriggerCharacter: Optional[List[str]]


class DocumentOnTypeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentOnTypeFormattingOptions, TSInterface):
    pass


class DocumentOnTypeFormattingParams(TextDocumentPositionParams, TSInterface):
    ch: str
    options: FormattingOptions


class PrepareSupportDefaultBehavior(IntEnum):
    Identifier = 1


class RenameClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    prepareSupport: Optional[bool]
    prepareSupportDefaultBehavior: Optional[PrepareSupportDefaultBehavior]
    honorsChangeAnnotations: Optional[bool]


class RenameOptions(WorkDoneProgressOptions, TSInterface):
    prepareProvider: Optional[bool]


class RenameRegistrationOptions(TextDocumentRegistrationOptions, RenameOptions, TSInterface):
    pass


class RenameParams(TextDocumentPositionParams, WorkDoneProgressParams, TSInterface):
    newName: str


class PrepareRenameParams(TextDocumentPositionParams, TSInterface):
    pass


class FoldingRangeClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]
    rangeLimit: Optional[int]
    lineFoldingOnly: Optional[bool]


class FoldingRangeOptions(WorkDoneProgressOptions, TSInterface):
    pass


class FoldingRangeRegistrationOptions(TextDocumentRegistrationOptions, FoldingRangeOptions, StaticRegistrationOptions, TSInterface):
    pass


class FoldingRangeParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier


class FoldingRangeKind(Enum):
    Comment = 'comment'
    Imports = 'imports'
    Region = 'region'


class FoldingRange(TSInterface):
    startLine: int
    startCharacter: Optional[int]
    endLine: int
    endCharacter: Optional[int]
    kind: Optional[str]


class SelectionRangeClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class SelectionRangeOptions(WorkDoneProgressOptions, TSInterface):
    pass


class SelectionRangeRegistrationOptions(SelectionRangeOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions, TSInterface):
    pass


class SelectionRangeParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier
    positions: List[Position]


class SelectionRange(TSInterface):
    range: Range
    parent: Optional['SelectionRange']


class CallHierarchyClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class CallHierarchyOptions(WorkDoneProgressOptions, TSInterface):
    pass


class CallHierarchyRegistrationOptions(TextDocumentRegistrationOptions, CallHierarchyOptions, StaticRegistrationOptions, TSInterface):
    pass


class CallHierarchyPrepareParams(TextDocumentPositionParams, WorkDoneProgressParams, TSInterface):
    pass


class CallHierarchyItem(TSInterface):
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]]
    detail: Optional[str]
    uri: DocumentUri
    range: Range
    selectionRange: Range
    data: Optional[Any]


class CallHierarchyIncomingCallsParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    item: CallHierarchyItem


class CallHierarchyIncomingCall(TSInterface):
    from_: CallHierarchyItem
    fromRanges: List[Range]


class CallHierarchyOutgoingCallsParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    item: CallHierarchyItem


class CallHierarchyOutgoingCall(TSInterface):
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


class SemanticTokensLegend(TSInterface):
    tokenTypes: List[str]
    tokenModifiers: List[str]


class SemanticTokensClientCapabilities(TSInterface):
    class Requests_(TSInterface):
        class Range_1(TSInterface):
            pass
        class Full_1(TSInterface):
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


class SemanticTokensOptions(WorkDoneProgressOptions, TSInterface):
    class Range_1(TSInterface):
        pass
    class Full_1(TSInterface):
        delta: Optional[bool]
    legend: SemanticTokensLegend
    range: Union[bool, Range_1, None]
    full: Union[bool, Full_1, None]


class SemanticTokensRegistrationOptions(TextDocumentRegistrationOptions, SemanticTokensOptions, StaticRegistrationOptions, TSInterface):
    pass


class SemanticTokensParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier


class SemanticTokens(TSInterface):
    resultId: Optional[str]
    data: List[int]


class SemanticTokensPartialResult(TSInterface):
    data: List[int]


class SemanticTokensDeltaParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier
    previousResultId: str


class SemanticTokensDelta(TSInterface):
    resultId: Optional[str]
    edits: List['SemanticTokensEdit']


class SemanticTokensEdit(TSInterface):
    start: int
    deleteCount: int
    data: Optional[List[int]]


class SemanticTokensDeltaPartialResult(TSInterface):
    edits: List[SemanticTokensEdit]


class SemanticTokensRangeParams(WorkDoneProgressParams, PartialResultParams, TSInterface):
    textDocument: TextDocumentIdentifier
    range: Range


class SemanticTokensWorkspaceClientCapabilities(TSInterface):
    refreshSupport: Optional[bool]


class LinkedEditingRangeClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class LinkedEditingRangeOptions(WorkDoneProgressOptions, TSInterface):
    pass


class LinkedEditingRangeRegistrationOptions(TextDocumentRegistrationOptions, LinkedEditingRangeOptions, StaticRegistrationOptions, TSInterface):
    pass


class LinkedEditingRangeParams(TextDocumentPositionParams, WorkDoneProgressParams, TSInterface):
    pass


class LinkedEditingRanges(TSInterface):
    ranges: List[Range]
    wordPattern: Optional[str]


class MonikerClientCapabilities(TSInterface):
    dynamicRegistration: Optional[bool]


class MonikerOptions(WorkDoneProgressOptions, TSInterface):
    pass


class MonikerRegistrationOptions(TextDocumentRegistrationOptions, MonikerOptions, TSInterface):
    pass


class MonikerParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams, TSInterface):
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


class Moniker(TSInterface):
    scheme: str
    identifier: str
    unique: UniquenessLevel
    kind: Optional[MonikerKind]


ResponseMessage.references__ = {
    'error': [ResponseError]
}
ProgressParams.references__ = {
    'token': [ProgressToken],
    'value': [T]
}
Range.references__ = {
    'start': [Position],
    'end': [Position]
}
Location.references__ = {
    'uri': [DocumentUri],
    'range': [Range]
}
LocationLink.references__ = {
    'originSelectionRange': [Range],
    'targetUri': [DocumentUri],
    'targetRange': [Range],
    'targetSelectionRange': [Range]
}
Diagnostic.references__ = {
    'range': [Range],
    'severity': [DiagnosticSeverity],
    'codeDescription': [CodeDescription]
}
DiagnosticRelatedInformation.references__ = {
    'location': [Location]
}
CodeDescription.references__ = {
    'href': [URI]
}
TextEdit.references__ = {
    'range': [Range]
}
AnnotatedTextEdit.references__ = {
    'annotationId': [ChangeAnnotationIdentifier]
}
TextDocumentEdit.references__ = {
    'textDocument': [OptionalVersionedTextDocumentIdentifier],
    'edits': [AnnotatedTextEdit]
}
CreateFile.references__ = {
    'uri': [DocumentUri],
    'options': [CreateFileOptions],
    'annotationId': [ChangeAnnotationIdentifier]
}
RenameFile.references__ = {
    'oldUri': [DocumentUri],
    'newUri': [DocumentUri],
    'options': [RenameFileOptions],
    'annotationId': [ChangeAnnotationIdentifier]
}
DeleteFile.references__ = {
    'uri': [DocumentUri],
    'options': [DeleteFileOptions],
    'annotationId': [ChangeAnnotationIdentifier]
}
WorkspaceEdit.references__ = {
    'changes': [DocumentUri],
    'documentChanges': [DeleteFile],
    'changeAnnotations': [ChangeAnnotation]
}
WorkspaceEditClientCapabilities.references__ = {
    'failureHandling': [FailureHandlingKind],
    'changeAnnotationSupport': [WorkspaceEditClientCapabilities.ChangeAnnotationSupport_]
}
TextDocumentIdentifier.references__ = {
    'uri': [DocumentUri]
}
TextDocumentItem.references__ = {
    'uri': [DocumentUri]
}
TextDocumentPositionParams.references__ = {
    'textDocument': [TextDocumentIdentifier],
    'position': [Position]
}
TextDocumentRegistrationOptions.references__ = {
    'documentSelector': [DocumentSelector]
}
MarkupContent.references__ = {
    'kind': [MarkupKind]
}
WorkDoneProgressParams.references__ = {
    'workDoneToken': [ProgressToken]
}
PartialResultParams.references__ = {
    'partialResultToken': [ProgressToken]
}
InitializeParams.references__ = {
    'clientInfo': [InitializeParams.ClientInfo_],
    'rootUri': [DocumentUri],
    'capabilities': [ClientCapabilities],
    'trace': [TraceValue]
}
TextDocumentClientCapabilities.references__ = {
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
ClientCapabilities.Workspace_.references__ = {
    'workspaceEdit': [WorkspaceEditClientCapabilities],
    'didChangeConfiguration': [DidChangeConfigurationClientCapabilities],
    'didChangeWatchedFiles': [DidChangeWatchedFilesClientCapabilities],
    'symbol': [WorkspaceSymbolClientCapabilities],
    'executeCommand': [ExecuteCommandClientCapabilities],
    'semanticTokens': [SemanticTokensWorkspaceClientCapabilities],
    'codeLens': [CodeLensWorkspaceClientCapabilities],
    'fileOperations': [ClientCapabilities.Workspace_.FileOperations_]
}
ClientCapabilities.references__ = {
    'workspace': [ClientCapabilities.Workspace_],
    'textDocument': [TextDocumentClientCapabilities],
    'window': [ClientCapabilities.Window_],
    'general': [ClientCapabilities.General_]
}
ClientCapabilities.Window_.references__ = {
    'showMessage': [ShowMessageRequestClientCapabilities],
    'showDocument': [ShowDocumentClientCapabilities]
}
ClientCapabilities.General_.references__ = {
    'regularExpressions': [RegularExpressionsClientCapabilities],
    'markdown': [MarkdownClientCapabilities]
}
InitializeResult.references__ = {
    'capabilities': [ServerCapabilities],
    'serverInfo': [InitializeResult.ServerInfo_]
}
ServerCapabilities.references__ = {
    'textDocumentSync': [TextDocumentSyncKind],
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
ServerCapabilities.Workspace_.references__ = {
    'workspaceFolders': [WorkspaceFoldersServerCapabilities],
    'fileOperations': [ServerCapabilities.Workspace_.FileOperations_]
}
ServerCapabilities.Workspace_.FileOperations_.references__ = {
    'didCreate': [FileOperationRegistrationOptions],
    'willCreate': [FileOperationRegistrationOptions],
    'didRename': [FileOperationRegistrationOptions],
    'willRename': [FileOperationRegistrationOptions],
    'didDelete': [FileOperationRegistrationOptions],
    'willDelete': [FileOperationRegistrationOptions]
}
SetTraceParams.references__ = {
    'value': [TraceValue]
}
ShowMessageParams.references__ = {
    'type': [MessageType]
}
ShowMessageRequestClientCapabilities.references__ = {
    'messageActionItem': [ShowMessageRequestClientCapabilities.MessageActionItem_]
}
ShowMessageRequestParams.references__ = {
    'type': [MessageType]
}
ShowDocumentParams.references__ = {
    'uri': [URI],
    'selection': [Range]
}
LogMessageParams.references__ = {
    'type': [MessageType]
}
WorkDoneProgressCreateParams.references__ = {
    'token': [ProgressToken]
}
WorkDoneProgressCancelParams.references__ = {
    'token': [ProgressToken]
}
WorkspaceFolder.references__ = {
    'uri': [DocumentUri]
}
DidChangeWorkspaceFoldersParams.references__ = {
    'event': [WorkspaceFoldersChangeEvent]
}
ConfigurationItem.references__ = {
    'scopeUri': [DocumentUri]
}
FileEvent.references__ = {
    'uri': [DocumentUri]
}
WorkspaceSymbolClientCapabilities.references__ = {
    'symbolKind': [WorkspaceSymbolClientCapabilities.SymbolKind_],
    'tagSupport': [WorkspaceSymbolClientCapabilities.TagSupport_]
}
ApplyWorkspaceEditParams.references__ = {
    'edit': [WorkspaceEdit]
}
FileOperationPattern.references__ = {
    'matches': [FileOperationPatternKind],
    'options': [FileOperationPatternOptions]
}
FileOperationFilter.references__ = {
    'pattern': [FileOperationPattern]
}
TextDocumentSyncOptions.references__ = {
    'change': [TextDocumentSyncKind],
    'save': [SaveOptions]
}
DidOpenTextDocumentParams.references__ = {
    'textDocument': [TextDocumentItem]
}
TextDocumentChangeRegistrationOptions.references__ = {
    'syncKind': [TextDocumentSyncKind]
}
DidChangeTextDocumentParams.references__ = {
    'textDocument': [VersionedTextDocumentIdentifier]
}
TextDocumentContentChangeEvent_0.references__ = {
    'range': [Range]
}
WillSaveTextDocumentParams.references__ = {
    'textDocument': [TextDocumentIdentifier],
    'reason': [TextDocumentSaveReason]
}
DidSaveTextDocumentParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
DidCloseTextDocumentParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
PublishDiagnosticsClientCapabilities.references__ = {
    'tagSupport': [PublishDiagnosticsClientCapabilities.TagSupport_]
}
PublishDiagnosticsParams.references__ = {
    'uri': [DocumentUri]
}
CompletionClientCapabilities.CompletionItem_.references__ = {
    'tagSupport': [CompletionClientCapabilities.CompletionItem_.TagSupport_],
    'resolveSupport': [CompletionClientCapabilities.CompletionItem_.ResolveSupport_],
    'insertTextModeSupport': [CompletionClientCapabilities.CompletionItem_.InsertTextModeSupport_]
}
CompletionClientCapabilities.references__ = {
    'completionItem': [CompletionClientCapabilities.CompletionItem_],
    'completionItemKind': [CompletionClientCapabilities.CompletionItemKind_]
}
CompletionParams.references__ = {
    'context': [CompletionContext]
}
CompletionContext.references__ = {
    'triggerKind': [CompletionTriggerKind]
}
InsertReplaceEdit.references__ = {
    'insert': [Range],
    'replace': [Range]
}
CompletionItem.references__ = {
    'kind': [CompletionItemKind],
    'documentation': [MarkupContent],
    'insertTextFormat': [InsertTextFormat],
    'insertTextMode': [InsertTextMode],
    'textEdit': [InsertReplaceEdit],
    'command': [Command]
}
Hover.references__ = {
    'contents': [MarkupContent],
    'range': [Range]
}
SignatureHelpClientCapabilities.SignatureInformation_.references__ = {
    'parameterInformation': [SignatureHelpClientCapabilities.SignatureInformation_.ParameterInformation_]
}
SignatureHelpClientCapabilities.references__ = {
    'signatureInformation': [SignatureHelpClientCapabilities.SignatureInformation_]
}
SignatureHelpParams.references__ = {
    'context': [SignatureHelpContext]
}
SignatureHelpContext.references__ = {
    'triggerKind': [SignatureHelpTriggerKind],
    'activeSignatureHelp': [SignatureHelp]
}
SignatureInformation.references__ = {
    'documentation': [MarkupContent]
}
ParameterInformation.references__ = {
    'documentation': [MarkupContent]
}
ReferenceParams.references__ = {
    'context': [ReferenceContext]
}
DocumentHighlight.references__ = {
    'range': [Range],
    'kind': [DocumentHighlightKind]
}
DocumentSymbolClientCapabilities.references__ = {
    'symbolKind': [DocumentSymbolClientCapabilities.SymbolKind_],
    'tagSupport': [DocumentSymbolClientCapabilities.TagSupport_]
}
DocumentSymbolParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
DocumentSymbol.references__ = {
    'kind': [SymbolKind],
    'range': [Range],
    'selectionRange': [Range]
}
SymbolInformation.references__ = {
    'kind': [SymbolKind],
    'location': [Location]
}
CodeActionClientCapabilities.CodeActionLiteralSupport_.references__ = {
    'codeActionKind': [CodeActionClientCapabilities.CodeActionLiteralSupport_.CodeActionKind_]
}
CodeActionClientCapabilities.references__ = {
    'codeActionLiteralSupport': [CodeActionClientCapabilities.CodeActionLiteralSupport_],
    'resolveSupport': [CodeActionClientCapabilities.ResolveSupport_]
}
CodeActionParams.references__ = {
    'textDocument': [TextDocumentIdentifier],
    'range': [Range],
    'context': [CodeActionContext]
}
CodeAction.references__ = {
    'kind': [CodeActionKind],
    'disabled': [CodeAction.Disabled_],
    'edit': [WorkspaceEdit],
    'command': [Command]
}
CodeLensParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
CodeLens.references__ = {
    'range': [Range],
    'command': [Command]
}
DocumentLinkParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
DocumentLink.references__ = {
    'range': [Range],
    'target': [DocumentUri]
}
DocumentColorParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
ColorInformation.references__ = {
    'range': [Range],
    'color': [Color]
}
ColorPresentationParams.references__ = {
    'textDocument': [TextDocumentIdentifier],
    'color': [Color],
    'range': [Range]
}
ColorPresentation.references__ = {
    'textEdit': [TextEdit]
}
DocumentFormattingParams.references__ = {
    'textDocument': [TextDocumentIdentifier],
    'options': [FormattingOptions]
}
DocumentRangeFormattingParams.references__ = {
    'textDocument': [TextDocumentIdentifier],
    'range': [Range],
    'options': [FormattingOptions]
}
DocumentOnTypeFormattingParams.references__ = {
    'options': [FormattingOptions]
}
RenameClientCapabilities.references__ = {
    'prepareSupportDefaultBehavior': [PrepareSupportDefaultBehavior]
}
FoldingRangeParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
SelectionRangeParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
SelectionRange.references__ = {
    'range': [Range],
    'parent': [SelectionRange]
}
CallHierarchyItem.references__ = {
    'kind': [SymbolKind],
    'uri': [DocumentUri],
    'range': [Range],
    'selectionRange': [Range]
}
CallHierarchyIncomingCallsParams.references__ = {
    'item': [CallHierarchyItem]
}
CallHierarchyIncomingCall.references__ = {
    'from_': [CallHierarchyItem]
}
CallHierarchyOutgoingCallsParams.references__ = {
    'item': [CallHierarchyItem]
}
CallHierarchyOutgoingCall.references__ = {
    'to': [CallHierarchyItem]
}
SemanticTokensClientCapabilities.Requests_.references__ = {
    'range': [SemanticTokensClientCapabilities.Requests_.Range_1],
    'full': [SemanticTokensClientCapabilities.Requests_.Full_1]
}
SemanticTokensClientCapabilities.references__ = {
    'requests': [SemanticTokensClientCapabilities.Requests_]
}
SemanticTokensOptions.references__ = {
    'legend': [SemanticTokensLegend],
    'range': [SemanticTokensOptions.Range_1],
    'full': [SemanticTokensOptions.Full_1]
}
SemanticTokensParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
SemanticTokensDeltaParams.references__ = {
    'textDocument': [TextDocumentIdentifier]
}
SemanticTokensRangeParams.references__ = {
    'textDocument': [TextDocumentIdentifier],
    'range': [Range]
}
Moniker.references__ = {
    'unique': [UniquenessLevel],
    'kind': [MonikerKind]
}


RequestMessage.optional__ = {
    'params': None
}
ResponseMessage.optional__ = {
    'result': None,
    'error': None
}
ResponseError.optional__ = {
    'data': None
}
NotificationMessage.optional__ = {
    'params': None
}
RegularExpressionsClientCapabilities.optional__ = {
    'version': None
}
LocationLink.optional__ = {
    'originSelectionRange': None
}
Diagnostic.optional__ = {
    'severity': None,
    'code': None,
    'codeDescription': None,
    'source': None,
    'tags': None,
    'relatedInformation': None,
    'data': None
}
Command.optional__ = {
    'arguments': None
}
ChangeAnnotation.optional__ = {
    'needsConfirmation': None,
    'description': None
}
CreateFileOptions.optional__ = {
    'overwrite': None,
    'ignoreIfExists': None
}
CreateFile.optional__ = {
    'options': None,
    'annotationId': None
}
RenameFileOptions.optional__ = {
    'overwrite': None,
    'ignoreIfExists': None
}
RenameFile.optional__ = {
    'options': None,
    'annotationId': None
}
DeleteFileOptions.optional__ = {
    'recursive': None,
    'ignoreIfNotExists': None
}
DeleteFile.optional__ = {
    'options': None,
    'annotationId': None
}
WorkspaceEdit.optional__ = {
    'changes': None,
    'documentChanges': None,
    'changeAnnotations': None
}
WorkspaceEditClientCapabilities.optional__ = {
    'documentChanges': None,
    'resourceOperations': None,
    'failureHandling': None,
    'normalizesLineEndings': None,
    'changeAnnotationSupport': None
}
WorkspaceEditClientCapabilities.ChangeAnnotationSupport_.optional__ = {
    'groupsOnLabel': None
}
DocumentFilter.optional__ = {
    'language': None,
    'scheme': None,
    'pattern': None
}
StaticRegistrationOptions.optional__ = {
    'id': None
}
MarkdownClientCapabilities.optional__ = {
    'version': None
}
WorkDoneProgressBegin.optional__ = {
    'cancellable': None,
    'message': None,
    'percentage': None
}
WorkDoneProgressReport.optional__ = {
    'cancellable': None,
    'message': None,
    'percentage': None
}
WorkDoneProgressEnd.optional__ = {
    'message': None
}
WorkDoneProgressParams.optional__ = {
    'workDoneToken': None
}
WorkDoneProgressOptions.optional__ = {
    'workDoneProgress': None
}
PartialResultParams.optional__ = {
    'partialResultToken': None
}
InitializeParams.ClientInfo_.optional__ = {
    'version': None
}
InitializeParams.optional__ = {
    'clientInfo': None,
    'locale': None,
    'rootPath': None,
    'initializationOptions': None,
    'trace': None,
    'workspaceFolders': None
}
TextDocumentClientCapabilities.optional__ = {
    'synchronization': None,
    'completion': None,
    'hover': None,
    'signatureHelp': None,
    'declaration': None,
    'definition': None,
    'typeDefinition': None,
    'implementation': None,
    'references': None,
    'documentHighlight': None,
    'documentSymbol': None,
    'codeAction': None,
    'codeLens': None,
    'documentLink': None,
    'colorProvider': None,
    'formatting': None,
    'rangeFormatting': None,
    'onTypeFormatting': None,
    'rename': None,
    'publishDiagnostics': None,
    'foldingRange': None,
    'selectionRange': None,
    'linkedEditingRange': None,
    'callHierarchy': None,
    'semanticTokens': None,
    'moniker': None
}
ClientCapabilities.Workspace_.optional__ = {
    'applyEdit': None,
    'workspaceEdit': None,
    'didChangeConfiguration': None,
    'didChangeWatchedFiles': None,
    'symbol': None,
    'executeCommand': None,
    'workspaceFolders': None,
    'configuration': None,
    'semanticTokens': None,
    'codeLens': None,
    'fileOperations': None
}
ClientCapabilities.Workspace_.FileOperations_.optional__ = {
    'dynamicRegistration': None,
    'didCreate': None,
    'willCreate': None,
    'didRename': None,
    'willRename': None,
    'didDelete': None,
    'willDelete': None
}
ClientCapabilities.optional__ = {
    'workspace': None,
    'textDocument': None,
    'window': None,
    'general': None,
    'experimental': None
}
ClientCapabilities.Window_.optional__ = {
    'workDoneProgress': None,
    'showMessage': None,
    'showDocument': None
}
ClientCapabilities.General_.optional__ = {
    'regularExpressions': None,
    'markdown': None
}
InitializeResult.ServerInfo_.optional__ = {
    'version': None
}
InitializeResult.optional__ = {
    'serverInfo': None
}
ServerCapabilities.optional__ = {
    'textDocumentSync': None,
    'completionProvider': None,
    'hoverProvider': None,
    'signatureHelpProvider': None,
    'declarationProvider': None,
    'definitionProvider': None,
    'typeDefinitionProvider': None,
    'implementationProvider': None,
    'referencesProvider': None,
    'documentHighlightProvider': None,
    'documentSymbolProvider': None,
    'codeActionProvider': None,
    'codeLensProvider': None,
    'documentLinkProvider': None,
    'colorProvider': None,
    'documentFormattingProvider': None,
    'documentRangeFormattingProvider': None,
    'documentOnTypeFormattingProvider': None,
    'renameProvider': None,
    'foldingRangeProvider': None,
    'executeCommandProvider': None,
    'selectionRangeProvider': None,
    'linkedEditingRangeProvider': None,
    'callHierarchyProvider': None,
    'semanticTokensProvider': None,
    'monikerProvider': None,
    'workspaceSymbolProvider': None,
    'workspace': None,
    'experimental': None
}
ServerCapabilities.Workspace_.optional__ = {
    'workspaceFolders': None,
    'fileOperations': None
}
ServerCapabilities.Workspace_.FileOperations_.optional__ = {
    'didCreate': None,
    'willCreate': None,
    'didRename': None,
    'willRename': None,
    'didDelete': None,
    'willDelete': None
}
LogTraceParams.optional__ = {
    'verbose': None
}
ShowMessageRequestClientCapabilities.MessageActionItem_.optional__ = {
    'additionalPropertiesSupport': None
}
ShowMessageRequestClientCapabilities.optional__ = {
    'messageActionItem': None
}
ShowMessageRequestParams.optional__ = {
    'actions': None
}
ShowDocumentParams.optional__ = {
    'external': None,
    'takeFocus': None,
    'selection': None
}
Registration.optional__ = {
    'registerOptions': None
}
WorkspaceFoldersServerCapabilities.optional__ = {
    'supported': None,
    'changeNotifications': None
}
DidChangeConfigurationClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
ConfigurationItem.optional__ = {
    'scopeUri': None,
    'section': None
}
DidChangeWatchedFilesClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
FileSystemWatcher.optional__ = {
    'kind': None
}
WorkspaceSymbolClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'symbolKind': None,
    'tagSupport': None
}
WorkspaceSymbolClientCapabilities.SymbolKind_.optional__ = {
    'valueSet': None
}
ExecuteCommandClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
ExecuteCommandParams.optional__ = {
    'arguments': None
}
ApplyWorkspaceEditParams.optional__ = {
    'label': None
}
ApplyWorkspaceEditResponse.optional__ = {
    'failureReason': None,
    'failedChange': None
}
FileOperationPatternOptions.optional__ = {
    'ignoreCase': None
}
FileOperationPattern.optional__ = {
    'matches': None,
    'options': None
}
FileOperationFilter.optional__ = {
    'scheme': None
}
TextDocumentSyncOptions.optional__ = {
    'openClose': None,
    'change': None,
    'willSave': None,
    'willSaveWaitUntil': None,
    'save': None
}
TextDocumentContentChangeEvent_0.optional__ = {
    'rangeLength': None
}
SaveOptions.optional__ = {
    'includeText': None
}
TextDocumentSaveRegistrationOptions.optional__ = {
    'includeText': None
}
DidSaveTextDocumentParams.optional__ = {
    'text': None
}
TextDocumentSyncClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'willSave': None,
    'willSaveWaitUntil': None,
    'didSave': None
}
PublishDiagnosticsClientCapabilities.optional__ = {
    'relatedInformation': None,
    'tagSupport': None,
    'versionSupport': None,
    'codeDescriptionSupport': None,
    'dataSupport': None
}
PublishDiagnosticsParams.optional__ = {
    'version': None
}
CompletionClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'completionItem': None,
    'completionItemKind': None,
    'contextSupport': None
}
CompletionClientCapabilities.CompletionItem_.optional__ = {
    'snippetSupport': None,
    'commitCharactersSupport': None,
    'documentationFormat': None,
    'deprecatedSupport': None,
    'preselectSupport': None,
    'tagSupport': None,
    'insertReplaceSupport': None,
    'resolveSupport': None,
    'insertTextModeSupport': None
}
CompletionClientCapabilities.CompletionItemKind_.optional__ = {
    'valueSet': None
}
CompletionOptions.optional__ = {
    'triggerCharacters': None,
    'allCommitCharacters': None,
    'resolveProvider': None
}
CompletionParams.optional__ = {
    'context': None
}
CompletionContext.optional__ = {
    'triggerCharacter': None
}
CompletionItem.optional__ = {
    'kind': None,
    'tags': None,
    'detail': None,
    'documentation': None,
    'deprecated': None,
    'preselect': None,
    'sortText': None,
    'filterText': None,
    'insertText': None,
    'insertTextFormat': None,
    'insertTextMode': None,
    'textEdit': None,
    'additionalTextEdits': None,
    'commitCharacters': None,
    'command': None,
    'data': None
}
HoverClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'contentFormat': None
}
Hover.optional__ = {
    'range': None
}
SignatureHelpClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'signatureInformation': None,
    'contextSupport': None
}
SignatureHelpClientCapabilities.SignatureInformation_.optional__ = {
    'documentationFormat': None,
    'parameterInformation': None,
    'activeParameterSupport': None
}
SignatureHelpClientCapabilities.SignatureInformation_.ParameterInformation_.optional__ = {
    'labelOffsetSupport': None
}
SignatureHelpOptions.optional__ = {
    'triggerCharacters': None,
    'retriggerCharacters': None
}
SignatureHelpParams.optional__ = {
    'context': None
}
SignatureHelpContext.optional__ = {
    'triggerCharacter': None,
    'activeSignatureHelp': None
}
SignatureHelp.optional__ = {
    'activeSignature': None,
    'activeParameter': None
}
SignatureInformation.optional__ = {
    'documentation': None,
    'parameters': None,
    'activeParameter': None
}
ParameterInformation.optional__ = {
    'documentation': None
}
DeclarationClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'linkSupport': None
}
DefinitionClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'linkSupport': None
}
TypeDefinitionClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'linkSupport': None
}
ImplementationClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'linkSupport': None
}
ReferenceClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
DocumentHighlightClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
DocumentHighlight.optional__ = {
    'kind': None
}
DocumentSymbolClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'symbolKind': None,
    'hierarchicalDocumentSymbolSupport': None,
    'tagSupport': None,
    'labelSupport': None
}
DocumentSymbolClientCapabilities.SymbolKind_.optional__ = {
    'valueSet': None
}
DocumentSymbolOptions.optional__ = {
    'label': None
}
DocumentSymbol.optional__ = {
    'detail': None,
    'tags': None,
    'deprecated': None,
    'children': None
}
SymbolInformation.optional__ = {
    'tags': None,
    'deprecated': None,
    'containerName': None
}
CodeActionClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'codeActionLiteralSupport': None,
    'isPreferredSupport': None,
    'disabledSupport': None,
    'dataSupport': None,
    'resolveSupport': None,
    'honorsChangeAnnotations': None
}
CodeActionOptions.optional__ = {
    'codeActionKinds': None,
    'resolveProvider': None
}
CodeActionContext.optional__ = {
    'only': None
}
CodeAction.optional__ = {
    'kind': None,
    'diagnostics': None,
    'isPreferred': None,
    'disabled': None,
    'edit': None,
    'command': None,
    'data': None
}
CodeLensClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
CodeLensOptions.optional__ = {
    'resolveProvider': None
}
CodeLens.optional__ = {
    'command': None,
    'data': None
}
CodeLensWorkspaceClientCapabilities.optional__ = {
    'refreshSupport': None
}
DocumentLinkClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'tooltipSupport': None
}
DocumentLinkOptions.optional__ = {
    'resolveProvider': None
}
DocumentLink.optional__ = {
    'target': None,
    'tooltip': None,
    'data': None
}
DocumentColorClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
ColorPresentation.optional__ = {
    'textEdit': None,
    'additionalTextEdits': None
}
DocumentFormattingClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
FormattingOptions.optional__ = {
    'trimTrailingWhitespace': None,
    'insertFinalNewline': None,
    'trimFinalNewlines': None
}
DocumentRangeFormattingClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
DocumentOnTypeFormattingClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
DocumentOnTypeFormattingOptions.optional__ = {
    'moreTriggerCharacter': None
}
RenameClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'prepareSupport': None,
    'prepareSupportDefaultBehavior': None,
    'honorsChangeAnnotations': None
}
RenameOptions.optional__ = {
    'prepareProvider': None
}
FoldingRangeClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'rangeLimit': None,
    'lineFoldingOnly': None
}
FoldingRange.optional__ = {
    'startCharacter': None,
    'endCharacter': None,
    'kind': None
}
SelectionRangeClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
SelectionRange.optional__ = {
    'parent': None
}
CallHierarchyClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
CallHierarchyItem.optional__ = {
    'tags': None,
    'detail': None,
    'data': None
}
SemanticTokensClientCapabilities.optional__ = {
    'dynamicRegistration': None,
    'overlappingTokenSupport': None,
    'multilineTokenSupport': None
}
SemanticTokensClientCapabilities.Requests_.optional__ = {
    'range': None,
    'full': None
}
SemanticTokensClientCapabilities.Requests_.Full_1.optional__ = {
    'delta': None
}
SemanticTokensOptions.optional__ = {
    'range': None,
    'full': None
}
SemanticTokensOptions.Full_1.optional__ = {
    'delta': None
}
SemanticTokens.optional__ = {
    'resultId': None
}
SemanticTokensDelta.optional__ = {
    'resultId': None
}
SemanticTokensEdit.optional__ = {
    'data': None
}
SemanticTokensWorkspaceClientCapabilities.optional__ = {
    'refreshSupport': None
}
LinkedEditingRangeClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
LinkedEditingRanges.optional__ = {
    'wordPattern': None
}
MonikerClientCapabilities.optional__ = {
    'dynamicRegistration': None
}
Moniker.optional__ = {
    'kind': None
}


if __name__ == "__main__":
    msg = Message(jsonrpc="test")
    print(msg.__dict__)
    msg = RequestMessage(jsonrpc="test", id=1, method="gogogo")
    print(msg.__dict__)
    msg = RequestMessage(jsonrpc="test", id="2", method="gogogo", params="[1, 2, 3]")
    print(msg.__dict__)
