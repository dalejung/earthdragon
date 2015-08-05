import ast
from ast import UnaryOp, BinOp, Tuple, Name
import copy
from functools import singledispatch
import inspect

from asttools import get_source, func_rewrite, func_code, Matcher, unwrap
from asttools.function import get_invoked_args, create_function

from .context import section
from .typelet import List, Type

class Pattern:
    when = None
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def _match(self, obj, args, kwargs):
        if not self.match(obj):
            return False
        if self.when:
            ret = self.when(*args, **kwargs)
            return ret
        return True

_default = object()
class DefaultPattern(Pattern):
    def match(self, obj):
        return True

class InstancePattern(Pattern):
    _type = Type(type)

    def __init__(self, _type):
        self._type = _type

    def match(self, obj):
        return isinstance(obj, self._type)

class ScalarPattern(Pattern):
    def __init__(self, value):
        self.value = value

    def match(self, obj):
        if not isinstance(obj, (int, str)):
            return False
        return obj == self.value

class IdentityPattern(Pattern):
    def __init__(self, value):
        self.value = value

    def match(self, obj):
        return obj is self.value

class MultiPattern(Pattern):
    patterns = List(Pattern)

    def match(self, obj):
        assert len(obj) == len(self.patterns)
        tests = zip(self.patterns, obj)
        return all([p.match(o) for p, o in tests])

class UnhandledPatternError(Exception):
    pass

class PatternMatcher:
    match = List(str)
    patterns = List(Pattern)

    def __init__(self, argspec, match, meta):
        self.argspec = argspec
        self.match = match
        self.meta = meta
        self.patterns = []
        self.funcs = {}

    def add_pattern(self, pattern, func):
        self.patterns.append(pattern)
        self.funcs[pattern] = func

    def __call__(self, *args, **kwargs):
        invoked = get_invoked_args(self.argspec, *args, **kwargs)
        mvars = [invoked[name] for name in self.match]
        if len(mvars) == 1:
            mvars = mvars[0]

        for pattern in self.patterns:
            if pattern._match(mvars, args, kwargs):
                func = self.funcs[pattern]
                return func(*args, **kwargs)
        raise UnhandledPatternError("Not handled by PatternMatcher")

def config_from_subscript(sub):
    """
    Convert
    [name: "Frank", siblings: 'Bob', 'Sarah']

    to:

    {
        'name': [ast.Name(id='Frank')],
        'siblings': [
            ast.Name(id='Bob'),
            ast.Name(id='Sarah'),
        ]
    }
    Note: the values are still ast.AST nodes
    """
    assert isinstance(sub, ast.Subscript)

    blocks = {}
    block = None
    if isinstance(sub.slice, ast.ExtSlice):
        items = sub.slice.dims
    else:
        items = [sub.slice]

    for item in items:
        name, value = process_item(item)
        if name:
            block = blocks.setdefault(name, [])
        block.append(value)
    return blocks

def process_item(item):
    if isinstance(item, ast.Slice):
        name = unwrap(item.lower)
        value = item.upper
        return name, value

    if isinstance(item, ast.Index):
        return None, item.value
    raise TypeError()


def get_meta(sub):
    blocks = config_from_subscript(sub)
    meta = {}
    for k, vals in blocks.items():
        meta[k] = list(map(unwrap, vals))
    return meta

def validate(meta_line, cases):
    assert meta_line == Matcher('meta[_any_]')

    case_matcher = Matcher("~ _any_ | _any_")
    tuple_matcher = Matcher("~ _any_ | _any_, _any_")
    for line in cases:
        pass

def pattern_split(lines):
    return lines[0], lines[1:]

def pattern(func):
    builder = PatternBuilder(func)
    return builder.build()

def resolve_name(scope, name):
    import builtins
    try:
        return scope[name]
    except KeyError:
        return getattr(builtins, name)

_na = object()
def before_pipe(node):
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Invert):
            return node.operand, _na
    if isinstance(node, ast.BinOp):
        if isinstance(node.left, ast.UnaryOp) and isinstance(node.op, ast.BitOr):
            return before_pipe(node.left)[0], node.right
        if isinstance(node.op, ast.BitOr):
            return node.left, node.right
    raise TypeError("Unsupported node type")

def after_pipe(node):
    return _na, node

def split_case_return(node):
    elts = [node]

    if isinstance(node, ast.Tuple):
        elts = node.elts
    found_pipe = False

    case_nodes = []
    return_nodes = []
    grabber = before_pipe
    for elt in elts:
        case_bit, return_bit = grabber(elt)
        if found_pipe: assert case_bit is _na

        if not found_pipe and return_bit is not _na:
            grabber = after_pipe
            found_pipe = True

        if case_bit is not _na:
            case_nodes.append(case_bit)

        if return_bit is not _na:
            return_nodes.append(return_bit)

    return case_nodes, return_nodes

def split_case(node):
    if isinstance(node, ast.Expr):
        node = node.value

    case_nodes, return_nodes = split_case_return(node)

    pattern_case = case_nodes
    if len(case_nodes) == 1:
        pattern_case = case_nodes[0]

    pattern_return = return_nodes[0]
    if len(return_nodes) > 1:
        pattern_return = ast.fix_missing_locations(
            ast.Tuple(elts=return_nodes, ctx=ast.Load())
        )

    return pattern_case, pattern_return

class PatternBuilder:
    def __init__(self, func):
        self.func = func
        self.func_def = func_code(func)
        self.scope = func.__globals__
        self.argspec = inspect.getargspec(func)

    def build(self):
        func = self.func
        func_def = self.func_def
        argspec = self.argspec

        meta_line, cases = pattern_split(func_def.body)
        meta = get_meta(meta_line.value)
        validate(meta_line, cases)

        pt = PatternMatcher(argspec, meta['match'], meta)
        for line in cases:
            pattern, new_func = self.process_case(line, func)
            pt.add_pattern(pattern, new_func)

        return pt

    def process_pattern(self, pnode):
        class_name = pnode.__class__.__name__
        method_name = 'process_pattern_' + class_name
        method = getattr(self, method_name, None)
        if method is None:
            raise TypeError("Unhandled type {0}", class_name)
        return method(pnode)

    def process_pattern_Name(self, pnode):
        pval = unwrap(pnode)
        scope = self.scope
        if pval == 'default':
            obj = _default
        else:
            obj = resolve_name(scope, pval)
        return build_pattern(obj)

    def process_pattern_NameConstant(self, pnode):
        return build_pattern(pnode.value)

    def process_pattern_Str(self, pnode):
        return build_pattern(pnode.s)

    def process_pattern_Num(self, pnode):
        return build_pattern(pnode.n)

    def process_pattern_Subscript(self, pnode):
        pattern = self.process_pattern(pnode.value)
        b = config_from_subscript(pnode)
        when = b.get('when')
        if when:
            when_func = self._return_from_template(when[0])
            pattern.when = when_func
        return pattern

    def process_pattern_list(self, pnode):
        patterns = []
        for node in pnode:
            pattern = self.process_pattern(node)
            patterns.append(pattern)

        return MultiPattern(patterns=patterns)

    def process_case(self, line, func):
        pattern_case, pattern_return = split_case(line)
        pattern = self.process_pattern(pattern_case)
        new_func = self._return_from_template(pattern_return)

        return pattern, new_func

    def _return_from_template(self, expression):
        new_func_def = copy.deepcopy(self.func_def)
        ret = ast.Return(value=expression, lineno=1, col_offset=0)
        new_func_def.body = [ret]
        new_func = create_function(new_func_def, self.func)
        return new_func


def build_pattern(obj):
    if obj is _default:
        return DefaultPattern()
    if isinstance(obj, type):
        return InstancePattern(obj)
    if isinstance(obj, (str, int)):
        return ScalarPattern(obj)
    if any(map(lambda t: obj is t, [None, False, True])):
        return IdentityPattern(obj)
    raise TypeError("Unhandled type {0}", type(obj))

