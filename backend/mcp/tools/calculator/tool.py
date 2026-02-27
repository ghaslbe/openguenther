import ast
import operator
import math

SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCS = {
    'abs': abs,
    'round': round,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'log10': math.log10,
    'pi': math.pi,
    'e': math.e,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Nur Zahlen erlaubt")
    elif isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op = SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Operator nicht erlaubt: {type(node.op).__name__}")
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op = SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError("Operator nicht erlaubt")
        return op(operand)
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCS:
            func = SAFE_FUNCS[node.func.id]
            args = [_safe_eval(a) for a in node.args]
            if callable(func):
                return func(*args)
            return func
        raise ValueError(f"Funktion nicht erlaubt: {getattr(node.func, 'id', '?')}")
    elif isinstance(node, ast.Name):
        if node.id in SAFE_FUNCS:
            val = SAFE_FUNCS[node.id]
            if not callable(val):
                return val
        raise ValueError(f"Variable nicht erlaubt: {node.id}")
    raise ValueError("Ungueltiger Ausdruck")


def calculate(expression):
    """Safely evaluate a math expression."""
    try:
        tree = ast.parse(expression, mode='eval')
        result = _safe_eval(tree.body)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e), "expression": expression}


TOOL_DEFINITION = {
    "name": "calculate",
    "description": "Wertet einen mathematischen Ausdruck sicher aus. Unterstuetzt +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e.",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematischer Ausdruck, z.B. '2 + 3 * 4', 'sqrt(144)', 'sin(pi/2)'"
            }
        },
        "required": ["expression"]
    }
}
