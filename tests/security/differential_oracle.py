"""Finite host oracle for defined C0 scalar programs, independent of codegen.

No compiler code, AST decoder or emitted instruction is used to calculate the
expected results. This is not a canonical build dependency or general fuzzer.
"""
from dataclasses import dataclass
import operator
import random

I64_MIN = -(1 << 63)
I64_MAX = (1 << 63) - 1
SEED = 0x4E514C44
OPERATORS = ('+', '-', '*', '/', '<', '<=', '>', '>=', '==', '!=')
VARIABLES = ('a', 'b', 'c', 'd', 'e', 'f', 'snapshot')
COMPARISONS = {'<': operator.lt, '<=': operator.le, '>': operator.gt,
               '>=': operator.ge, '==': operator.eq, '!=': operator.ne}


def evaluate(expression, environment):
    if isinstance(expression, int):
        value = expression
    elif isinstance(expression, str):
        value = environment[expression]
    else:
        operation, left, right = expression
        a, b = evaluate(left, environment), evaluate(right, environment)
        if operation in COMPARISONS:
            return int(COMPARISONS[operation](a, b))
        if operation == '+':
            value = a + b
        elif operation == '-':
            value = a - b
        elif operation == '*':
            value = a * b
        elif operation == '/':
            # Python // floors negatives; C0 signed division truncates to zero.
            magnitude = abs(a) // abs(b)
            value = -magnitude if (a < 0) != (b < 0) else magnitude
        else:
            raise ValueError('unknown oracle operation: ' + operation)
    if not I64_MIN <= value <= I64_MAX:
        raise OverflowError('oracle expression is outside defined i64 arithmetic')
    return value


def number(value):
    if value == I64_MIN:
        return '(0-9223372036854775807-1)'
    return str(value) if value >= 0 else '(0-' + str(-value) + ')'


def render(expression):
    if isinstance(expression, int):
        return number(expression)
    if isinstance(expression, str):
        return expression
    operation, left, right = expression
    return '(' + render(left) + operation + render(right) + ')'


def signature(value):
    # The target repeatedly stores q's low byte, then divides q by256 toward0.
    # Compute the independent expectation from Python's magnitude byte encoding.
    magnitude = abs(value).to_bytes(8, 'little')
    digits = bytes((-byte) & 255 for byte in magnitude) if value < 0 else magnitude
    return bytes([int(value < 0)]) + digits


def expression(rng, depth):
    if not depth:
        return rng.choice(VARIABLES) if rng.randrange(2) else rng.randrange(-15, 16)
    operation = rng.choice(OPERATORS)
    right = rng.choice((-7, -3, -1, 1, 3, 7)) if operation == '/' else expression(rng, depth - 1)
    return operation, expression(rng, depth - 1), right


@dataclass(frozen=True)
class Case:
    identifier: str
    source: bytes
    expected_stdout: bytes
    expected_exit: int
    model: dict


def make_case(ordinal, body, operation):
    rng = random.Random(SEED + ordinal)
    rounds = ordinal % 4 + 1
    initial = rng.randrange(256)
    offsets = [rng.randrange(-15, 16) for _ in range(6)]
    constants = [rng.randrange(-15, 16) for _ in range(6)]
    trace, results, output = [], [], bytearray()
    returned = body if operation == 'i64-edge' else ('+', body, 'snapshot')

    def tap(value):
        byte = value & 255
        trace.append(byte)
        return byte

    def mix(arguments):
        # A fresh lexical frame per call. The outer snapshot remains unchanged
        # when the branch introduces a different binding with the same name.
        frame = dict(zip(('a', 'b', 'c', 'd', 'e', 'f'), arguments))
        frame['snapshot'] = frame['a'] + frame['b']
        frame['a'] += frame['d']
        if frame['c'] < frame['e']:
            inner_snapshot = frame['b'] + frame['e']
            frame['b'] = inner_snapshot - frame['f']
        else:
            frame['b'] -= frame['e']
        return evaluate(returned, frame)

    value = initial
    for step in range(rounds):
        arguments = [tap(value + offsets[0]), tap(step + offsets[1])]
        nested = mix([tap(item + step) for item in constants])
        arguments.append(tap(nested))
        arguments.extend(tap(item + step) for item in offsets[3:])
        result = mix(arguments)
        results.append(result)
        output.extend(signature(result))
        value = result & 255
    assert len(trace) == 12 * rounds and len(trace) <= 48
    output.extend(bytes([len(trace), *trace]))

    tap_source = '''fn tap(value){
let position=byte_load(0)+1
byte_store(position,value)
byte_store(0,position)
return byte_load(position)
}
'''
    mix_source = '''fn mix6(a,b,c,d,e,f){
let snapshot=a+b
a=a+d
if c<e{let snapshot=b+e b=snapshot-f}else{b=b-e}
return ''' + render(returned) + '''
}
'''
    inner = 'mix6(' + ','.join('tap(' + number(item) + '+step)' for item in constants) + ')'
    arguments = ['tap(value+' + number(offsets[0]) + ')',
                 'tap(step+' + number(offsets[1]) + ')', 'tap(' + inner + ')']
    arguments += ['tap(step+' + number(item) + ')' for item in offsets[3:]]
    main_source = '''fn main(){
let value=''' + str(initial) + '''
let step=0
while step<''' + str(rounds) + '''{
let result=mix6(''' + ','.join(arguments) + ''')
byte_store(64,result<0)
let quotient=result
let digit=0
while digit<8{
byte_store(65+digit,quotient)
quotient=quotient/256
digit=digit+1
}
output_write(64,9)
byte_store(90,result)
value=byte_load(90)
step=step+1
}
output_write(0,byte_load(0)+1)
return value
}
'''
    functions = [main_source, tap_source, mix_source]
    shift = ordinal % 3
    source = ''.join(functions[shift:] + functions[:shift]).encode('ascii')
    return Case(f'case-{ordinal:02d}', source, bytes(output), value,
                dict(seed=SEED + ordinal, expression=body, operator=operation,
                     rounds=rounds, initial=initial, offsets=offsets,
                     nested_arguments=constants, trace_bytes=len(trace), results=results))


def corpus():
    cases = []
    for ordinal in range(40):
        rng = random.Random(SEED ^ ordinal)
        operation = OPERATORS[ordinal % len(OPERATORS)]
        right = rng.choice((-7, -3, -1, 1, 3, 7)) if operation == '/' else expression(rng, 1)
        body = operation, expression(rng, 1), right
        cases.append(make_case(ordinal, body, operation))
    # Pure edge returns exercise the exact MIN/MAX and upper bytes without
    # changing them by the ordinary generated fixture's snapshot addition.
    edges = (I64_MIN, I64_MIN + 1, I64_MAX, I64_MAX - 1,
             1 << 32, -(1 << 32), (1 << 48) + 65537, -((1 << 48) + 65537))
    for ordinal, edge in enumerate(edges, 40):
        cases.append(make_case(ordinal, edge, 'i64-edge'))
    return tuple(cases)
