# Bootstrap host-wrapper output contract

The machine, Stage 0, B0, C0 emitter and bounded-successor materializers, and
C0 stream compile adapter, reject an output that aliases a consumed input.
Protection includes source, hash manifest, executing wrapper and predecessor
seed; the successor also protects its compiler adapter and that adapter's seed
and pin. Direct paths, symbolic links, parent-directory aliases and real hard
links are compared by file identity. Rebuilding the stage's own seed remains
supported and must produce the pinned bytes.

Validation runs before reconstruction/compilation and again after candidate
chmod, immediately before publication. Output directories are rejected;
`mv -fT --` publishes to an exact destination, so a directory appearing at the
rename step cannot receive a hidden temporary executable. Failure removes the
candidate and preserves protected inputs. Materializers accept zero or one
output argument; the stream adapter requires exactly input and output.

These Bash wrappers are host file-policy tools, outside the semantic compiler
chain. The caller supplies the output under its existing filesystem privileges.
Hash verification establishes candidate identity; it does not authorize the
rename destination. This is not filesystem isolation against a user controlling
the installation directory or arbitrary concurrent parent-directory changes.
No new canonical build/runtime dependency, source grammar or binary ABI is
introduced.

## Executable invariants

- MO01/MO02: protected inputs and their observed aliases cannot be output;
  input bytes and modes survive rejection.
- MO03: default and independent rebuilds retain the exact pinned bytes.
- MO04/MO05: destination rechecks, exact rename and cleanup reject controlled
  late alias/directory replacement.
- MO06: excess arguments cannot publish output.
- MO07: real hard-link aliases are rejected on the qualified Linux filesystem.

`tests/bootstrap/test_materializer_outputs.py` provides these copied-installation
regressions. The portable methods run in the main bootstrap gate. Linux
qualification separately requires MO07 with real hard links; Android hard-link
denial does not become a passing skip or a substitute identity test.

## ELF host inspection

Bootstrap tests consume complete `readelf` header/program reports before
searching them. Inspector failures fail closed. Searching a live producer with
`grep -q` under `pipefail` can both reject a valid header after broken pipe and
hide a forbidden interpreter behind the producer's nonzero exit. EI01/EI02/EI03
in `tests/bootstrap/test_elf_inspection.py` exercise long reports, forbidden
interpreter detection and controlled inspector failure through the real
foundation test gate. Inspector shims are test dependencies, not compilers or
canonical build inputs.

EI04 exercises the four actual Core GNU_STACK predicates with RW, RWE and
missing-stack reports. The final awk decision preserves a detected execute
permission; an END block must not overwrite the earlier failure with success.
