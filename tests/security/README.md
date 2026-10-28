# Canonical native boundary assurance

## Defined-program differential gate

`make test` and `make bootstrap-test` also run
`test_compiler_differential.py`, a separate finite wrong-code detector:

```sh
python3 -B -W error::ResourceWarning tests/security/test_compiler_differential.py -v
```

The host-only `differential_oracle.py` builds 48 bounded valid source programs:
40 seeded arithmetic/comparison combinations and eight exact i64 edge values.
They combine six mutable parameters, outer/inner local shadowing, forward and
nested calls, nested terminating loops, and left-to-right byte-memory effects.
Both runtime profiles must match an independent Python arithmetic model, exact
stdout bytes, empty stderr and exit status. A sign plus eight quotient bytes
observes the full signed result, including MIN/MAX, rather than only Linux's
low exit byte. The Python expectation uses magnitude byte encoding instead of
interpreting the compiler's AST or emitted instructions. Signed division follows
truncation toward zero, with explicit oracle overflow/division controls.

The complete gate requires 96 matching profile/program pairs and two real
negative controls. Those controls compile deliberately changed **valid source**
to prove independent detection of altered exit status and altered stdout. They
are expected sensitivity mismatches, not reported compiler defects. Compile
errors, signals, timeouts and supervisor failures cannot count as those controls.
No arbitrary mutated source, wire or ELF is executed.

`NQL_DIFFERENTIAL_OUTPUT` may name a new evidence directory; otherwise a unique
directory is created below `TMPDIR`. It retains all source/model/expected bytes,
294 supervised invocations for a successful complete run, generated executables,
streams, compiler/pin/helper identities and `summary.json`. Only a completed
successful full unittest process with unchanged inputs and full corpus counts
publishes `passed: true`. Discovery/selected-method runs retain invocation files
but do not independently publish that full-gate summary.

The existing supervisor supplies a 600-second total budget, five seconds per
invocation, 8 MiB per stream and 3 MiB input bound. These are host test budgets,
not language limits or compiler performance claims. Python is an independent
host oracle and QEMU is an execution adapter off x86_64; neither enters canonical
semantic compilation. This is finite generated-program differential testing,
not coverage-guided fuzzing, a memory sanitizer, an RSS cap, optimizer comparison
or proof of absence of miscompilation. Existing native-boundary assurance and
historical signal/retention limits below remain separate.

## Native-boundary mutation profile

This host-only profile supplements the existing canonical compiler tests. It
does not supply language semantics or enter the bootstrap chain. Its scope is
the experimental C0.32 source/NQAF6/native boundary, not a repository-wide audit
or a claim of complete NolQu-L Safety. The language contract is
[NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md).

## Run and evidence

Run from the repository root on Linux, with Python 3 and an executable pinned
frontend/backend pair. Non-x86_64 hosts also need `qemu-x86_64`. Missing execution
support fails the profile instead of skipping it.

```sh
python3 -B -W error::ResourceWarning tests/security/test_bounded_runner.py -v
NQL_ASSURANCE_OUTPUT=/tmp/nql-assurance-NEW-DIRECTORY \
  python3 -B -W error::ResourceWarning tests/security/test_native_assurance.py -v
```

The output directory must not exist. With no environment setting, the test
creates a unique directory and prints its path. It retains the exact corpus,
every input/stdout/stderr, invocation status/PID/time/hash, and `summary.json`.
It never retries a compiler failure. Failure evidence is retained too. Retention
has no formal numeric period; copy valuable failures into maintained evidence
before clearing temporary storage.

Corpus `native-boundary-v1.json` has twelve valid/invalid sources; its SHA-256 is
`1f30672e7085104130363f346c4b07f069306fb7f2f1a6ce62da0162db516bee`.
The mutation seed is `0x4e514c32`. Sorted mutations and corpus order make inputs
reproducible; temporary names, PIDs and timings are not deterministic outputs.
The summary binds source, installed seed/pin identity, harness and corpus bytes.

## Test contracts

| Invariant | Actual test ID | Checked boundary and limit |
| --- | --- | --- |
| Malformed source is bounded and diagnostic; successful AST preserves source and owned graph | `NativeBoundaryAssurance.test_seed_sources_and_deterministic_mutations` | 24 corpus/profile cases and 132 deterministic insertion/deletion/bit-flip inputs; valid seeds must reach codegen, forbidden bytes must be rejected, unconstrained mutations may legitimately fail semantic validation |
| Invalid framing, reserved fields, spans and node IDs never produce an artifact | `NativeBoundaryAssurance.test_wire_framing_reserved_fields_and_spans` | 360 truncation/field/trailing-byte rejections in both profiles; diagnostic, status 1 and empty stdout required |
| Unsafe permission ends at the real source scope | `NativeBoundaryAssurance.test_safety_headers_and_scope_restoration_metamorphic` | comment/newline/brace variants; outside raw call must report exact C0S-001 location |
| Defined transformations preserve observable machine behavior | `NativeBoundaryAssurance.test_defined_pure_program_metamorphic_behavior` | 12 fixed executions: rename, grouping, untaken branch, loop, unused unsafe scope and function call; expected exit 42/stdout `NQL`/empty stderr |
| Test infrastructure cannot turn process/cleanup/setup failure into rejection PASS | eleven `BoundedRunnerTests` methods | real host children; binary status/streams, signal, timeout, output cap, acquisition cancellation, detached/reaped descendants, unrelated-child survival, setup failure/corpus preservation and interrupted-supervisor protocol controls |

Only the fixed pure oracle programs are executed. Arbitrary mutated ELF output
is never run. This is deterministic mutation testing, **LIMITED fuzzing**; no
coverage instrumentation or coverage percentage is available. Passing this
finite corpus does not prove arbitrary malformed input safe or rule out wrong
code outside the tested defined semantics.

The profile permits 5 seconds per target invocation, a 600-second total wall budget, input
up to 3 MiB, and strictly less than 8 MiB per captured output stream. Linux
`RLIMIT_FSIZE`, `RLIMIT_CPU`, disabled core dumps and session-scoped timeout
termination enforce the applicable limits. A private Linux subreaper owns this
one command's descendants and reaps them before returning/hashing streams,
including cancellation and normal leader exit. It does not adopt the unittest
process's unrelated children. This Linux test runner operates on the main
thread: SIGINT/TERM/HUP/ALRM are abort signals, deferred until handle registration
and cleanup, then surfaced as KeyboardInterrupt. Previous handlers are restored.
SIGKILL of the controller and uninterruptible kernel tasks cannot be cleaned up
by Python handlers; this is not a sandbox or universal termination guarantee.
Status and streams remain available
when a limit fires. Limits are test resource budgets, not performance promises.
No RSS limit is implemented: QEMU's virtual guest mappings are not a physical
memory budget. Compiler arena/source/token/node bounds are separately covered
by the existing capacity/runtime tests; no RSS or allocation-failure proof is
claimed here.

The original 300-second profile budget predated private-supervisor hardening.
With supervision it exhausted that budget after 473 target invocations and
238/360 wire rejections; the final invocation received only 0.067 seconds of
remaining budget. The failed run is retained. Extrapolating the observed rate
requires about 377 seconds for 594 invocations, so 600 seconds provides explicit
host-time headroom. Per-process limits, corpus, cases and expected compiler
outcomes are unchanged. This is a measured host-test budget correction, not a
retry accepted as a fix for the separate unexplained bootstrap SIGKILL.

## Layered coverage and gaps

| Area | Existing or supplemental evidence | Scope remaining |
| --- | --- | --- |
| Lexer/parser | source corpus/mutations, `test_c0_native_frontend.py`, existing capacity/frontend suites | coverage-guided fuzzing unavailable; Unicode identifiers unsupported |
| Semantic/Safety | source-scope test above; `test_c0_native_backend.py` tests independent containment, arity and global shadow resolution | full type/ownership/lifetime/Safe-mode verification not implemented; invariant comments are not proofs |
| Serialization/codegen/ABI | wire test above; actual six-register mmap, callee-save, call alignment and both runtime profiles in `test_c0_native_runtime.py` | no alternate ISA qualification |
| Wrong code | independent fixed expected bytes/status above; frozen predecessor byte parity and real B/C named oracles | no canonical optimizer exists to compare optimization modes |
| CLI/files/processes | existing `test_canonical_cli.py`, `test_canonical_project.py`, MCP permission/publication/process tests | no new CLI sandbox or remote-service deployment is assumed |
| Runtime/resource | existing raw return/error, descriptor-zero, short-write/EINTR, close-once and mapped-arena cleanup tests | arbitrary raw syscall arguments remain the programmer's responsibility; no allocation fault-pressure campaign |
| Bootstrap | B0 rebuilds/pins, actual complete-source B==C and fail-closed MCP receipt consumer | component equality is not Full Compiler or full-language self-hosting |
| Dependencies/artifacts | unchanged canonical predecessor/hash checks; recorded host tool identities | no dependency-advisory rescan, signing, SBOM or provenance implementation was added |

ASan/UBSan/MSan instrumentation is **UNSUPPORTED for this direct NolQu-L machine
code path**: there is no matching compiler instrumentation. TSan is not an
applicable generated-runtime check for this single-threaded subset. Host Python
tests run with `ResourceWarning` as an error; that is not a memory sanitizer.
The host runner additionally uses existing Linux procfs/prctl through Python's
standard-library ctypes; missing supervisor support fails closed. No new Clang,
LLVM, C, Rust or other semantic build dependency is introduced.

## Profiles and release decision

- **PR/manual:** the two commands above plus impacted existing suites. This
  profile has been run locally; it is not wired into the compiler main gate or
  scheduled CI. The existing native regression remains in `make test`.
- **Extended/scheduled:** coverage-guided fuzzing, persistent-corpus expansion,
  allocation/resource-pressure testing and dependency advisory scans are
  **NOT RUN / NOT IMPLEMENTED** for this addition. No schedule is claimed.
- **Release:** the profile alone cannot qualify a release. Full applicable
  compiler/ABI/bootstrap gates, unresolved incident review, dependency review,
  artifact integrity and documented residual risks must also be resolved.

One earlier full main run observed a frozen C0.30 comparison backend receiving
SIGKILL while the candidate compilation succeeded. A serial run on identical
inputs later passed. The signal sender/cause was not retained, so the incident
is **OPEN**, not fixed or quarantined; no OOM attribution is established. Local
passing results do not remove this stable-release blocker. Overall readiness
remains **PARTIAL / NOT READY** for stable or security-qualified promotion.
