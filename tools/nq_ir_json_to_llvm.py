#!/usr/bin/env python3
import json
import sys


class LowerError(Exception):
    pass


class Lowerer:
    def __init__(self, items):
        self.items = items
        self.temp_id = 0
        self.active_context = None
        self.label_prefixes = {
            0: "ie_",
            1: "id_",
            2: "ws_",
            3: "we_",
            4: "cf_",
            5: "cd_",
            6: "tc_",
            7: "te_",
            8: "wc_",
        }
        self.global_slots = self.collect_global_slots()
        self.string_literals = self.collect_string_literals()
        self.input_str_count = self.count_input_str_sites()
        self.int_to_str_count = self.count_int_to_str_sites()
        self.str_concat_count = self.count_str_concat_sites()
        self.input_str_base = max(self.string_literals.keys(), default=-1) + 1
        self.string_dynamic_base = self.input_str_base + self.input_str_count
        self.str_concat_base = self.string_dynamic_base + self.int_to_str_count
        self.string_table_size = self.str_concat_base + self.str_concat_count
        self.input_str_next = 0
        self.int_to_str_next = 0
        self.str_concat_next = 0
        self.unsupported_groups = {}

    @staticmethod
    def item_ref(item):
        details = [f"source line {item['line']}", f"op {item['op']}"]
        if "name" in item:
            details.append(f"name {item['name']}")
        return f"IR index {item['index']} ({', '.join(details)})"

    def error_at(self, item, message):
        if self.active_context is not None:
            return LowerError(f"{self.item_ref(item)} [{self.active_context}]: {message}")
        return LowerError(f"{self.item_ref(item)}: {message}")

    def new_tmp(self):
        self.temp_id += 1
        return f"%t{self.temp_id}"

    def split_program(self):
        functions = []
        main = []
        i = 0
        while i < len(self.items):
            item = self.items[i]
            if item["op"] == "FN_BGN":
                name = item.get("name")
                if not name:
                    raise self.error_at(item, "FN_BGN missing name")
                body = []
                i += 1
                while i < len(self.items) and self.items[i]["op"] != "FN_END":
                    body.append(self.items[i])
                    i += 1
                if i >= len(self.items):
                    raise self.error_at(item, f"missing FN_END for {name}")
                functions.append((name, body))
            else:
                main.append(item)
            i += 1
        return functions, main

    def collect_global_slots(self):
        slots = set()
        for item in self.items:
            if item["op"] in {"LOAD_G", "STORE_G"}:
                slots.add(item["a"])
        return sorted(slots)

    def collect_string_literals(self):
        literals = {}
        for item in self.items:
            if item["op"] == "PRINT_STR":
                text = item.get("text")
                if text is None:
                    raise self.error_at(item, "PRINT_STR is missing exported text")
                literals[item["a"]] = text
            elif item["op"] == "CONST" and "text" in item:
                text = item.get("text")
                if text is None:
                    raise self.error_at(item, "CONST is missing exported text")
                literals[item["a"]] = text
        return literals

    def count_input_str_sites(self):
        return sum(1 for item in self.items if item["op"] == "INPUT_STR")

    def count_int_to_str_sites(self):
        return sum(1 for item in self.items if item["op"] == "INT_TO_STR")

    def count_str_concat_sites(self):
        return sum(1 for item in self.items if item["op"] == "STR_CONCAT")

    @staticmethod
    def llvm_escape(text):
        out = []
        for ch in text.encode("utf-8"):
            if 32 <= ch <= 126 and ch not in (34, 92):
                out.append(chr(ch))
            else:
                out.append(f"\\{ch:02X}")
        return "".join(out)

    def label_name(self, label_type, label_id, item=None):
        if label_type not in self.label_prefixes:
            if item is not None:
                raise self.error_at(item, f"unsupported label type {label_type}")
            raise LowerError(f"unsupported label type {label_type}")
        return f"{self.label_prefixes[label_type]}{label_id}"

    def auto_block_name(self, item):
        return f"bb_{item['index']}"

    def infer_param_count(self, body):
        max_offset = None
        for item in body:
            if item["op"] in {"LOAD_P", "STORE_P"}:
                offset = item["a"]
                if offset < 16 or (offset - 16) % 8 != 0:
                    raise self.error_at(item, f"unsupported parameter offset {offset}")
                max_offset = offset if max_offset is None else max(max_offset, offset)
        if max_offset is None:
            return 0
        return ((max_offset - 16) // 8) + 1

    @staticmethod
    def fold_cmp_bool(body):
        # Pre-scan: collect all cf_ids that are referenced by raw CMP instructions
        # that are NOT immediately followed by the bool pattern (i.e., appear in
        # AND/OR chains). A CMP at index i is a candidate for folding only if
        # body[i+1]["op"] == "CONST" with a==1. All other CMPs reference their
        # cf_id as a branch target that must remain as an actual block.
        # We must NOT fold a CMP whose cf_id is also referenced by an earlier
        # unfolded CMP — otherwise that earlier CMP's branch target disappears.
        shared_cf_ids = set()
        jmp_label_refs = {}
        for j, item in enumerate(body):
            if item["op"] == "JMP":
                key = (item["b"], item["a"])
                jmp_label_refs[key] = jmp_label_refs.get(key, 0) + 1
            if item["op"] == "CMP":
                # Is this a non-terminal CMP (not the start of the bool pattern)?
                if j + 5 >= len(body) or body[j + 1]["op"] != "CONST" or body[j + 1]["a"] != 1:
                    shared_cf_ids.add(item["b"])

        out = []
        i = 0
        while i < len(body):
            if i + 5 < len(body):
                a, b, c, d, e, f = body[i : i + 6]
                if (
                    a["op"] == "CMP"
                    and b["op"] == "CONST"
                    and b["a"] == 1
                    and c["op"] == "JMP"
                    and c["b"] == 5
                    and d["op"] == "LBL"
                    and d["b"] == 4
                    and d["a"] == a["b"]
                    and e["op"] == "CONST"
                    and e["a"] == 0
                    and f["op"] == "LBL"
                    and f["b"] == 5
                    and f["a"] == c["a"]
                    # Only fold if cf_id is not shared with earlier unfolded CMPs
                    and a["b"] not in shared_cf_ids
                    # OR short-circuit emits an earlier JMP to the same done label.
                    # Folding would delete that LBL_CD and leave an undefined branch.
                    and jmp_label_refs.get((c["b"], c["a"]), 0) == 1
                ):
                    out.append(
                        {
                            "index": a["index"],
                            "op": "BOOL_CMP",
                            "a": a["a"],
                            "b": a["b"],
                            "line": a["line"],
                        }
                    )
                    i += 6
                    continue
            out.append(body[i])
            i += 1
        return out

    def param_value(self, item, param_count):
        offset = item["a"]
        if offset < 16 or (offset - 16) % 8 != 0:
            raise self.error_at(item, f"unsupported parameter offset {offset}")
        stack_slot = (offset - 16) // 8
        arg_index = param_count - 1 - stack_slot
        if arg_index < 0 or arg_index >= param_count:
            raise self.error_at(item, f"parameter offset {offset} is outside inferred parameter count {param_count}")
        return f"%arg{arg_index}"

    def lower_block(self, body, *, in_function):
        body = self.fold_cmp_bool(body)
        blocks = []
        current_block = "entry"
        current_lines = []
        current_terminated = False
        last_terminated = False
        skip_until_label = False
        value_stack = []
        current = None
        rbx = None
        rcx = None
        pending_cmp = None
        param_count = self.infer_param_count(body) if in_function else 0
        local_slots = sorted({item["a"] for item in body if item["op"] in {"LOAD_L", "STORE_L"}})
        local_map = {slot: f"%local_{slot}" for slot in local_slots}
        for_slots = sorted({item["a"] for item in body if item["op"] in {"FE_ST", "FE_CMP"}})
        for_map = {slot: f"%forend_{slot}" for slot in for_slots}
        mutable_param_slots = sorted({item["a"] for item in body if item["op"] == "STORE_P"})
        mutable_param_map = {slot: f"%pmut_{slot}" for slot in mutable_param_slots}
        label_incoming_values = {}

        def push_block(skip_to_label=False):
            nonlocal current_block, current_lines, current_terminated, last_terminated, skip_until_label, pending_cmp
            if current_block is not None:
                blocks.append((current_block, current_lines))
                if current_lines:
                    last_terminated = current_terminated
            current_block = None
            current_lines = []
            current_terminated = False
            skip_until_label = skip_to_label
            pending_cmp = None

        def ensure_block(item):
            nonlocal current_block, current_lines, current_terminated, value_stack, current, rbx, rcx, pending_cmp
            if current_block is None:
                if item["op"] == "LBL":
                    current_block = self.label_name(item["b"], item["a"], item)
                else:
                    current_block = self.auto_block_name(item)
                current_lines = []
                current_terminated = False
                value_stack = []
                current = None
                rbx = None
                rcx = None
                pending_cmp = None

        def next_block_name(idx):
            if idx + 1 >= len(body):
                raise self.error_at(body[idx], "control flow requires a fallthrough block")
            nxt = body[idx + 1]
            if nxt["op"] == "LBL":
                return self.label_name(nxt["b"], nxt["a"], nxt)
            return self.auto_block_name(nxt)

        def record_label_value(label_type, label_id, block_name, value):
            if label_type != 5 or block_name is None or value is None:
                return
            target = self.label_name(label_type, label_id)
            label_incoming_values.setdefault(target, []).append((block_name, value))

        def apply_label_phi(label):
            nonlocal current
            incoming = label_incoming_values.get(label)
            if not incoming:
                return
            phi = self.new_tmp()
            incoming_text = ", ".join(f"[ {value}, %{block} ]" for block, value in incoming)
            current_lines.append(f"  {phi} = phi i64 {incoming_text}")
            current = phi

        i = 0
        while i < len(body):
            item = body[i]
            if skip_until_label and item["op"] != "LBL":
                i += 1
                continue
            if skip_until_label and item["op"] == "LBL":
                skip_until_label = False
            ensure_block(item)
            op = item["op"]

            if op == "CONST":
                current = str(item["a"])
            elif op == "ARR_NEW":
                count = item["a"]
                capacity = count + 32
                hdr_count = self.new_tmp()
                raw_ptr = self.new_tmp()
                count_ptr = self.new_tmp()
                data_ptr = self.new_tmp()
                tmp = self.new_tmp()
                current_lines.extend([
                    f"  {hdr_count} = add i64 {count}, 34",
                    f"  {raw_ptr} = call ptr @calloc(i64 {hdr_count}, i64 8)",
                    f"  store i64 {capacity}, ptr {raw_ptr}",
                    f"  {count_ptr} = getelementptr i64, ptr {raw_ptr}, i64 1",
                    f"  store i64 {count}, ptr {count_ptr}",
                    f"  {data_ptr} = getelementptr i64, ptr {raw_ptr}, i64 2",
                    f"  {tmp} = ptrtoint ptr {data_ptr} to i64",
                ])
                current = tmp
            elif op == "LOAD_G":
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = load i64, ptr @gslot_{item['a']}")
                current = tmp
            elif op == "STORE_G":
                if current is None:
                    raise self.error_at(item, "STORE_G without current value")
                current_lines.append(f"  store i64 {current}, ptr @gslot_{item['a']}")
            elif op == "LOAD_L":
                if item["a"] not in local_map:
                    raise self.error_at(item, f"unknown local slot {item['a']}")
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = load i64, ptr {local_map[item['a']]}")
                current = tmp
            elif op == "STORE_L":
                if current is None:
                    raise self.error_at(item, "STORE_L without current value")
                if item["a"] not in local_map:
                    raise self.error_at(item, f"unknown local slot {item['a']}")
                current_lines.append(f"  store i64 {current}, ptr {local_map[item['a']]}")
            elif op == "LOAD_P":
                if item["a"] in mutable_param_map:
                    tmp = self.new_tmp()
                    current_lines.append(f"  {tmp} = load i64, ptr {mutable_param_map[item['a']]}")
                    current = tmp
                else:
                    current = self.param_value(item, param_count)
            elif op == "STORE_P":
                if current is None:
                    raise self.error_at(item, "STORE_P without current value")
                if item["a"] not in mutable_param_map:
                    raise self.error_at(item, f"STORE_P to unknown param slot {item['a']}")
                current_lines.append(f"  store i64 {current}, ptr {mutable_param_map[item['a']]}")
            elif op == "CMP":
                # Non-terminal CMP: appears in AND/OR chains where fold_cmp_bool
                # cannot fold (not followed immediately by the CONST/JMP/LBL/CONST/LBL pattern).
                # Emit a conditional branch to the false label (cf_label_id = item["b"])
                # when the comparison FAILS; otherwise fall through.
                if current is None or rbx is None:
                    raise self.error_at(item, "CMP missing operand state")
                _cmp_fail_pred = {
                    11: "sle",  # GT  fails when rbx <= rax
                    12: "sge",  # LT  fails when rbx >= rax
                    13: "ne",   # EQ  fails when rbx != rax
                    14: "eq",   # NEQ fails when rbx == rax
                    15: "slt",  # GTE fails when rbx <  rax
                    16: "sgt",  # LTE fails when rbx >  rax
                }
                if item["a"] not in _cmp_fail_pred:
                    raise self.error_at(item, f"unsupported compare token {item['a']}")
                cmp_tmp = self.new_tmp()
                fail_label = self.label_name(4, item["b"], item)  # LBL_CF = 4
                fallthrough = next_block_name(i)
                current_lines.append(f"  {cmp_tmp} = icmp {_cmp_fail_pred[item['a']]} i64 {rbx}, {current}")
                current_lines.append(f"  br i1 {cmp_tmp}, label %{fail_label}, label %{fallthrough}")
                current_terminated = True
                push_block()
            elif op == "BOOL_CMP":
                if current is None or rbx is None:
                    raise self.error_at(item, "BOOL_CMP missing operand state")
                pred_map = {
                    11: "sgt",
                    12: "slt",
                    13: "eq",
                    14: "ne",
                    15: "sge",
                    16: "sle",
                }
                if item["a"] not in pred_map:
                    raise self.error_at(item, f"unsupported compare token {item['a']}")
                cmp_tmp = self.new_tmp()
                current_tmp = self.new_tmp()
                current_lines.append(f"  {cmp_tmp} = icmp {pred_map[item['a']]} i64 {rbx}, {current}")
                current_lines.append(f"  {current_tmp} = zext i1 {cmp_tmp} to i64")
                current = current_tmp
            elif op == "PUSH":
                if current is None:
                    raise self.error_at(item, "PUSH without current value")
                value_stack.append(current)
            elif op == "POP_RBX":
                if not value_stack:
                    raise self.error_at(item, "POP_RBX on empty stack")
                rbx = value_stack.pop()
            elif op == "POP_RAX":
                if not value_stack:
                    raise self.error_at(item, "POP_RAX on empty stack")
                current = value_stack.pop()
            elif op == "MOV_RBX":
                if current is None:
                    raise self.error_at(item, "MOV_RBX without current value")
                rbx = current
            elif op == "MOV_RCX":
                if current is None:
                    raise self.error_at(item, "MOV_RCX without current value")
                rcx = current
            elif op == "INC_RAX":
                if current is None:
                    raise self.error_at(item, "INC_RAX without current value")
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = add i64 {current}, 1")
                current = tmp
            elif op == "FE_ST":
                if current is None:
                    raise self.error_at(item, "FE_ST without current value")
                if item["a"] not in for_map:
                    raise self.error_at(item, f"unknown for-end slot {item['a']}")
                current_lines.append(f"  store i64 {current}, ptr {for_map[item['a']]}")
            elif op == "FE_CMP":
                if current is None:
                    raise self.error_at(item, "FE_CMP without current value")
                if item["a"] not in for_map:
                    raise self.error_at(item, f"unknown for-end slot {item['a']}")
                end_tmp = self.new_tmp()
                cmp_tmp = self.new_tmp()
                current_lines.append(f"  {end_tmp} = load i64, ptr {for_map[item['a']]}")
                current_lines.append(f"  {cmp_tmp} = icmp sge i64 {current}, {end_tmp}")
                pending_cmp = cmp_tmp
            elif op == "IMUL8":
                if current is None:
                    raise self.error_at(item, "IMUL8 without current value")
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = mul i64 {current}, 8")
                current = tmp
            elif op in {"ADD", "SUB", "MUL"}:
                if current is None or rbx is None:
                    raise self.error_at(item, f"{op} missing operand state")
                overflow_pair = self.new_tmp()
                tmp = self.new_tmp()
                overflow = self.new_tmp()
                if op == "ADD":
                    current_lines.append(f"  {overflow_pair} = call {{ i64, i1 }} @llvm.sadd.with.overflow.i64(i64 {rbx}, i64 {current})")
                elif op == "SUB":
                    current_lines.append(f"  {overflow_pair} = call {{ i64, i1 }} @llvm.ssub.with.overflow.i64(i64 {rbx}, i64 {current})")
                elif op == "MUL":
                    current_lines.append(f"  {overflow_pair} = call {{ i64, i1 }} @llvm.smul.with.overflow.i64(i64 {rbx}, i64 {current})")
                current_lines.append(f"  {tmp} = extractvalue {{ i64, i1 }} {overflow_pair}, 0")
                current_lines.append(f"  {overflow} = extractvalue {{ i64, i1 }} {overflow_pair}, 1")
                current_lines.append(f"  call void @__nq_check_int_overflow(i1 {overflow})")
                current = tmp
            elif op in {"DIV", "MOD"}:
                # DIV/MOD have no preceding POP_RBX in the IR — left operand is on value_stack
                if current is None or not value_stack:
                    raise self.error_at(item, f"{op} missing operand state")
                left = value_stack.pop()
                tmp = self.new_tmp()
                current_lines.append(f"  call void @__nq_check_div_zero(i64 {current})")
                if op == "DIV":
                    current_lines.append(f"  {tmp} = sdiv i64 {left}, {current}")
                elif op == "MOD":
                    current_lines.append(f"  {tmp} = srem i64 {left}, {current}")
                current = tmp
            elif op == "CALL":
                name = item.get("name")
                if not name:
                    raise self.error_at(item, "CALL missing name")
                argc = 0
                if i + 1 < len(body) and body[i + 1]["op"] == "ADD_RSP":
                    rsp_bytes = body[i + 1]["a"]
                    if rsp_bytes % 8 != 0:
                        raise self.error_at(body[i + 1], f"ADD_RSP operand {rsp_bytes} is not a multiple of 8")
                    argc = rsp_bytes // 8
                    i += 1
                if argc > len(value_stack):
                    raise self.error_at(item, f"CALL needs {argc} args but stack has {len(value_stack)}")
                args = value_stack[-argc:] if argc else []
                if argc:
                    value_stack = value_stack[:-argc]
                arg_text = ", ".join(f"i64 {value}" for value in args)
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = call i64 @{name}({arg_text})")
                current = tmp
            elif op == "ADD_RSP":
                pass
            elif op in {"SET_EF", "CLR_EF", "MOD_BGN", "MOD_END"}:
                pass
            elif op == "JMP_TC":
                target = self.label_name(6, item["a"], item)
                current_lines.append(f"  br label %{target}")
                current_terminated = True
                push_block(True)
            elif op == "JZ":
                if current is None:
                    raise self.error_at(item, "JZ without current value")
                cond_tmp = self.new_tmp()
                target = self.label_name(item["b"], item["a"], item)
                fallthrough = next_block_name(i)
                current_lines.append(f"  {cond_tmp} = icmp eq i64 {current}, 0")
                current_lines.append(f"  br i1 {cond_tmp}, label %{target}, label %{fallthrough}")
                current_terminated = True
                push_block()
            elif op == "JMP":
                target = self.label_name(item["b"], item["a"], item)
                record_label_value(item["b"], item["a"], current_block, current)
                current_lines.append(f"  br label %{target}")
                current_terminated = True
                push_block(True)
            elif op == "JGE":
                if pending_cmp is None:
                    raise self.error_at(item, "JGE without FE_CMP compare state")
                target = self.label_name(item["b"], item["a"], item)
                fallthrough = next_block_name(i)
                current_lines.append(f"  br i1 {pending_cmp}, label %{target}, label %{fallthrough}")
                current_terminated = True
                push_block()
            elif op == "LBL":
                target = self.label_name(item["b"], item["a"], item)
                if current_block is None:
                    current_block = target
                    current_lines = []
                    current_terminated = False
                    apply_label_phi(target)
                elif not current_lines:
                    if current_block != target:
                        record_label_value(item["b"], item["a"], current_block, current)
                        current_lines.append(f"  br label %{target}")
                        current_terminated = True
                        push_block()
                        current_block = target
                        current_lines = []
                        current_terminated = False
                        apply_label_phi(target)
                    else:
                        apply_label_phi(target)
                else:
                    record_label_value(item["b"], item["a"], current_block, current)
                    current_lines.append(f"  br label %{target}")
                    current_terminated = True
                    push_block()
                    current_block = target
                    current_lines = []
                    current_terminated = False
                    apply_label_phi(target)
            elif op == "RET":
                if current is None:
                    raise self.error_at(item, "RET without current value")
                current_lines.append(f"  ret i64 {current}")
                current_terminated = True
                push_block(True)
            elif op == "PRINT_INT":
                if current is None:
                    raise self.error_at(item, "PRINT_INT without current value")
                fmt_ptr = self.new_tmp()
                current_lines.append(f"  {fmt_ptr} = getelementptr [6 x i8], ptr @.fmt, i64 0, i64 0")
                current_lines.append(f"  call i32 (ptr, ...) @printf(ptr {fmt_ptr}, i64 {current})")
            elif op == "PRINT_STR":
                if item["a"] not in self.string_literals:
                    raise self.error_at(item, f"unknown string literal index {item['a']}")
                fmt_ptr = self.new_tmp()
                str_ptr = self.new_tmp()
                text = self.string_literals[item["a"]]
                current_lines.append(f"  {fmt_ptr} = getelementptr [4 x i8], ptr @.strfmt, i64 0, i64 0")
                current_lines.append(
                    f"  {str_ptr} = getelementptr [{len(text.encode('utf-8')) + 1} x i8], ptr @strlit_{item['a']}, i64 0, i64 0"
                )
                current_lines.append(f"  call i32 (ptr, ...) @printf(ptr {fmt_ptr}, ptr {str_ptr})")
            elif op == "PRINT_STR_VAR":
                if current is None:
                    raise self.error_at(item, "PRINT_STR_VAR without current value")
                if self.string_table_size == 0:
                    raise self.error_at(item, "PRINT_STR_VAR requires string slot table")
                current_lines.append(f"  call void @__nq_print_str_id(i64 {current})")
            elif op == "STR_LEN":
                if current is None:
                    raise self.error_at(item, "STR_LEN without current value")
                if self.string_table_size == 0:
                    raise self.error_at(item, "STR_LEN requires string slot table")
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = call i64 @__nq_str_len_id(i64 {current})")
                current = tmp
            elif op == "STR_AT":
                if current is None or not value_stack:
                    raise self.error_at(item, "STR_AT missing operand state")
                if self.string_table_size == 0:
                    raise self.error_at(item, "STR_AT requires string slot table")
                base = value_stack.pop()
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = call i64 @__nq_str_at_id(i64 {base}, i64 {current})")
                current = tmp
            elif op == "STR_CONCAT":
                if current is None or rbx is None:
                    raise self.error_at(item, "STR_CONCAT missing operand state")
                if self.str_concat_next >= self.str_concat_count:
                    raise self.error_at(item, "STR_CONCAT slot allocation overflow")
                slot = self.str_concat_base + self.str_concat_next
                self.str_concat_next += 1
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = call i64 @__nq_str_concat_slot(i64 {slot}, i64 {rbx}, i64 {current})")
                current = tmp
            elif op == "STR_TO_INT":
                if current is None:
                    raise self.error_at(item, "STR_TO_INT without current value")
                if self.string_table_size == 0:
                    raise self.error_at(item, "STR_TO_INT requires string slot table")
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = call i64 @__nq_str_to_int_id(i64 {current})")
                current = tmp
            elif op == "INT_TO_STR":
                if current is None:
                    raise self.error_at(item, "INT_TO_STR without current value")
                if self.int_to_str_next >= self.int_to_str_count:
                    raise self.error_at(item, "INT_TO_STR slot allocation overflow")
                slot = self.string_dynamic_base + self.int_to_str_next
                self.int_to_str_next += 1
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = call i64 @__nq_int_to_str_slot(i64 {slot}, i64 {current})")
                current = tmp
            elif op in {"STR_EQ", "STR_NEQ"}:
                if current is None or not value_stack:
                    raise self.error_at(item, f"{op} missing operand state")
                if self.string_table_size == 0:
                    raise self.error_at(item, f"{op} requires string slot table")
                left = value_stack.pop()
                eq_tmp = self.new_tmp()
                current_lines.append(f"  {eq_tmp} = call i64 @__nq_str_eq_id(i64 {left}, i64 {current})")
                if op == "STR_EQ":
                    current = eq_tmp
                else:
                    neq_cmp = self.new_tmp()
                    neq_tmp = self.new_tmp()
                    current_lines.append(f"  {neq_cmp} = icmp eq i64 {eq_tmp}, 0")
                    current_lines.append(f"  {neq_tmp} = zext i1 {neq_cmp} to i64")
                    current = neq_tmp
            elif op == "HEAP_ST":
                if current is None or not value_stack:
                    raise self.error_at(item, "HEAP_ST missing operand state")
                base = value_stack[-1]  # peek array ptr from stack top (not pop)
                addr_i64 = self.new_tmp()
                addr_ptr = self.new_tmp()
                current_lines.append(f"  {addr_i64} = add i64 {base}, {item['a']}")
                current_lines.append(f"  {addr_ptr} = inttoptr i64 {addr_i64} to ptr")
                current_lines.append(f"  store i64 {current}, ptr {addr_ptr}")
            elif op == "ARR_LD":
                if current is None or not value_stack:
                    raise self.error_at(item, "ARR_LD missing base or offset")
                base = value_stack.pop()
                base_ptr = self.new_tmp()
                addr_i64 = self.new_tmp()
                addr_ptr = self.new_tmp()
                load_tmp = self.new_tmp()
                current_lines.append(f"  {base_ptr} = inttoptr i64 {base} to ptr")
                current_lines.append(f"  call void @__nq_check_arr_bounds(ptr {base_ptr}, i64 {current})")
                current_lines.append(f"  {addr_i64} = add i64 {base}, {current}")
                current_lines.append(f"  {addr_ptr} = inttoptr i64 {addr_i64} to ptr")
                current_lines.append(f"  {load_tmp} = load i64, ptr {addr_ptr}")
                current = load_tmp
            elif op == "ARR_ST":
                if current is None or len(value_stack) < 2:
                    raise self.error_at(item, "ARR_ST missing offset on stack")
                offset = value_stack.pop()
                base = value_stack.pop()
                base_ptr = self.new_tmp()
                addr_i64 = self.new_tmp()
                addr_ptr = self.new_tmp()
                current_lines.append(f"  {base_ptr} = inttoptr i64 {base} to ptr")
                current_lines.append(f"  call void @__nq_check_arr_bounds(ptr {base_ptr}, i64 {offset})")
                current_lines.append(f"  {addr_i64} = add i64 {base}, {offset}")
                current_lines.append(f"  {addr_ptr} = inttoptr i64 {addr_i64} to ptr")
                current_lines.append(f"  store i64 {current}, ptr {addr_ptr}")
            elif op == "ARR_PUSH":
                if current is None or not value_stack:
                    raise self.error_at(item, "ARR_PUSH missing array/value state")
                base = value_stack.pop()
                base_ptr = self.new_tmp()
                tmp = self.new_tmp()
                current_lines.append(f"  {base_ptr} = inttoptr i64 {base} to ptr")
                current_lines.append(f"  {tmp} = call i64 @__nq_arr_push_i64(ptr {base_ptr}, i64 {current})")
                current = tmp
            elif op == "ARR_POP":
                if current is None:
                    raise self.error_at(item, "ARR_POP without array value")
                base_ptr = self.new_tmp()
                tmp = self.new_tmp()
                current_lines.append(f"  {base_ptr} = inttoptr i64 {current} to ptr")
                current_lines.append(f"  {tmp} = call i64 @__nq_arr_pop_i64(ptr {base_ptr})")
                current = tmp
            elif op == "LNOT":
                if current is None:
                    raise self.error_at(item, "LNOT: no current value")
                tmp_cmp = self.new_tmp()
                tmp_ext = self.new_tmp()
                current_lines.append(f"  {tmp_cmp} = icmp eq i64 {current}, 0")
                current_lines.append(f"  {tmp_ext} = zext i1 {tmp_cmp} to i64")
                current = tmp_ext
            elif op == "ARR_LEN":
                if current is None:
                    raise self.error_at(item, "ARR_LEN: no current value")
                tmp_sub = self.new_tmp()
                tmp_ptr = self.new_tmp()
                tmp_len = self.new_tmp()
                current_lines.append(f"  {tmp_sub} = sub i64 {current}, 8")
                current_lines.append(f"  {tmp_ptr} = inttoptr i64 {tmp_sub} to ptr")
                current_lines.append(f"  {tmp_len} = load i64, ptr {tmp_ptr}")
                current = tmp_len
            elif op == "ABS":
                if current is None:
                    raise self.error_at(item, "ABS: no current value")
                tmp_neg = self.new_tmp()
                tmp_is_neg = self.new_tmp()
                tmp_result = self.new_tmp()
                current_lines.append(f"  {tmp_neg} = sub i64 0, {current}")
                current_lines.append(f"  {tmp_is_neg} = icmp slt i64 {current}, 0")
                current_lines.append(f"  {tmp_result} = select i1 {tmp_is_neg}, i64 {tmp_neg}, i64 {current}")
                current = tmp_result
            elif op == "MIN":
                if current is None or rbx is None:
                    raise self.error_at(item, "MIN: missing operand state")
                tmp_cond = self.new_tmp()
                tmp_result = self.new_tmp()
                current_lines.append(f"  {tmp_cond} = icmp slt i64 {rbx}, {current}")
                current_lines.append(f"  {tmp_result} = select i1 {tmp_cond}, i64 {rbx}, i64 {current}")
                current = tmp_result
            elif op == "MAX":
                if current is None or rbx is None:
                    raise self.error_at(item, "MAX: missing operand state")
                tmp_cond = self.new_tmp()
                tmp_result = self.new_tmp()
                current_lines.append(f"  {tmp_cond} = icmp sgt i64 {rbx}, {current}")
                current_lines.append(f"  {tmp_result} = select i1 {tmp_cond}, i64 {rbx}, i64 {current}")
                current = tmp_result
            elif op == "INPUT_STR":
                slot = self.input_str_base + self.input_str_next
                self.input_str_next += 1
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = call i64 @__nq_input_str_slot(i64 {slot})")
                current = tmp
            elif op == "INPUT_INT":
                tmp_buf = self.new_tmp()
                tmp_fmt = self.new_tmp()
                tmp_val = self.new_tmp()
                current_lines.append(f"  {tmp_buf} = alloca i64")
                current_lines.append(f"  {tmp_fmt} = getelementptr [5 x i8], ptr @.fmt_d, i64 0, i64 0")
                current_lines.append(f"  call i32 (ptr, ...) @scanf(ptr {tmp_fmt}, ptr {tmp_buf})")
                current_lines.append(f"  {tmp_val} = load i64, ptr {tmp_buf}")
                current = tmp_val
            elif op == "ARGC":
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = load i64, ptr @nq_argc")
                current = tmp
            elif op == "ARG":
                if current is None:
                    raise self.error_at(item, "ARG without index value")
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = call i64 @__nq_arg(i64 {current})")
                current = tmp
            elif op == "PRINT_NL":
                nl_ptr = self.new_tmp()
                current_lines.append(f"  {nl_ptr} = getelementptr [2 x i8], ptr @.nl, i64 0, i64 0")
                current_lines.append(f"  call i32 (ptr, ...) @printf(ptr {nl_ptr})")
            elif op in {"BAND", "BOR", "BXOR"}:
                if current is None or rbx is None:
                    raise self.error_at(item, f"{op} missing operand state")
                tmp = self.new_tmp()
                if op == "BAND":
                    current_lines.append(f"  {tmp} = and i64 {rbx}, {current}")
                elif op == "BOR":
                    current_lines.append(f"  {tmp} = or i64 {rbx}, {current}")
                elif op == "BXOR":
                    current_lines.append(f"  {tmp} = xor i64 {rbx}, {current}")
                current = tmp
            elif op == "BNOT":
                if current is None:
                    raise self.error_at(item, "BNOT: no current value")
                tmp = self.new_tmp()
                current_lines.append(f"  {tmp} = xor i64 {current}, -1")
                current = tmp
            elif op in {"SHL", "SHR"}:
                # SHL/SHR pop LHS from value_stack (shift amount is current)
                if current is None or not value_stack:
                    raise self.error_at(item, f"{op} missing operand state")
                left = value_stack.pop()
                count = self.new_tmp()
                tmp = self.new_tmp()
                current_lines.append(f"  {count} = and i64 {current}, 63")
                if op == "SHL":
                    current_lines.append(f"  {tmp} = shl i64 {left}, {count}")
                else:
                    current_lines.append(f"  {tmp} = ashr i64 {left}, {count}")
                current = tmp
            else:
                raise self.unsupported_op_error(item)
            i += 1

        if current_block is not None:
            blocks.append((current_block, current_lines))
            if current_lines:
                last_terminated = current_terminated

        return blocks, param_count, last_terminated, local_slots, for_slots, mutable_param_slots

    def lower(self):
        functions, main = self.split_program()
        ir = ["; Nolqu IR to LLVM IR bridge"]
        ir.append("@nq_argc = private global i64 0")
        ir.append("@nq_argv = private global ptr null")
        for slot in self.global_slots:
            ir.append(f"@gslot_{slot} = global i64 0")
        for idx, text in sorted(self.string_literals.items()):
            escaped = self.llvm_escape(text)
            text_len = len(text.encode("utf-8")) + 1
            ir.append(f'@strlit_{idx} = private constant [{text_len} x i8] c"{escaped}\\00"')
        for dyn_slot in range(self.input_str_count):
            ir.append(f"@nq_input_str_buf_{dyn_slot} = private global [256 x i8] zeroinitializer")
        for dyn_slot in range(self.int_to_str_count):
            ir.append(f"@nq_its_buf_{dyn_slot} = private global [32 x i8] zeroinitializer")
        for dyn_slot in range(self.str_concat_count):
            ir.append(f"@nq_strcat_buf_{dyn_slot} = private global [4096 x i8] zeroinitializer")
        string_table_size = self.string_table_size
        if string_table_size:
            string_ptrs = []
            for idx in range(string_table_size):
                if idx in self.string_literals:
                    text_len = len(self.string_literals[idx].encode("utf-8")) + 1
                    string_ptrs.append(f"ptr getelementptr ([{text_len} x i8], ptr @strlit_{idx}, i64 0, i64 0)")
                elif self.input_str_base <= idx < self.input_str_base + self.input_str_count:
                    dyn_idx = idx - self.input_str_base
                    string_ptrs.append(f"ptr getelementptr ([256 x i8], ptr @nq_input_str_buf_{dyn_idx}, i64 0, i64 0)")
                elif self.string_dynamic_base <= idx < self.string_dynamic_base + self.int_to_str_count:
                    dyn_idx = idx - self.string_dynamic_base
                    string_ptrs.append(f"ptr getelementptr ([32 x i8], ptr @nq_its_buf_{dyn_idx}, i64 0, i64 0)")
                elif self.str_concat_base <= idx < self.str_concat_base + self.str_concat_count:
                    dyn_idx = idx - self.str_concat_base
                    string_ptrs.append(f"ptr getelementptr ([4096 x i8], ptr @nq_strcat_buf_{dyn_idx}, i64 0, i64 0)")
                else:
                    string_ptrs.append("ptr null")
            string_ptr_list = ", ".join(string_ptrs)
            ir.append(f"@str_ptrs = private constant [{string_table_size} x ptr] [{string_ptr_list}]")
            string_lens = [
                str(len(self.string_literals[idx].encode("utf-8")) if idx in self.string_literals else 0)
                for idx in range(string_table_size)
            ]
            string_len_list = ", ".join("i64 " + v for v in string_lens)
            ir.append(f"@str_lens = private global [{string_table_size} x i64] [{string_len_list}]")
        ir.extend([
            "declare i32 @printf(ptr, ...)",
            "declare i32 @puts(ptr)",
            "declare i32 @scanf(ptr, ...)",
            "declare ptr @fgets(ptr, i32, ptr)",
            "declare i32 @snprintf(ptr, i64, ptr, ...)",
            "declare i32 @strcmp(ptr, ptr)",
            "declare void @exit(i32)",
            "declare ptr @calloc(i64, i64)",
            "@stdin = external global ptr",
            "declare void @llvm.memcpy.p0.p0.i64(ptr, ptr, i64, i1)",
            "declare { i64, i1 } @llvm.sadd.with.overflow.i64(i64, i64)",
            "declare { i64, i1 } @llvm.ssub.with.overflow.i64(i64, i64)",
            "declare { i64, i1 } @llvm.smul.with.overflow.i64(i64, i64)",
            '@.fmt = private constant [6 x i8] c"%lld\\0A\\00"',
            '@.strfmt = private constant [4 x i8] c"%s\\0A\\00"',
            '@.fmt_d = private constant [5 x i8] c"%lld\\00"',
            '@.nl = private constant [2 x i8] c"\\0A\\00"',
            '@.arr_oob = private constant [26 x i8] c"array index out of bounds\\00"',
            '@.arr_full = private constant [24 x i8] c"array capacity exceeded\\00"',
            '@.arr_empty = private constant [26 x i8] c"array pop: array is empty\\00"',
            '@.str_oob = private constant [27 x i8] c"string index out of bounds\\00"',
            '@.div_zero = private constant [17 x i8] c"division by zero\\00"',
            '@.int_ovf = private constant [17 x i8] c"integer overflow\\00"',
            '@.bad_str = private constant [18 x i8] c"bad string handle\\00"',
            '@.its_fail = private constant [21 x i8] c"int to string failed\\00"',
            '@.strcat_ovf = private constant [23 x i8] c"string concat overflow\\00"',
            "",
            "define void @__nq_check_int_overflow(i1 %overflow) {",
            "entry:",
            "  br i1 %overflow, label %overflow_block, label %ok",
            "overflow_block:",
            "  %msg = getelementptr [17 x i8], ptr @.int_ovf, i64 0, i64 0",
            "  call i32 @puts(ptr %msg)",
            "  call void @exit(i32 1)",
            "  unreachable",
            "ok:",
            "  ret void",
            "}",
            "",
            'define i64 @__nq_atoi_ptr(ptr %ptr) {',
            'entry:',
            '  %first = load i8, ptr %ptr',
            '  %is_minus = icmp eq i8 %first, 45',
            '  %start = select i1 %is_minus, i64 1, i64 0',
            '  br label %loop',
            'loop:',
            '  %idx = phi i64 [ %start, %entry ], [ %next_idx, %digit ]',
            '  %acc = phi i64 [ 0, %entry ], [ %next_acc, %digit ]',
            '  %char_ptr = getelementptr i8, ptr %ptr, i64 %idx',
            '  %char = load i8, ptr %char_ptr',
            '  %is_zero = icmp eq i8 %char, 0',
            '  br i1 %is_zero, label %finish, label %digit_check',
            'digit_check:',
            '  %below = icmp ult i8 %char, 48',
            '  %above = icmp ugt i8 %char, 57',
            '  %not_digit = or i1 %below, %above',
            '  br i1 %not_digit, label %finish, label %digit',
            'digit:',
            '  %digit_i8 = sub i8 %char, 48',
            '  %digit_i64 = zext i8 %digit_i8 to i64',
            '  %scaled = mul i64 %acc, 10',
            '  %next_acc = add i64 %scaled, %digit_i64',
            '  %next_idx = add i64 %idx, 1',
            '  br label %loop',
            'finish:',
            '  %neg_acc = sub i64 0, %acc',
            '  %result = select i1 %is_minus, i64 %neg_acc, i64 %acc',
            '  ret i64 %result',
            '}',
            '',
            'define i64 @__nq_arg(i64 %index) {',
            'entry:',
            '  %neg = icmp slt i64 %index, 0',
            '  br i1 %neg, label %oob, label %range',
            'range:',
            '  %argc = load i64, ptr @nq_argc',
            '  %too_high = icmp sge i64 %index, %argc',
            '  br i1 %too_high, label %oob, label %load',
            'load:',
            '  %argv = load ptr, ptr @nq_argv',
            '  %slot = getelementptr ptr, ptr %argv, i64 %index',
            '  %arg_ptr = load ptr, ptr %slot',
            '  %is_null = icmp eq ptr %arg_ptr, null',
            '  br i1 %is_null, label %oob, label %parse',
            'parse:',
            '  %value = call i64 @__nq_atoi_ptr(ptr %arg_ptr)',
            '  ret i64 %value',
            'oob:',
            '  ret i64 0',
            '}',
            '',
            'define i64 @__nq_arr_push_i64(ptr %base, i64 %value) {',
            'entry:',
            '  %count_slot = getelementptr i64, ptr %base, i64 -1',
            '  %capacity_slot = getelementptr i64, ptr %base, i64 -2',
            '  %count = load i64, ptr %count_slot',
            '  %capacity = load i64, ptr %capacity_slot',
            '  %full = icmp sge i64 %count, %capacity',
            '  br i1 %full, label %full_block, label %ok',
            'ok:',
            '  %elem = getelementptr i64, ptr %base, i64 %count',
            '  store i64 %value, ptr %elem',
            '  %next = add i64 %count, 1',
            '  store i64 %next, ptr %count_slot',
            '  ret i64 %next',
            'full_block:',
            '  %msg = getelementptr [24 x i8], ptr @.arr_full, i64 0, i64 0',
            '  call i32 @puts(ptr %msg)',
            '  call void @exit(i32 1)',
            '  unreachable',
            '}',
            '',
            'define i64 @__nq_arr_pop_i64(ptr %base) {',
            'entry:',
            '  %count_slot = getelementptr i64, ptr %base, i64 -1',
            '  %count = load i64, ptr %count_slot',
            '  %empty = icmp eq i64 %count, 0',
            '  br i1 %empty, label %empty_block, label %ok',
            'ok:',
            '  %next = sub i64 %count, 1',
            '  store i64 %next, ptr %count_slot',
            '  %elem = getelementptr i64, ptr %base, i64 %next',
            '  %value = load i64, ptr %elem',
            '  ret i64 %value',
            'empty_block:',
            '  %msg = getelementptr [26 x i8], ptr @.arr_empty, i64 0, i64 0',
            '  call i32 @puts(ptr %msg)',
            '  call void @exit(i32 1)',
            '  unreachable',
            '}',
            '',
            "define void @__nq_check_div_zero(i64 %divisor) {",
            "entry:",
            "  %is_zero = icmp eq i64 %divisor, 0",
            "  br i1 %is_zero, label %zero, label %ok",
            "zero:",
            "  %msg = getelementptr [17 x i8], ptr @.div_zero, i64 0, i64 0",
            "  call i32 @puts(ptr %msg)",
            "  call void @exit(i32 1)",
            "  unreachable",
            "ok:",
            "  ret void",
            "}",
            "",
            "define void @__nq_check_arr_bounds(ptr %base, i64 %offset) {",
            "entry:",
            "  %neg = icmp slt i64 %offset, 0",
            "  br i1 %neg, label %oob, label %check",
            "check:",
            "  %hdr = getelementptr i64, ptr %base, i64 -1",
            "  %len = load i64, ptr %hdr",
            "  %len_bytes = mul i64 %len, 8",
            "  %too_high = icmp sge i64 %offset, %len_bytes",
            "  br i1 %too_high, label %oob, label %ok",
            "oob:",
            "  %msg = getelementptr [26 x i8], ptr @.arr_oob, i64 0, i64 0",
            "  call i32 @puts(ptr %msg)",
            "  call void @exit(i32 1)",
            "  unreachable",
            "ok:",
            "  ret void",
            "}",
            "",
        ])

        if string_table_size:
            ir.extend([
                "",
                "",
                "define i64 @__nq_input_str_slot(i64 %slot) {",
                "entry:",
                "  %slot_neg = icmp slt i64 %slot, 0",
                "  br i1 %slot_neg, label %bad, label %range",
                "range:",
                f"  %too_high = icmp uge i64 %slot, {string_table_size}",
                "  br i1 %too_high, label %bad, label %load",
                "load:",
                f"  %ptr_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %slot",
                "  %ptr = load ptr, ptr %ptr_slot",
                "  %is_null = icmp eq ptr %ptr, null",
                "  br i1 %is_null, label %bad, label %read",
                "read:",
                "  %stdin_ptr = load ptr, ptr @stdin",
                "  %read_result = call ptr @fgets(ptr %ptr, i32 256, ptr %stdin_ptr)",
                "  %is_eof = icmp eq ptr %read_result, null",
                "  br i1 %is_eof, label %empty, label %scan",
                "empty:",
                "  store i8 0, ptr %ptr",
                f"  %empty_len_slot = getelementptr [{string_table_size} x i64], ptr @str_lens, i64 0, i64 %slot",
                "  store i64 0, ptr %empty_len_slot",
                "  ret i64 %slot",
                "scan:",
                "  br label %loop",
                "loop:",
                "  %idx = phi i64 [ 0, %scan ], [ %next_idx, %next ]",
                "  %char_ptr = getelementptr i8, ptr %ptr, i64 %idx",
                "  %char = load i8, ptr %char_ptr",
                "  %is_zero = icmp eq i8 %char, 0",
                "  br i1 %is_zero, label %store_len, label %check_newline",
                "check_newline:",
                "  %is_newline = icmp eq i8 %char, 10",
                "  br i1 %is_newline, label %trim, label %next",
                "trim:",
                "  store i8 0, ptr %char_ptr",
                "  br label %store_len",
                "next:",
                "  %next_idx = add i64 %idx, 1",
                "  br label %loop",
                "store_len:",
                f"  %len_slot = getelementptr [{string_table_size} x i64], ptr @str_lens, i64 0, i64 %slot",
                "  store i64 %idx, ptr %len_slot",
                "  ret i64 %slot",
                "bad:",
                "  %bad_msg = getelementptr [18 x i8], ptr @.bad_str, i64 0, i64 0",
                "  call i32 @puts(ptr %bad_msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "}",
                "",
                "define i64 @__nq_int_to_str_slot(i64 %slot, i64 %value) {",
                "entry:",
                "  %slot_neg = icmp slt i64 %slot, 0",
                "  br i1 %slot_neg, label %bad, label %range",
                "range:",
                f"  %too_high = icmp uge i64 %slot, {string_table_size}",
                "  br i1 %too_high, label %bad, label %load",
                "load:",
                f"  %ptr_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %slot",
                "  %ptr = load ptr, ptr %ptr_slot",
                "  %is_null = icmp eq ptr %ptr, null",
                "  br i1 %is_null, label %bad, label %format",
                "format:",
                "  %fmt = getelementptr [5 x i8], ptr @.fmt_d, i64 0, i64 0",
                "  %written32 = call i32 (ptr, i64, ptr, ...) @snprintf(ptr %ptr, i64 32, ptr %fmt, i64 %value)",
                "  %written_bad = icmp slt i32 %written32, 0",
                "  br i1 %written_bad, label %fail, label %len",
                "len:",
                "  %written = sext i32 %written32 to i64",
                "  %too_long = icmp sge i64 %written, 32",
                "  br i1 %too_long, label %fail, label %store_len",
                "store_len:",
                f"  %len_slot = getelementptr [{string_table_size} x i64], ptr @str_lens, i64 0, i64 %slot",
                "  store i64 %written, ptr %len_slot",
                "  ret i64 %slot",
                "bad:",
                "  %bad_msg = getelementptr [18 x i8], ptr @.bad_str, i64 0, i64 0",
                "  call i32 @puts(ptr %bad_msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "fail:",
                "  %fail_msg = getelementptr [21 x i8], ptr @.its_fail, i64 0, i64 0",
                "  call i32 @puts(ptr %fail_msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "}",
                "",
                "define void @__nq_print_str_id(i64 %id) {",
                "entry:",
                "  %neg = icmp slt i64 %id, 0",
                "  br i1 %neg, label %bad, label %range",
                "range:",
                f"  %too_high = icmp uge i64 %id, {string_table_size}",
                "  br i1 %too_high, label %bad, label %load",
                "load:",
                f"  %slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %id",
                "  %ptr = load ptr, ptr %slot",
                "  %is_null = icmp eq ptr %ptr, null",
                "  br i1 %is_null, label %bad, label %print",
                "print:",
                "  %fmt = getelementptr [4 x i8], ptr @.strfmt, i64 0, i64 0",
                "  call i32 (ptr, ...) @printf(ptr %fmt, ptr %ptr)",
                "  ret void",
                "bad:",
                "  %msg = getelementptr [18 x i8], ptr @.bad_str, i64 0, i64 0",
                "  call i32 @puts(ptr %msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "}",
                "",
                "define i64 @__nq_str_len_id(i64 %id) {",
                "entry:",
                "  %neg = icmp slt i64 %id, 0",
                "  br i1 %neg, label %bad, label %range",
                "range:",
                f"  %too_high = icmp uge i64 %id, {string_table_size}",
                "  br i1 %too_high, label %bad, label %load",
                "load:",
                f"  %ptr_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %id",
                "  %ptr = load ptr, ptr %ptr_slot",
                "  %is_null = icmp eq ptr %ptr, null",
                "  br i1 %is_null, label %bad, label %ok",
                "ok:",
                f"  %len_slot = getelementptr [{string_table_size} x i64], ptr @str_lens, i64 0, i64 %id",
                "  %len = load i64, ptr %len_slot",
                "  ret i64 %len",
                "bad:",
                "  %msg = getelementptr [18 x i8], ptr @.bad_str, i64 0, i64 0",
                "  call i32 @puts(ptr %msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "}",
                "",
                "define i64 @__nq_str_concat_slot(i64 %dst, i64 %left, i64 %right) {",
                "entry:",
                "  %dst_neg = icmp slt i64 %dst, 0",
                "  br i1 %dst_neg, label %bad, label %left_check",
                "left_check:",
                "  %left_neg = icmp slt i64 %left, 0",
                "  br i1 %left_neg, label %bad, label %right_check",
                "right_check:",
                "  %right_neg = icmp slt i64 %right, 0",
                "  br i1 %right_neg, label %bad, label %range",
                "range:",
                f"  %dst_high = icmp uge i64 %dst, {string_table_size}",
                f"  %left_high = icmp uge i64 %left, {string_table_size}",
                f"  %right_high = icmp uge i64 %right, {string_table_size}",
                "  %range_a = or i1 %dst_high, %left_high",
                "  %range_bad = or i1 %range_a, %right_high",
                "  br i1 %range_bad, label %bad, label %load",
                "load:",
                f"  %dst_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %dst",
                f"  %left_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %left",
                f"  %right_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %right",
                "  %dst_ptr = load ptr, ptr %dst_slot",
                "  %left_ptr = load ptr, ptr %left_slot",
                "  %right_ptr = load ptr, ptr %right_slot",
                "  %dst_null = icmp eq ptr %dst_ptr, null",
                "  %left_null = icmp eq ptr %left_ptr, null",
                "  %right_null = icmp eq ptr %right_ptr, null",
                "  %null_a = or i1 %dst_null, %left_null",
                "  %null_bad = or i1 %null_a, %right_null",
                "  br i1 %null_bad, label %bad, label %lengths",
                "lengths:",
                f"  %left_len_slot = getelementptr [{string_table_size} x i64], ptr @str_lens, i64 0, i64 %left",
                f"  %right_len_slot = getelementptr [{string_table_size} x i64], ptr @str_lens, i64 0, i64 %right",
                "  %left_len = load i64, ptr %left_len_slot",
                "  %right_len = load i64, ptr %right_len_slot",
                "  %total = add i64 %left_len, %right_len",
                "  %too_long = icmp uge i64 %total, 4095",
                "  br i1 %too_long, label %overflow, label %copy",
                "copy:",
                "  call void @llvm.memcpy.p0.p0.i64(ptr %dst_ptr, ptr %left_ptr, i64 %left_len, i1 false)",
                "  %right_dst = getelementptr i8, ptr %dst_ptr, i64 %left_len",
                "  call void @llvm.memcpy.p0.p0.i64(ptr %right_dst, ptr %right_ptr, i64 %right_len, i1 false)",
                "  %term = getelementptr i8, ptr %dst_ptr, i64 %total",
                "  store i8 0, ptr %term",
                f"  %dst_len_slot = getelementptr [{string_table_size} x i64], ptr @str_lens, i64 0, i64 %dst",
                "  store i64 %total, ptr %dst_len_slot",
                "  ret i64 %dst",
                "bad:",
                "  %bad_msg = getelementptr [18 x i8], ptr @.bad_str, i64 0, i64 0",
                "  call i32 @puts(ptr %bad_msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "overflow:",
                "  %ovf_msg = getelementptr [23 x i8], ptr @.strcat_ovf, i64 0, i64 0",
                "  call i32 @puts(ptr %ovf_msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "}",
                "",
                "define i64 @__nq_str_to_int_id(i64 %id) {",
                "entry:",
                "  %id_neg = icmp slt i64 %id, 0",
                "  br i1 %id_neg, label %bad, label %range",
                "range:",
                f"  %id_high = icmp uge i64 %id, {string_table_size}",
                "  br i1 %id_high, label %bad, label %load",
                "load:",
                f"  %ptr_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %id",
                "  %ptr = load ptr, ptr %ptr_slot",
                "  %is_null = icmp eq ptr %ptr, null",
                "  br i1 %is_null, label %bad, label %sign_check",
                "sign_check:",
                "  %first = load i8, ptr %ptr",
                "  %is_minus = icmp eq i8 %first, 45",
                "  %start = select i1 %is_minus, i64 1, i64 0",
                "  br label %loop",
                "loop:",
                "  %idx = phi i64 [ %start, %sign_check ], [ %next_idx, %digit ]",
                "  %acc = phi i64 [ 0, %sign_check ], [ %next_acc, %digit ]",
                "  %char_ptr = getelementptr i8, ptr %ptr, i64 %idx",
                "  %char = load i8, ptr %char_ptr",
                "  %is_zero = icmp eq i8 %char, 0",
                "  br i1 %is_zero, label %finish, label %digit_check",
                "digit_check:",
                "  %below = icmp ult i8 %char, 48",
                "  %above = icmp ugt i8 %char, 57",
                "  %not_digit = or i1 %below, %above",
                "  br i1 %not_digit, label %finish, label %digit",
                "digit:",
                "  %digit_i8 = sub i8 %char, 48",
                "  %digit_i64 = zext i8 %digit_i8 to i64",
                "  %scaled = mul i64 %acc, 10",
                "  %next_acc = add i64 %scaled, %digit_i64",
                "  %next_idx = add i64 %idx, 1",
                "  br label %loop",
                "finish:",
                "  %neg_acc = sub i64 0, %acc",
                "  %result = select i1 %is_minus, i64 %neg_acc, i64 %acc",
                "  ret i64 %result",
                "bad:",
                "  %msg = getelementptr [18 x i8], ptr @.bad_str, i64 0, i64 0",
                "  call i32 @puts(ptr %msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "}",
                "",
                "define i64 @__nq_str_at_id(i64 %id, i64 %index) {",
                "entry:",
                "  %id_neg = icmp slt i64 %id, 0",
                "  br i1 %id_neg, label %bad_handle, label %range",
                "range:",
                f"  %id_high = icmp uge i64 %id, {string_table_size}",
                "  br i1 %id_high, label %bad_handle, label %load",
                "load:",
                f"  %ptr_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %id",
                "  %ptr = load ptr, ptr %ptr_slot",
                "  %is_null = icmp eq ptr %ptr, null",
                "  br i1 %is_null, label %bad_handle, label %index_check",
                "index_check:",
                "  %index_neg = icmp slt i64 %index, 0",
                "  br i1 %index_neg, label %oob, label %len_check",
                "len_check:",
                f"  %len_slot = getelementptr [{string_table_size} x i64], ptr @str_lens, i64 0, i64 %id",
                "  %len = load i64, ptr %len_slot",
                "  %too_high = icmp sge i64 %index, %len",
                "  br i1 %too_high, label %oob, label %char_load",
                "char_load:",
                "  %char_ptr = getelementptr i8, ptr %ptr, i64 %index",
                "  %byte = load i8, ptr %char_ptr",
                "  %result = zext i8 %byte to i64",
                "  ret i64 %result",
                "bad_handle:",
                "  %bad_msg = getelementptr [18 x i8], ptr @.bad_str, i64 0, i64 0",
                "  call i32 @puts(ptr %bad_msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "oob:",
                "  %oob_msg = getelementptr [27 x i8], ptr @.str_oob, i64 0, i64 0",
                "  call i32 @puts(ptr %oob_msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "}",
                "",
                "define i64 @__nq_str_eq_id(i64 %left, i64 %right) {",
                "entry:",
                "  %left_neg = icmp slt i64 %left, 0",
                "  br i1 %left_neg, label %bad, label %left_range",
                "left_range:",
                f"  %left_high = icmp uge i64 %left, {string_table_size}",
                "  br i1 %left_high, label %bad, label %left_load",
                "left_load:",
                f"  %left_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %left",
                "  %left_ptr = load ptr, ptr %left_slot",
                "  %left_null = icmp eq ptr %left_ptr, null",
                "  br i1 %left_null, label %bad, label %right_check",
                "right_check:",
                "  %right_neg = icmp slt i64 %right, 0",
                "  br i1 %right_neg, label %bad, label %right_range",
                "right_range:",
                f"  %right_high = icmp uge i64 %right, {string_table_size}",
                "  br i1 %right_high, label %bad, label %right_load",
                "right_load:",
                f"  %right_slot = getelementptr [{string_table_size} x ptr], ptr @str_ptrs, i64 0, i64 %right",
                "  %right_ptr = load ptr, ptr %right_slot",
                "  %right_null = icmp eq ptr %right_ptr, null",
                "  br i1 %right_null, label %bad, label %compare",
                "compare:",
                "  %cmp = call i32 @strcmp(ptr %left_ptr, ptr %right_ptr)",
                "  %is_eq = icmp eq i32 %cmp, 0",
                "  %result = zext i1 %is_eq to i64",
                "  ret i64 %result",
                "bad:",
                "  %msg = getelementptr [18 x i8], ptr @.bad_str, i64 0, i64 0",
                "  call i32 @puts(ptr %msg)",
                "  call void @exit(i32 1)",
                "  unreachable",
                "}",
                "",
            ])

        for name, body in functions:
            self.active_context = f"function '{name}'"
            blocks, param_count, terminated, local_slots, for_slots, mutable_param_slots = self.lower_block(body, in_function=True)
            if not terminated:
                if body:
                    raise self.error_at(body[-1], f"function '{name}' does not terminate in the supported bridge subset")
                raise LowerError(f"function '{name}' does not terminate in the supported bridge subset")
            params = ", ".join(f"i64 %arg{i}" for i in range(param_count))
            ir.append(f"define i64 @{name}({params}) {{")
            for idx, (block_name, lines) in enumerate(blocks):
                ir.append(f"{block_name}:")
                if block_name == "entry":
                    for slot in local_slots:
                        ir.append(f"  %local_{slot} = alloca i64")
                    for slot in for_slots:
                        ir.append(f"  %forend_{slot} = alloca i64")
                    for slot in mutable_param_slots:
                        arg_index = param_count - 1 - ((slot - 16) // 8)
                        ir.append(f"  %pmut_{slot} = alloca i64")
                        ir.append(f"  store i64 %arg{arg_index}, ptr %pmut_{slot}")
                ir.extend(lines)
                if idx == len(blocks) - 1 and not lines and terminated:
                    ir.append("  unreachable")
            ir.append("}")
            ir.append("")

        self.active_context = "main"
        blocks, _, terminated, local_slots, for_slots, _ = self.lower_block(main, in_function=False)
        ir.append("define i32 @main(i32 %argc32, ptr %argv) {")
        for idx, (block_name, lines) in enumerate(blocks):
            ir.append(f"{block_name}:")
            if block_name == "entry":
                ir.append("  %argc64_raw = sext i32 %argc32 to i64")
                ir.append("  %argc64 = sub i64 %argc64_raw, 1")
                ir.append("  store i64 %argc64, ptr @nq_argc")
                ir.append("  %argv_user = getelementptr ptr, ptr %argv, i64 1")
                ir.append("  store ptr %argv_user, ptr @nq_argv")
                for slot in local_slots:
                    ir.append(f"  %local_{slot} = alloca i64")
                for slot in for_slots:
                    ir.append(f"  %forend_{slot} = alloca i64")
            ir.extend(lines)
            if idx == len(blocks) - 1 and (not terminated or not lines):
                ir.append("  ret i32 0")
        ir.append("}")
        ir.append("")
        self.active_context = None
        return "\n".join(ir)

    def unsupported_op_error(self, item):
        op = item["op"]
        detail = self.unsupported_groups.get(op)
        if detail is None:
            return self.error_at(item, f"unsupported op {op}")
        return self.error_at(
            item,
            f"unsupported op {op} ({detail}); this feature should stay on the nasm backend or wait for further IR-bridge support",
        )


def main(argv):
    if len(argv) != 3:
        print("usage: nq_ir_json_to_llvm.py <input.json> <output.ll>", file=sys.stderr)
        return 1

    input_path, output_path = argv[1], argv[2]
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        llvm_ir = Lowerer(items).lower()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(llvm_ir)
    except (OSError, json.JSONDecodeError, LowerError) as exc:
        print(f"[nq-ir-llvm] Error: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {output_path} written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
