#!/usr/bin/env python3
import json
import re
import sys


LINE_RE = re.compile(
    r"^(?P<index>\d+)\t(?P<op>[A-Z0-9_]+) A=(?P<a>-?\d+) B=(?P<b>-?\d+) LN=(?P<line>\d+)(?: NAME=(?P<name>[A-Za-z_][A-Za-z0-9_]*))?(?: TEXT=(?P<text>.*))?$"
)


def parse_ir_dump(text: str):
    lines = [line.rstrip("\n") for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("empty IR dump")
    if lines[0] != "== IR ==":
        raise ValueError("missing IR header")

    out = []
    for raw in lines[1:]:
        m = LINE_RE.fullmatch(raw)
        if not m:
            raise ValueError(f"unsupported IR dump line: {raw}")
        item = {
            "index": int(m.group("index")),
            "op": m.group("op"),
            "a": int(m.group("a")),
            "b": int(m.group("b")),
            "line": int(m.group("line")),
        }
        if m.group("name") is not None:
            item["name"] = m.group("name")
        if m.group("text") is not None:
            item["text"] = m.group("text")
        out.append(item)
    return out


def main(argv):
    if len(argv) != 3:
        print("usage: nq_ir_dump_parser.py <input.ir> <output.json>", file=sys.stderr)
        return 1

    input_path, output_path = argv[1], argv[2]
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            parsed = parse_ir_dump(f.read())
    except (OSError, ValueError) as exc:
        print(f"[nq-ir-parser] Error: {exc}", file=sys.stderr)
        return 1

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)
            f.write("\n")
    except OSError as exc:
        print(f"[nq-ir-parser] Error: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {output_path} written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
