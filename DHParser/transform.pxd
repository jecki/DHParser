#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

import cython

# any functions that causes trouble with cython has been commented out!

# cpdef transformation_factory(t1=?, t2=?, t3=?, t4=?, t5=?)
# cpdef type_guard(t)
# cpdef decorator(f)
# cpdef gen_special(*args)
# cpdef gen_partial(*args, **kwargs)
cpdef key_node_name(node: Node)
# cpdef traverse(root_node: Node, processing_table: ProcessingTableType,
#               key_func: KeyFunc = ?)
# cpdef traverse_recursive(path)
# cpdef traverse_locally(path: List[Node], processing_table: Dict,
#                       key_func: Callable = ?)
# cpdef apply_if(path: List[Node], transformation: Callable,
#                condition: Callable)
# cpdef apply_unless(path: List[Node], transformation: Callable,
#                  condition: Callable)
cpdef is_single_child(path: List[Node])
cpdef is_named(path: List[Node])
cpdef is_anonymous(path: List[Node])
cpdef contains_only_whitespace(path: List[Node])
cpdef is_empty(path: List[Node])
# cpdef is_token(path: List[Node], tokens: AbstractSet[str] = ?)
# cpdef is_one_of(path: List[Node], name_set: AbstractSet[str])
# cpdef not_one_of(path: List[Node], name_set: AbstractSet[str])
# cpdef name_matches(path: List[Node], patterns: AbstractSet[str])
# cpdef content_matches(path: List[Node], regexp: str)
# cpdef has_ancestor(path: List[Node], name_set: AbstractSet[str])
cpdef _replace_by(node: Node, child: Node, root: RootNode)
cpdef _reduce_child(node: Node, child: Node, root: RootNode)
cpdef replace_by_single_child(path: List[Node])
cpdef reduce_single_child(path: List[Node])
# cpdef replace_or_reduce(path: List[Node], condition: Callable = ?)
# cpdef change_name(path: List[Node], name: str)
# cpdef flatten(path: List[Node], condition: Callable = ?,
#               recursive: bool = ?)
cpdef collapse(path: List[Node])
# cpdef collapse_children_if(path: List[Node], condition: Callable,
#                   target_tag: ParserBase)
# cpdef close_package()
# cpdef transform_content(path: List[Node], func: Callable)
# cpdef replace_content_with(path: List[Node], content: str)
cpdef normalize_whitespace(path)
# cpdef merge_whitespace(path)
# cpdef move_fringes(path, condition: Callable = ?)
## cpdef lstrip(path: List[Node], condition: Callable = ?)
## cpdef rstrip(path: List[Node], condition: Callable = ?)
## cpdef strip(path: List[Node], condition: Callable = ?)
# cpdef keep_children(path: List[Node], section: slice)
# cpdef keep_children_if(path: List[Node], condition: Callable)
# cpdef keep_tokens(path: List[Node], tokens: AbstractSet[str] = ?)
# cpdef keep_nodes(path: List[Node], names: AbstractSet[str])
# cpdef keep_content(path: List[Node], regexp: str)
# cpdef remove_children_if(path: List[Node], condition: Callable)
# cpdef remove_brackets(path: List[Node])
# cpdef remove_tokens(path: List[Node], tokens: AbstractSet[str] = ?)
# cpdef remove_children(path: List[Node], names: AbstractSet[str])
# cpdef remove_content(path: List[Node], regexp: str)
# cpdef error_on(path: List[Node], condition: Callable,
#              error_msg: str, error_code: ErrorCode)
# cpdef assert_content(path: List[Node], regexp: str)
# cpdef require(path: List[Node], child_tags: AbstractSet[str])
# cpdef forbid(path: List[Node], child_tags: AbstractSet[str])
cpdef peek(path: List[Node])