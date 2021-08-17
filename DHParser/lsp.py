# lsp.py - Language Server Protocol data structures and support functions
#
# Copyright 20w0  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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


import bisect
import copy
from enum import Enum, IntEnum
import functools
from typing import Union, List, Tuple, Optional, Dict, Any, Generic, TypeVar, \
    Iterator, Iterable, Callable, cast

try:
    from typing import ForwardRef
except ImportError:
    from typing import _ForwardRef  # Python 3.6 compatibility
    ForwardRef = _ForwardRef

from DHParser.server import RPC_Table
from DHParser.toolkit import JSON_Type, JSON_Dict
from dataclasses import dataclass, asdict



#######################################################################
#
# Language-Server-Protocol functions
#
#######################################################################


# general #############################################################

# def get_lsp_methods(cls: Any, prefix: str= 'lsp_') -> List[str]:
#     """Returns the language-server-protocol-method-names from class `cls`.
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
                  prefix: str = 'lsp_') -> RPC_Table:
    """Creates an RPC from a list of functions or from the methods
    of a class that implement the language server protocol.
    The dictionary keys are derived from the function name by replacing an
    underscore _ with a slash / and a single capital S with a $-sign.
    if `prefix` is not the empty string only functions or methods that start
    with `prefix` will be added to the table. The prefix will be removed
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
    a = bisect.bisect_left(long_list, typed, lo, hi)
    b = bisect.bisect_left(long_list, typed[:-1] + chr(ord(typed[-1]) + 1), lo, hi)
    return a, b


# decorator for typed lsp-functions ###################################

class TSICheckLevel(IntEnum):
    NO_CHECK = 0        # No checks when instantiating a Type Script Interface
    ARG_CHECK = 1       # Check whether the named arguments match the given arguments
    TYPE_CHECK = 2      # In addition, check the types of the given arguments as well


TSI_DYNAMIC_CHECK = TSICheckLevel.TYPE_CHECK


def derive_types(annotation) -> Tuple:
    types = []
    if isinstance(annotation, ForwardRef):
        annotation = eval(annotation.__forward_arg__)
    elif isinstance(annotation, str):  # really needed?
        annotation = eval(annotation)
    try:
        origin = annotation.__origin__
        if origin is Union:
            for t_anno in annotation.__args__:
                types.extend(derive_types(t_anno))
        else:
            _ = annotation.__args__
            types.append(annotation.__origin__)
    except AttributeError:
        if annotation is Any:
            types.append(object)
        else:
            types.append(annotation)
    return tuple(types)


def chain_from_bases(cls, chain: str, field: str) -> Dict:
    try:
        return cls.__dict__[chain]
    except KeyError:
        chained = {}
        chained.update(getattr(cls, field, {}))
        for base in cls.__bases__:
            chained.update(getattr(base, field, {}))
        setattr(cls, chain, chained)
        return chained


class TSInterface:
    def derive_arg_types__(self, fields):
        cls = self.__class__
        assert not hasattr(cls, 'arg_types__')
        cls.arg_types__ = {param: derive_types(param_type)
                           for param, param_type in fields.items()}

    def typecheck__(self, level: TSICheckLevel):
        if level <= TSICheckLevel.NO_CHECK:  return
        # level is at least TSIContract.ARG_CHECK
        cls = self.__class__
        fields = cls.fields__
        if fields.keys() != self.__dict__.keys():
            missing = fields.keys() - self.__dict__.keys()
            wrong = self.__dict__.keys() - fields.keys()
            msgs = [f'{cls.__name__} ']
            if missing:
                msgs.append(f'missing required arguments: {", ".join(missing)}!')
            if wrong:
                msgs.append(f'got unexpected parameters: {", ".join(wrong)}!')
            raise TypeError(' '.join(msgs) + f' Received: {self.__dict__}')
        if level >= TSICheckLevel.TYPE_CHECK:
            if not hasattr(cls, 'arg_types__'):
                self.derive_arg_types__(fields)
            type_errors = [f'{arg} is not a {typ}' for arg, typ in self.arg_types__.items()
                           if (not isinstance(self.__dict__[arg], typ)
                               or (typ == [object] and self.__dict__[arg] is None))]
            if type_errors:
                raise TypeError(f'{cls.__name__} got wrong types: ' + ', '.join(type_errors))

    def __init__(self, *args, **kwargs):
        cls = self.__class__
        fields = chain_from_bases(cls, 'fields__', '__annotations__')
        args_dict = {kw: arg for kw, arg in zip(fields.keys(), args)}
        optional_fields = chain_from_bases(cls, 'optional_fields__', 'optional__')
        parameters = {**optional_fields, **kwargs, **args_dict}
        references = chain_from_bases(cls, 'all_refs__', 'references__')
        for ref, types in references.items():
            d = parameters[ref]
            if isinstance(d, (dict, tuple)):
                parameters[ref] = fromjson_obj(d, types)
        self.__dict__.update(parameters)
        self.typecheck__(TSI_DYNAMIC_CHECK)

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            raise ValueError(f'No field named "{key}" in {self.__class__.__name__}')

    def __eq__(self, other):
        return self.__dict__.keys() == other.__dict__.keys() \
            and all(v1 == v2 for v1, v2 in zip(self.__dict__.values(), other.__dict__.values()))

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(f'{k}={repr(v)}' for k, v in self.__dict__.items())})"

def asjson_obj(data: Union[TSInterface, JSON_Type], deepcopy: bool = False) -> JSON_Type:
    if data is None:  return None
    if isinstance(data, TSInterface):
        cls = data.__class__
        references = chain_from_bases(cls, 'all_refs__', 'references__')
        optionals = chain_from_bases(cls, 'optional_fields__', 'optional__')
        if references:
            d = {field: (asjson_obj(value, True) if field in references
                         else (copy.deepcopy(value) if deepcopy else value))
                 for field, value in data.__dict__.items()
                 if value is not None or field not in optionals}
            return d
        return copy.deepcopy(data.__dict__) if deepcopy else data.__dict__
    elif isinstance(data, (list, tuple)):
        if deepcopy or (data and isinstance(data[0], TSInterface)):  # assumes uniform list
            return [asjson_obj(item) for item in data]
        else:
            return data
    elif isinstance(data, dict):
        return {key: asjson_obj(value) for key, value in data}
    else:
        assert isinstance(data, (str, int, float, bool, None))
        return data


def asdict(data: TSInterface, deepcopy: bool = False) -> Dict:
    assert isinstance(data, TSInterface)
    result = asjson_obj(data, deepcopy)
    assert isinstance(result, Dict)
    return cast(Dict, result)


def fromjson_obj(d: JSON_Type, initial_type: List[type]) -> Union[TSInterface, JSON_Type]:
    if isinstance(d, (str, int, float, type(None))):  return d
    assert isinstance(initial_type, Iterable)
    type_errors = []
    for itype in initial_type:
        try:
            origin = getattr(itype, '__origin__', None)
            if origin is list or origin is List:
                try:
                    typ = itype.__args__[0]
                    return [fromjson_obj(item, [typ]) for item in d]
                except AttributeError:
                    return d
            if origin is dict or origin is Dict:
                try:
                    typ = initial_type.__args__[1]
                    return {key: fromjson_obj(value, [typ]) for key, value in d}
                except AttributeError:
                    return d
            assert issubclass(itype, TSInterface), str(itype)
            if isinstance(d, tuple):
                fields = chain_from_bases(itype, 'fields__', '__annotations__')
                d = {kw: arg for kw, arg in zip(fields.keys(), d)}
            references = chain_from_bases(itype, 'all_refs__', 'references__')
            refs = {field: fromjson_obj(d[field], typ)
                    for field, typ in references.items() if field in d}
            merged = {**d, **refs}
            return itype(**merged)
        except TypeError as e:
            type_errors.append(str(e))
    raise TypeError(f"No matching types for {d} among {initial_type}:\n" + '\n'.join(type_errors))


def fromdict(d: Dict, initial_type: Union[type, List[type]]) -> TSInterface:
    assert isinstance(d, Dict)
    if not isinstance(initial_type, Iterable):
        initial_type = [initial_type]
    result = fromjson_obj(d, initial_type)
    assert isinstance(result, TSInterface)
    return result


def json_adaptor(func):
    params = func.__annotations__
    if len(params) != 2 or 'return' not in params:
        raise ValueError(f'Decorator "json_adaptor" does not work with function '
            f'"{func.__name__}" annotated with "{params}"! '
            f'LSP functions can have at most one argument. Both the type of the '
            f' argument and the return type must be specified with annotations.')
    return_type = params['return']
    for k in params:
        if k != 'return':
            call_type = params[k]
            break
    ct_forward = isinstance(call_type, ForwardRef) or isinstance(call_type, str)
    rt_forward = isinstance(return_type, ForwardRef) or isinstance(return_type, str)
    resolve_types = ct_forward or rt_forward

    @functools.wraps(func)
    def adaptor(*args, **kwargs):
        nonlocal resolve_types, return_type, call_type
        if resolve_types:
            if isinstance(call_type, ForwardRef):  call_type = call_type.__forward_arg__
            elif isinstance(call_type, str):  call_type = eval(call_type)
            if isinstance(return_type, ForwardRef):  return_type = return_type.__forward_arg__
            elif isinstance(return_type, str):  return_type = eval(return_type)
            resolve_types = False
        dict_obj = args[0] if args else kwargs
        call_params = fromjson_obj(dict_obj, [call_type])
        return_val = func(call_params)
        return asjson_obj(return_val)

    return adaptor


#######################################################################
#
# Language-Server-Protocol data structures (AUTOGENERATED: Don't edit!)
#
#######################################################################

##### BEGIN OF LSP SPECS

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
    params: Union[List, object, None]


@dataclass
class ResponseMessage(Message):
    id: Union[int, str, None]
    result: Union[str, float, bool, object, None]
    error: Optional['ResponseError']


@dataclass
class ResponseError:
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


@dataclass
class NotificationMessage(Message):
    method: str
    params: Union[List, object, None]


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
    documentChanges: Union[List[TextDocumentEdit], List[Union[TextDocumentEdit, CreateFile, RenameFile, DeleteFile]], None]
    changeAnnotations: Optional[Dict[str, ChangeAnnotation]]


@dataclass
class WorkspaceEditClientCapabilities:
    @dataclass
    class ChangeAnnotationSupport_:
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


@dataclass
class PartialResultParams:
    partialResultToken: Optional[ProgressToken]


TraceValue = str


@dataclass
class InitializeParams(WorkDoneProgressParams):
    @dataclass
    class ClientInfo_:
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
class ClientCapabilities:
    @dataclass
    class Workspace_:
        @dataclass
        class FileOperations_:
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
    @dataclass
    class Window_:
        workDoneProgress: Optional[bool]
        showMessage: Optional['ShowMessageRequestClientCapabilities']
        showDocument: Optional['ShowDocumentClientCapabilities']
    @dataclass
    class General_:
        regularExpressions: Optional[RegularExpressionsClientCapabilities]
        markdown: Optional[MarkdownClientCapabilities]
    workspace: Optional[Workspace_]
    textDocument: Optional[TextDocumentClientCapabilities]
    window: Optional[Window_]
    general: Optional[General_]
    experimental: Optional[Any]


@dataclass
class InitializeResult:
    @dataclass
    class ServerInfo_:
        name: str
        version: Optional[str]
    capabilities: 'ServerCapabilities'
    serverInfo: Optional[ServerInfo_]


class InitializeError(IntEnum):
    unknownProtocolVersion = 1


@dataclass
class InitializeError:
    retry: bool


@dataclass
class ServerCapabilities:
    @dataclass
    class Workspace_:
        @dataclass
        class FileOperations_:
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


class MessageType(IntEnum):
    Error = 1
    Warning = 2
    Info = 3
    Log = 4


@dataclass
class ShowMessageRequestClientCapabilities:
    @dataclass
    class MessageActionItem_:
        additionalPropertiesSupport: Optional[bool]
    messageActionItem: Optional[MessageActionItem_]


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
    changeNotifications: Union[str, bool, None]


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


class FileChangeType(IntEnum):
    Created = 1
    Changed = 2
    Deleted = 3


@dataclass
class WorkspaceSymbolClientCapabilities:
    @dataclass
    class SymbolKind_:
        valueSet: Optional[List['SymbolKind']]
    @dataclass
    class TagSupport_:
        valueSet: List['SymbolTag']
    dynamicRegistration: Optional[bool]
    symbolKind: Optional[SymbolKind_]
    tagSupport: Optional[TagSupport_]


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
class TextDocumentSyncOptions:
    openClose: Optional[bool]
    change: Optional[TextDocumentSyncKind]
    willSave: Optional[bool]
    willSaveWaitUntil: Optional[bool]
    save: Union[bool, SaveOptions, None]


@dataclass
class PublishDiagnosticsClientCapabilities:
    @dataclass
    class TagSupport_:
        valueSet: List[DiagnosticTag]
    relatedInformation: Optional[bool]
    tagSupport: Optional[TagSupport_]
    versionSupport: Optional[bool]
    codeDescriptionSupport: Optional[bool]
    dataSupport: Optional[bool]


@dataclass
class PublishDiagnosticsParams:
    uri: DocumentUri
    version: Optional[int]
    diagnostics: List[Diagnostic]


@dataclass
class CompletionClientCapabilities:
    @dataclass
    class CompletionItem_:
        @dataclass
        class TagSupport_:
            valueSet: List['CompletionItemTag']
        @dataclass
        class ResolveSupport_:
            properties: List[str]
        @dataclass
        class InsertTextModeSupport_:
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
    @dataclass
    class CompletionItemKind_:
        valueSet: Optional[List['CompletionItemKind']]
    dynamicRegistration: Optional[bool]
    completionItem: Optional[CompletionItem_]
    completionItemKind: Optional[CompletionItemKind_]
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


class InsertTextFormat(IntEnum):
    PlainText = 1
    Snippet = 2


class CompletionItemTag(IntEnum):
    Deprecated = 1


@dataclass
class InsertReplaceEdit:
    newText: str
    insert: Range
    replace: Range


class InsertTextMode(IntEnum):
    asIs = 1
    adjustIndentation = 2


@dataclass
class CompletionItem:
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
class SignatureHelpClientCapabilities:
    @dataclass
    class SignatureInformation_:
        @dataclass
        class ParameterInformation_:
            labelOffsetSupport: Optional[bool]
        documentationFormat: Optional[List[MarkupKind]]
        parameterInformation: Optional[ParameterInformation_]
        activeParameterSupport: Optional[bool]
    dynamicRegistration: Optional[bool]
    signatureInformation: Optional[SignatureInformation_]
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
    documentation: Union[str, MarkupContent, None]
    parameters: Optional[List['ParameterInformation']]
    activeParameter: Optional[int]


@dataclass
class ParameterInformation:
    label: Union[str, Tuple[int, int]]
    documentation: Union[str, MarkupContent, None]


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


class DocumentHighlightKind(IntEnum):
    Text = 1
    Read = 2
    Write = 3


@dataclass
class DocumentSymbolClientCapabilities:
    @dataclass
    class SymbolKind_:
        valueSet: Optional[List['SymbolKind']]
    @dataclass
    class TagSupport_:
        valueSet: List['SymbolTag']
    dynamicRegistration: Optional[bool]
    symbolKind: Optional[SymbolKind_]
    hierarchicalDocumentSymbolSupport: Optional[bool]
    tagSupport: Optional[TagSupport_]
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
class CodeActionClientCapabilities:
    @dataclass
    class CodeActionLiteralSupport_:
        @dataclass
        class CodeActionKind_:
            valueSet: List['CodeActionKind']
        codeActionKind: CodeActionKind_
    @dataclass
    class ResolveSupport_:
        properties: List[str]
    dynamicRegistration: Optional[bool]
    codeActionLiteralSupport: Optional[CodeActionLiteralSupport_]
    isPreferredSupport: Optional[bool]
    disabledSupport: Optional[bool]
    dataSupport: Optional[bool]
    resolveSupport: Optional[ResolveSupport_]
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
class CodeAction:
    @dataclass
    class Disabled_:
        reason: str
    title: str
    kind: Optional[CodeActionKind]
    diagnostics: Optional[List[Diagnostic]]
    isPreferred: Optional[bool]
    disabled: Optional[Disabled_]
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


@dataclass
class SemanticTokensLegend:
    tokenTypes: List[str]
    tokenModifiers: List[str]


@dataclass
class SemanticTokensClientCapabilities:
    @dataclass
    class Requests_:
        @dataclass
        class Range_1:
            pass
        @dataclass
        class Full_1:
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


@dataclass
class SemanticTokensOptions(WorkDoneProgressOptions):
    @dataclass
    class Range_1:
        pass
    @dataclass
    class Full_1:
        delta: Optional[bool]
    legend: SemanticTokensLegend
    range: Union[bool, Range_1, None]
    full: Union[bool, Full_1, None]


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


@dataclass
class Moniker:
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



##### END OF LSP SPECS


#######################################################################
#
# Language-Server-Protocol methods
#
#######################################################################

class LSPBase:
    @json_adaptor
    def initialize(self, params: InitializeParams) -> InitializeResult:
        raise NotImplementedError
