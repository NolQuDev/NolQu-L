#!/usr/bin/env python3
# Transitional LLVM bootstrap.
# New language-semantics work should prefer the real Nolqu frontend/IR bridge.
import re
import sys
from dataclasses import dataclass


TOKEN_RE = re.compile(
    r"\s*(?:(?P<int>\d+)|(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>==|!=|>=|<=|[+\-*/%()=<>{},]))"
)


class ParseError(Exception):
    pass


@dataclass
class Token:
    kind: str
    value: str


def tokenize(expr: str):
    pos = 0
    out = []
    while pos < len(expr):
        m = TOKEN_RE.match(expr, pos)
        if not m:
            raise ParseError(f"unsupported expression syntax near: {expr[pos:]}")
        pos = m.end()
        if m.lastgroup == "int":
            out.append(Token("int", m.group("int")))
        elif m.lastgroup == "ident":
            out.append(Token("ident", m.group("ident")))
        else:
            out.append(Token("op", m.group("op")))
    out.append(Token("eof", ""))
    return out


def with_line(lineno: int, exc: ParseError):
    msg = str(exc)
    if msg.startswith("line "):
        return exc
    return ParseError(f"line {lineno}: {msg}")


def stmt_line(stmt):
    return stmt[1]


class ExprParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def cur(self):
        return self.tokens[self.pos]

    def eat(self, value=None, kind=None):
        tok = self.cur()
        if value is not None and tok.value != value:
            raise ParseError(f"expected '{value}'")
        if kind is not None and tok.kind != kind:
            raise ParseError(f"expected {kind}")
        self.pos += 1
        return tok

    def parse(self):
        node = self.parse_expr()
        if self.cur().kind != "eof":
            raise ParseError("unexpected trailing tokens")
        return node

    def parse_condition(self):
        lhs = self.parse_expr()
        if self.cur().value not in {"==", "!=", ">", "<", ">=", "<="}:
            raise ParseError("expected comparison operator in condition")
        op = self.eat(kind="op").value
        rhs = self.parse_expr()
        if self.cur().kind != "eof":
            raise ParseError("unexpected trailing tokens")
        return ("cmp", op, lhs, rhs)

    def parse_expr(self):
        node = self.parse_term()
        while self.cur().value in {"+", "-"}:
            op = self.eat(kind="op").value
            rhs = self.parse_term()
            node = (op, node, rhs)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.cur().value in {"*", "/", "%"}:
            op = self.eat(kind="op").value
            rhs = self.parse_factor()
            node = (op, node, rhs)
        return node

    def parse_factor(self):
        tok = self.cur()
        if tok.kind == "int":
            self.eat(kind="int")
            return ("int", int(tok.value))
        if tok.kind == "ident":
            name = self.eat(kind="ident").value
            if self.cur().value == "(":
                self.eat(value="(")
                args = []
                if self.cur().value != ")":
                    while True:
                        args.append(self.parse_expr())
                        if self.cur().value == ",":
                            self.eat(value=",")
                            continue
                        break
                self.eat(value=")")
                return ("call", name, args)
            return ("ident", name)
        if tok.value == "(":
            self.eat(value="(")
            node = self.parse_expr()
            self.eat(value=")")
            return node
        raise ParseError("expected factor")


class LLVMBuilder:
    def __init__(self):
        self.temp_id = 0
        self.label_id = 0
        self.lines = []
        self.functions = []
        self.vars = {}
        self.func_sigs = {}
        self.in_function = False

    def new_tmp(self):
        self.temp_id += 1
        return f"%t{self.temp_id}"

    def emit(self, line):
        self.lines.append(line)

    def new_label(self, stem):
        self.label_id += 1
        return f"{stem}{self.label_id}"

    def compile_expr(self, node):
        kind = node[0]
        if kind == "int":
            return str(node[1])
        if kind == "ident":
            name = node[1]
            if name not in self.vars:
                raise ParseError(f"undefined variable: {name}")
            tmp = self.new_tmp()
            self.emit(f"  {tmp} = load i64, ptr %{name}")
            return tmp
        if kind == "call":
            _, name, args = node
            if name not in self.func_sigs:
                raise ParseError(f"undefined function: {name}")
            _, expected = self.func_sigs[name]
            if len(args) != expected:
                raise ParseError(
                    f"wrong number of function arguments for '{name}': expected {expected}, got {len(args)}"
                )
            values = [self.compile_expr(arg) for arg in args]
            tmp = self.new_tmp()
            arg_text = ", ".join(f"i64 {value}" for value in values)
            self.emit(f"  {tmp} = call i64 @{name}({arg_text})")
            return tmp
        op, lhs, rhs = node
        l = self.compile_expr(lhs)
        r = self.compile_expr(rhs)
        tmp = self.new_tmp()
        if op == "+":
            self.emit(f"  {tmp} = add i64 {l}, {r}")
        elif op == "-":
            self.emit(f"  {tmp} = sub i64 {l}, {r}")
        elif op == "*":
            self.emit(f"  {tmp} = mul i64 {l}, {r}")
        elif op == "/":
            self.emit(f"  {tmp} = sdiv i64 {l}, {r}")
        elif op == "%":
            self.emit(f"  {tmp} = srem i64 {l}, {r}")
        else:
            raise ParseError(f"unsupported operator: {op}")
        return tmp

    def declare_var(self, name, expr):
        if name in self.vars:
            raise ParseError(f"duplicate variable: {name}")
        self.vars[name] = True
        self.emit(f"  %{name} = alloca i64")
        value = self.compile_expr(expr)
        self.emit(f"  store i64 {value}, ptr %{name}")

    def assign_var(self, name, expr):
        if name not in self.vars:
            raise ParseError(f"undefined variable: {name}")
        value = self.compile_expr(expr)
        self.emit(f"  store i64 {value}, ptr %{name}")

    def print_expr(self, expr):
        value = self.compile_expr(expr)
        fmt_ptr = self.new_tmp()
        self.emit(f"  {fmt_ptr} = getelementptr [6 x i8], ptr @.fmt, i64 0, i64 0")
        self.emit(f"  call i32 (ptr, ...) @printf(ptr {fmt_ptr}, i64 {value})")

    def compile_return(self, expr):
        if not self.in_function:
            raise ParseError("return outside function")
        value = self.compile_expr(expr)
        self.emit(f"  ret i64 {value}")

    def compile_condition(self, cond):
        _, op, lhs, rhs = cond
        l = self.compile_expr(lhs)
        r = self.compile_expr(rhs)
        tmp = self.new_tmp()
        op_map = {
            "==": "eq",
            "!=": "ne",
            ">": "sgt",
            "<": "slt",
            ">=": "sge",
            "<=": "sle",
        }
        self.emit(f"  {tmp} = icmp {op_map[op]} i64 {l}, {r}")
        return tmp

    def compile_block(self, stmts):
        terminated = False
        for stmt in stmts:
            if terminated:
                raise with_line(stmt_line(stmt), ParseError("unreachable statement after terminator"))
            terminated = self.compile_stmt(stmt)
        return terminated

    def compile_stmt(self, stmt):
        kind = stmt[0]
        lineno = stmt[1]
        try:
            if kind == "var":
                _, _, name, expr = stmt
                self.declare_var(name, expr)
                return False
            if kind == "assign":
                _, _, name, expr = stmt
                self.assign_var(name, expr)
                return False
            if kind == "print":
                _, _, expr = stmt
                self.print_expr(expr)
                return False
            if kind == "if":
                _, _, cond, then_stmts, else_stmts = stmt
                cond_tmp = self.compile_condition(cond)
                then_lbl = self.new_label("if_then_")
                else_lbl = self.new_label("if_else_")
                end_lbl = self.new_label("if_end_")
                self.emit(f"  br i1 {cond_tmp}, label %{then_lbl}, label %{else_lbl}")
                self.emit(f"{then_lbl}:")
                then_terminated = self.compile_block(then_stmts)
                if not then_terminated:
                    self.emit(f"  br label %{end_lbl}")
                self.emit(f"{else_lbl}:")
                else_terminated = self.compile_block(else_stmts)
                if not else_terminated:
                    self.emit(f"  br label %{end_lbl}")
                if then_terminated and else_terminated:
                    return True
                self.emit(f"{end_lbl}:")
                return False
            if kind == "while":
                _, _, cond, body_stmts = stmt
                cond_lbl = self.new_label("while_cond_")
                body_lbl = self.new_label("while_body_")
                end_lbl = self.new_label("while_end_")
                self.emit(f"  br label %{cond_lbl}")
                self.emit(f"{cond_lbl}:")
                cond_tmp = self.compile_condition(cond)
                self.emit(f"  br i1 {cond_tmp}, label %{body_lbl}, label %{end_lbl}")
                self.emit(f"{body_lbl}:")
                body_terminated = self.compile_block(body_stmts)
                if not body_terminated:
                    self.emit(f"  br label %{cond_lbl}")
                self.emit(f"{end_lbl}:")
                return False
            if kind == "func":
                _, _, name, params, body_stmts = stmt
                self.compile_function(name, params, body_stmts)
                return False
            if kind == "return":
                _, _, expr = stmt
                self.compile_return(expr)
                return True
            raise ParseError(f"unsupported statement kind: {kind}")
        except ParseError as exc:
            raise with_line(lineno, exc) from exc

    def compile_function(self, name, params, body_stmts):
        old_lines = self.lines
        old_vars = self.vars
        old_in_function = self.in_function
        self.lines = []
        self.vars = {}
        self.in_function = True
        for param in params:
            if param in self.vars:
                raise ParseError(f"duplicate parameter: {param}")
            self.vars[param] = True
            self.emit(f"  %{param} = alloca i64")
            self.emit(f"  store i64 %{param}.arg, ptr %{param}")
        terminated = self.compile_block(body_stmts)
        if not terminated:
            raise ParseError(f"function '{name}' must end with return")
        sig = ", ".join(f"i64 %{param}.arg" for param in params)
        self.functions.append(f"define i64 @{name}({sig}) {{")
        self.functions.append("entry:")
        self.functions.extend(self.lines)
        self.functions.append("}")
        self.functions.append("")
        self.lines = old_lines
        self.vars = old_vars
        self.in_function = old_in_function


def parse_var_line(stripped: str, lineno: int):
    rest = stripped[4:]
    if "=" not in rest:
        raise ParseError("expected '=' in var declaration")
    name, expr = rest.split("=", 1)
    name = name.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ParseError(f"invalid variable name: {name}")
    return ("var", lineno, name, ExprParser(tokenize(expr)).parse())


def parse_assign_line(stripped: str, lineno: int):
    name, expr = stripped.split("=", 1)
    name = name.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ParseError(f"invalid assignment target: {name}")
    return ("assign", lineno, name, ExprParser(tokenize(expr)).parse())


def parse_func_header(stripped: str):
    m = re.fullmatch(r"func\s+([A-Za-z_][A-Za-z0-9_]*)\(([^)]*)\)\s*\{", stripped)
    if not m:
        raise ParseError(f"invalid function declaration: {stripped}")
    name = m.group(1)
    params_raw = m.group(2).strip()
    params = []
    if params_raw:
        for item in params_raw.split(","):
            param = item.strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", param):
                raise ParseError(f"invalid parameter name: {param}")
            params.append(param)
    return name, params


def normalize_lines(text: str):
    lines = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line == "} else {":
            lines.append((lineno, "}"))
            lines.append((lineno, "else {"))
        else:
            lines.append((lineno, line))
    return lines


def parse_stmt_line(stripped: str, lines, idx):
    lineno = lines[idx][0]
    if stripped.startswith("var "):
        return parse_var_line(stripped, lineno), idx + 1
    if stripped.startswith("print "):
        expr = stripped[6:].strip()
        return ("print", lineno, ExprParser(tokenize(expr)).parse()), idx + 1
    if stripped.startswith("return "):
        expr = stripped[7:].strip()
        return ("return", lineno, ExprParser(tokenize(expr)).parse()), idx + 1
    if stripped.startswith("func ") and stripped.endswith("{"):
        name, params = parse_func_header(stripped)
        body_stmts, next_idx = parse_block(lines, idx + 1)
        return ("func", lineno, name, params, body_stmts), next_idx
    if stripped.startswith("if ") and stripped.endswith("{"):
        cond_text = stripped[3:-1].strip()
        cond = ExprParser(tokenize(cond_text)).parse_condition()
        then_stmts, next_idx = parse_block(lines, idx + 1)
        else_stmts = []
        if next_idx < len(lines) and lines[next_idx][1] == "else {":
            else_stmts, next_idx = parse_block(lines, next_idx + 1)
        return ("if", lineno, cond, then_stmts, else_stmts), next_idx
    if stripped.startswith("while ") and stripped.endswith("{"):
        cond_text = stripped[6:-1].strip()
        cond = ExprParser(tokenize(cond_text)).parse_condition()
        body_stmts, next_idx = parse_block(lines, idx + 1)
        return ("while", lineno, cond, body_stmts), next_idx
    if "=" in stripped and not stripped.startswith("func "):
        return parse_assign_line(stripped, lineno), idx + 1
    raise ParseError(f"unsupported LLVM backend statement: {stripped}")


def parse_block(lines, idx):
    stmts = []
    while idx < len(lines):
        lineno, stripped = lines[idx]
        if stripped == "}":
            return stmts, idx + 1
        try:
            stmt, idx = parse_stmt_line(stripped, lines, idx)
        except ParseError as exc:
            raise with_line(lineno, exc) from exc
        stmts.append(stmt)
    raise ParseError("expected '}'")


def parse_program(text: str):
    lines = normalize_lines(text)
    stmts = []
    idx = 0
    while idx < len(lines):
        lineno, stripped = lines[idx]
        try:
            stmt, idx = parse_stmt_line(stripped, lines, idx)
        except ParseError as exc:
            raise with_line(lineno, exc) from exc
        stmts.append(stmt)
    return stmts


def collect_function_signatures(stmts):
    sigs = {}
    for stmt in stmts:
        if stmt[0] != "func":
            continue
        _, lineno, name, params, _ = stmt
        if name in sigs:
            prev_line, _ = sigs[name]
            raise ParseError(f"line {lineno}: duplicate function: {name} (first declared at line {prev_line})")
        sigs[name] = (lineno, len(params))
    return sigs


def compile_source(src_path: str, out_path: str):
    builder = LLVMBuilder()
    with open(src_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        stmts = parse_program(source)
        builder.func_sigs = collect_function_signatures(stmts)
    except ParseError as exc:
        raise ParseError(str(exc)) from exc

    ir = [
        '; Nolqu experimental LLVM backend bootstrap',
        'declare i32 @printf(ptr, ...)',
        '@.fmt = private constant [6 x i8] c"%lld\\0A\\00"',
        '',
    ]
    for stmt in stmts:
        builder.compile_stmt(stmt)
    ir.extend(builder.functions)
    ir.extend([
        'define i32 @main() {',
        'entry:',
    ])
    ir.extend(builder.lines)
    ir.extend([
        '  ret i32 0',
        '}',
        '',
    ])

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ir))


def main(argv):
    if len(argv) != 3:
        print("usage: nq_llvm_bootstrap.py <input.nq> <output.ll>", file=sys.stderr)
        return 1
    src_path, out_path = argv[1], argv[2]
    try:
        compile_source(src_path, out_path)
    except ParseError as exc:
        print(f"[nolqu-llvm] Error: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {out_path} written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
