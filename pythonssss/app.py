from flask import Flask, render_template, request, jsonify
import ast
import math
import operator
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "calculator.db"

# Only these mathematical operators are allowed by the expression parser.
ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}
ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Scientific functions available to the user.
FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)),
    "tan": lambda x: math.tan(math.radians(x)),
    "asin": lambda x: math.degrees(math.asin(x)),
    "acos": lambda x: math.degrees(math.acos(x)),
    "atan": lambda x: math.degrees(math.atan(x)),
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
    "exp": math.exp,
    "factorial": math.factorial,
}
CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression TEXT NOT NULL,
                result TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_history(expression, result, mode):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO history (expression, result, mode, created_at) VALUES (?, ?, ?, ?)",
            (expression, result, mode, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()


def get_history(limit=100):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, expression, result, mode, created_at "
            "FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def fmt(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.12g}"


def normalize_expression(expression):
    expression = expression.strip().replace("×", "*").replace("÷", "/")
    expression = expression.replace("^", "**")
    # A simple calculator-friendly percentage conversion:
    # 20% becomes (20/100), so 500*20% becomes 100.
    expression = __import__("re").sub(
        r"(?<![A-Za-z_])(\d+(?:\.\d+)?)%",
        r"(\1/100)",
        expression,
    )
    return expression


def safe_eval(expression):
    expression = normalize_expression(expression)
    if not expression:
        raise ValueError("Enter a mathematical expression.")
    if len(expression) > 500:
        raise ValueError("Expression is too long. Maximum is 500 characters.")

    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError):
        raise ValueError("Invalid mathematical expression.")

    def calc(node):
        if isinstance(node, ast.Expression):
            return calc(node.body)

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if not math.isfinite(float(node.value)):
                raise ValueError("Invalid number.")
            return node.value

        if isinstance(node, ast.Name):
            if node.id in CONSTANTS:
                return CONSTANTS[node.id]
            raise ValueError(f"Unknown name: {node.id}")

        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY_OPS:
            return ALLOWED_UNARY_OPS[type(node.op)](calc(node.operand))

        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BIN_OPS:
            left = calc(node.left)
            right = calc(node.right)

            if isinstance(node.op, (ast.Div, ast.Mod, ast.FloorDiv)) and right == 0:
                raise ValueError("Cannot divide by zero.")

            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("Exponent is too large.")

            try:
                result = ALLOWED_BIN_OPS[type(node.op)](left, right)
            except (OverflowError, ZeroDivisionError, ValueError):
                raise ValueError("Invalid or extremely large result.")

            if not math.isfinite(float(result)):
                raise ValueError("Invalid or extremely large result.")
            return result

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                raise ValueError("That function is not allowed.")
            if len(node.args) != 1 or node.keywords:
                raise ValueError("Functions must have exactly one input.")
            value = calc(node.args[0])

            if node.func.id == "factorial":
                if not float(value).is_integer() or value < 0 or value > 1000:
                    raise ValueError("Factorial needs a whole number from 0 to 1000.")

            try:
                result = FUNCTIONS[node.func.id](value)
            except (ValueError, OverflowError, ZeroDivisionError):
                raise ValueError(f"Invalid value for {node.func.id}().")

            if not math.isfinite(float(result)):
                raise ValueError("Invalid or extremely large result.")
            return result

        raise ValueError("Only supported mathematical expressions are allowed.")

    return calc(tree)


def expression_steps(expression):
    """
    Creates a useful explanation without pretending to be a full symbolic algebra system.
    It reports the expression, the detected operation categories, and the final evaluated result.
    """
    normalized = normalize_expression(expression)
    tree = ast.parse(normalized, mode="eval")

    operations = []

    def walk(node):
        if isinstance(node, ast.BinOp):
            names = {
                ast.Add: "addition (+)",
                ast.Sub: "subtraction (-)",
                ast.Mult: "multiplication (*)",
                ast.Div: "division (/)",
                ast.Mod: "remainder (%)",
                ast.Pow: "power (**)",
                ast.FloorDiv: "floor division (//)",
            }
            operations.append(names.get(type(node.op), "operation"))
            walk(node.left)
            walk(node.right)
        elif isinstance(node, ast.Call):
            operations.append(f"function {node.func.id}()")
            for arg in node.args:
                walk(arg)
        elif isinstance(node, ast.UnaryOp):
            walk(node.operand)

    walk(tree.body)
    result = safe_eval(expression)

    unique_ops = []
    for item in operations:
        if item not in unique_ops:
            unique_ops.append(item)

    steps = [
        f"1. Read the complete expression: {expression}",
        "2. Apply parentheses and normal mathematical operator precedence (PEMDAS).",
    ]
    if "%" in expression:
        steps.append("3. Convert percentage values such as 20% into 20/100.")
    if unique_ops:
        steps.append(
            f"{len(steps) + 1}. Detected operations: " + ", ".join(unique_ops) + "."
        )
    steps.append(
        f"{len(steps) + 1}. Evaluate the expression from the inner/highest-priority operations outward."
    )
    steps.append(f"{len(steps) + 1}. Final answer: {fmt(result)}")
    return steps


def calculate_statistics(raw):
    if not raw.strip():
        raise ValueError("Enter numbers separated by commas.")
    try:
        values = [float(x.strip()) for x in raw.replace(";", ",").split(",") if x.strip()]
    except ValueError:
        raise ValueError("Use numbers separated by commas.")
    if not values:
        raise ValueError("Enter at least one number.")
    if len(values) > 1000:
        raise ValueError("Statistics input is limited to 1000 numbers.")

    ordered = sorted(values)
    n = len(values)
    mean = sum(values) / n
    median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2

    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    highest = max(counts.values())
    modes = sorted([v for v, c in counts.items() if c == highest]) if highest > 1 else []

    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = math.sqrt(variance)

    return {
        "count": n,
        "sum": sum(values),
        "mean": mean,
        "median": median,
        "mode": modes,
        "minimum": min(values),
        "maximum": max(values),
        "range": max(values) - min(values),
        "variance": variance,
        "standard_deviation": std_dev,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/calculate")
def calculate():
    data = request.get_json(silent=True) or {}
    expression = str(data.get("expression", "")).strip()
    mode = str(data.get("mode", "Smart")).strip() or "Smart"

    try:
        if mode == "Statistics":
            stats = calculate_statistics(expression)
            result = fmt(stats["mean"])
            save_history(expression, result, mode)
            return jsonify(
                success=True,
                result=result,
                expression=expression,
                mode=mode,
                statistics={k: ([fmt(x) for x in v] if isinstance(v, list) else fmt(v) if isinstance(v, (int, float)) else v)
                            for k, v in stats.items()},
            )

        # Batch mode: multiple expressions separated by a newline or semicolon.
        if mode == "Batch":
            raw_items = [x.strip() for x in expression.replace(";", "\n").splitlines() if x.strip()]
            if not raw_items:
                raise ValueError("Enter at least one expression.")
            if len(raw_items) > 50:
                raise ValueError("Batch mode supports up to 50 expressions at once.")

            results = []
            for item in raw_items:
                value = safe_eval(item)
                results.append({"expression": item, "result": fmt(value)})
                save_history(item, fmt(value), "Batch")
            return jsonify(success=True, batch=results, result=f"{len(results)} calculations completed.")

        value = safe_eval(expression)
        result = fmt(value)
        save_history(expression, result, mode)

        steps = expression_steps(expression) if mode == "Smart" else []
        return jsonify(
            success=True,
            result=result,
            expression=expression,
            mode=mode,
            steps=steps,
        )

    except (ValueError, OverflowError, ZeroDivisionError) as error:
        return jsonify(success=False, error=str(error)), 400


@app.post("/api/history/clear")
def clear_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM history")
        conn.commit()
    return jsonify(success=True)


@app.get("/api/history")
def history():
    return jsonify(history=get_history())


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
