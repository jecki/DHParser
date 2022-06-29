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
# cpdef traverse_recursive(trail)
# cpdef traverse_locally(trail: List[Node], processing_table: Dict,
#                       key_func: Callable = ?)
# cpdef apply_if(trail: List[Node], transformation: Callable, 
#                condition: Callable)
# cpdef apply_unless(trail: List[Node], transformation: Callable,
#                  condition: Callable)
cpdef is_single_child(trail: List[Node])
cpdef is_named(trail: List[Node])
cpdef is_anonymous(trail: List[Node])
cpdef contains_only_whitespace(trail: List[Node])
cpdef is_empty(trail: List[Node])
# cpdef is_token(trail: List[Node], tokens: AbstractSet[str] = ?)
# cpdef is_one_of(trail: List[Node], name_set: AbstractSet[str])
# cpdef not_one_of(trail: List[Node], name_set: AbstractSet[str])
# cpdef name_matches(trail: List[Node], patterns: AbstractSet[str])
# cpdef content_matches(trail: List[Node], regexp: str)
# cpdef has_ancestor(trail: List[Node], name_set: AbstractSet[str])
cpdef _replace_by(node: Node, child: Node, root: RootNode)
cpdef _reduce_child(node: Node, child: Node, root: RootNode)
cpdef replace_by_single_child(trail: List[Node])
cpdef reduce_single_child(trail: List[Node])
# cpdef replace_or_reduce(trail: List[Node], condition: Callable = ?)
# cpdef change_name(trail: List[Node], name: str)
# cpdef flatten(trail: List[Node], condition: Callable = ?,
#               recursive: bool = ?)
cpdef collapse(trail: List[Node])
# cpdef collapse_children_if(trail: List[Node], condition: Callable,
#                   target_tag: ParserBase)
# cpdef close_package()
# cpdef transform_content(trail: List[Node], func: Callable)
# cpdef replace_content_with(trail: List[Node], content: str)
cpdef normalize_whitespace(trail)
# cpdef merge_whitespace(trail)
# cpdef move_fringes(trail, condition: Callable = ?)
## cpdef lstrip(trail: List[Node], condition: Callable = ?)
## cpdef rstrip(trail: List[Node], condition: Callable = ?)
## cpdef strip(trail: List[Node], condition: Callable = ?)
# cpdef keep_children(trail: List[Node], section: slice)
# cpdef keep_children_if(trail: List[Node], condition: Callable)
# cpdef keep_tokens(trail: List[Node], tokens: AbstractSet[str] = ?)
# cpdef keep_nodes(trail: List[Node], names: AbstractSet[str])
# cpdef keep_content(trail: List[Node], regexp: str)
# cpdef remove_children_if(trail: List[Node], condition: Callable)
# cpdef remove_brackets(trail: List[Node])
# cpdef remove_tokens(trail: List[Node], tokens: AbstractSet[str] = ?)
# cpdef remove_children(trail: List[Node], names: AbstractSet[str])
# cpdef remove_content(trail: List[Node], regexp: str)
# cpdef error_on(trail: List[Node], condition: Callable,
#              error_msg: str, error_code: ErrorCode)
# cpdef assert_content(trail: List[Node], regexp: str)
# cpdef require(trail: List[Node], child_tags: AbstractSet[str])
# cpdef forbid(trail: List[Node], child_tags: AbstractSet[str])
cpdef peek(trail: List[Node])