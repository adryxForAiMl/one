"""Small shared utility helpers, including safe math expression parsing."""

import ast
import math

from backend.exceptions import ValidationError


def parse_csv_numbers(text):
    """Parse a comma-separated string into floats, ignoring blank fields."""
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def _power(base, exponent):
    if abs(exponent) > 10000:
        raise ValidationError("Exponent magnitude must be at most 10000.")
    return base ** exponent


_BINARY = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
           ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
           ast.Pow: _power, ast.Mod: lambda a, b: a % b}
_UNARY = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}
_FUNCTIONS = {name: getattr(math, name) for name in
              ("sin", "cos", "tan", "exp", "log", "sqrt", "log10")}


def compile_expression(expression, variables=("x",)):
    """Compile a small arithmetic expression using only safe math functions."""
    try:
        tree = ast.parse(expression.replace("^", "**"), mode="eval")
    except SyntaxError as exc:
        raise ValidationError("Enter a valid math expression, such as sin(x) or x**2 - 2.") from exc

    def evaluate(node, values):
        if isinstance(node, ast.Expression):
            return evaluate(node.body, values)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in values:
                return values[node.id]
            if node.id == "pi":
                return math.pi
            if node.id == "e":
                return math.e
            raise ValidationError(f"Unknown symbol: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            return _BINARY[type(node.op)](evaluate(node.left, values), evaluate(node.right, values))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](evaluate(node.operand, values))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
            return _FUNCTIONS[node.func.id](*(evaluate(arg, values) for arg in node.args))
        raise ValidationError("Expression supports arithmetic, powers, and basic math functions only.")

    def function(*args):
        return evaluate(tree, dict(zip(variables, args)))
    return function
