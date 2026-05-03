from dataclasses import dataclass

# TODO: determine best data type for variable given value (if int reccomend int, if float reccomend float64, etc)

MATLAB_JULIA_LIB = {
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "exp": "exp",
    "sqrt": "sqrt",
    "log": "log",
    "eye": "eye",
    "zeros": "zeros",
}

SPECIAL_CHATS = {"pi": "π"}


def convert_literal(expr: str) -> str:
    """
    Convert a literal MATLAB expression to Julia syntax.
    Currently a pass-through; extend for things like 1i -> 1im.
    """
    return expr.strip()


@dataclass
class LiteralNode:
    value: str = ""
    translated: str = ""


@dataclass
class OpNode:
    op: str = ""
    left: object = None
    right: object = None


PREC = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}


def _strip_outer_parens(s: str) -> str:
    """
    If the entire string is wrapped in a single pair of outer parentheses,
    strip them so internal operators can be found at depth 0.
    """
    if not s or s[0] != "(" or s[-1] != ")":
        return s
    depth = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and i < len(s) - 1:
            return s
    return s[1:-1]


def _needs_parens(parent_op: str, child_node: object, is_right_child: bool) -> bool:
    """
    Decide whether a child expression must be parenthesized when emitted
    inside a parent operation.
    """
    if not isinstance(child_node, OpNode):
        return False
    child_op = child_node.op
    pp = PREC[parent_op]
    cp = PREC[child_op]
    if cp < pp:
        return True
    if cp > pp:
        return False
    # same precedence
    if parent_op in ("+", "*"):
        return child_op != parent_op
    if parent_op in ("-", "/"):
        return is_right_child
    if parent_op == "^":
        return not is_right_child
    return False


def create_expression_tree(s: str) -> object:
    """
    Build an expression tree from a MATLAB string, splitting on top-level
    arithmetic operators and treating function calls / grouped substrings
    as opaque literals.
    """
    s = s.strip()
    if not s:
        return LiteralNode(s)

    s = _strip_outer_parens(s)

    depth = 0
    candidates = []  # tuples of (precedence, index, operator)

    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and ch in PREC:
            candidates.append((PREC[ch], i, ch))

    if not candidates:
        return LiteralNode(s)

    # Pick the root operator: rightmost for left-assoc, leftmost for right-assoc
    min_prec = min(c[0] for c in candidates)
    same_prec = [c for c in candidates if c[0] == min_prec]

    if len(same_prec) == 1:
        _, split_idx, op = same_prec[0]
    else:
        if any(c[2] == "^" for c in same_prec):
            # right-associative: pick leftmost
            _, split_idx, op = same_prec[0]
        else:
            # left-associative: pick rightmost
            _, split_idx, op = same_prec[-1]

    left_s = s[:split_idx].strip()
    right_s = s[split_idx + 1 :].strip()
    return OpNode(op, create_expression_tree(left_s), create_expression_tree(right_s))


def translate_tree(node: object) -> None:
    """
    Walk the expression tree and translate every LiteralNode leaf via
    translate_expression.
    """
    if isinstance(node, OpNode):
        translate_tree(node.left)
        translate_tree(node.right)
    elif isinstance(node, LiteralNode):
        node.translated = translate_expression(node.value)


def rebuild_string(node: object) -> str:
    """
    Reconstruct the Julia expression string from a translated tree.
    """
    if isinstance(node, LiteralNode):
        return node.translated

    left_str = rebuild_string(node.left)
    right_str = rebuild_string(node.right)

    if _needs_parens(node.op, node.left, is_right_child=False):
        left_str = f"({left_str})"
    if _needs_parens(node.op, node.right, is_right_child=True):
        right_str = f"({right_str})"

    return f"{left_str} {node.op} {right_str}"


def translate_expression(matlab_input: str) -> str:
    """
    Parse a MATLAB-style expression string and convert function calls
    to Julia equivalents. Handles nested function calls by resolving
    innermost parentheses first via a stack.
    """

    stack = []  # frames: (function_name, prefix_before_call)
    current = ""  # text accumulated at the current nesting level

    for ch in matlab_input:
        if ch == "(":
            # Identify function name immediately before this '('
            j = len(current) - 1
            while j >= 0 and (current[j].isalnum() or current[j] == "_"):
                j -= 1
            func_name = current[j + 1 :] if j < len(current) - 1 else ""
            prefix = current[: j + 1]
            stack.append((func_name, prefix))
            current = ""
        elif ch == ")":
            func_name, prefix = stack.pop()
            if func_name and func_name in MATLAB_JULIA_LIB:
                args = (
                    [a.strip() for a in current.split(",")] if current.strip() else []
                )
                julia_func = MATLAB_JULIA_LIB[func_name]
                resolved = f"{julia_func}({', '.join(args)})"
            elif (
                func_name in SPECIAL_CHATS
            ):  # Special case for characters such as pi which are unicode in Julia
                julia_func = SPECIAL_CHATS[func_name]
                resolved = f"{julia_func}"
            elif func_name:
                resolved = f"{func_name}({current})"
            else:
                resolved = f"({convert_literal(current)})"
            current = prefix + resolved
        else:
            current += ch

    return current


if __name__ == "__main__":
    matlab_str = input("What is the MATLAB code to translate? ")
    tree = create_expression_tree(matlab_str)
    translate_tree(tree)
    print(rebuild_string(tree))
