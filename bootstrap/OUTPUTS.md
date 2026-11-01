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

All eight bootstrap shell gates that inspect stack permissions use the shared
wide-report permission parser in `tests/shared/lib.sh`. It requires the relevant program header, validates
its numeric fields and alignment, and checks every combined or split flag
field. Every GNU_STACK row must lack execute permission; a safe later row
cannot erase an unsafe earlier row. Zero permission bits are valid. The Core
no-RWX LOAD check uses the same parser and rejects write plus execute across
separate fields, while its existing exact RX/RW layout checks remain in place.

EI04 checks that every stack gate uses this contract. EI07/EI09 cover missing,
malformed, combined/split, duplicate and zero-permission rows and hexadecimal
addresses containing E. EI08 feeds unsafe/missing/malformed stack reports
through the real foundation gate. EI05 preserves Python paths containing
spaces; EI06 checks owned process-group cleanup on suite timeout.

MCP `verify_elf_properties` reads ELF identification/class/endianness/machine
bytes instead of using the pathname-bearing `file` text as target evidence.
Both `file` and `readelf` must finish successfully with complete stdout and
stderr. Failed, timed-out, cancelled or truncated inspections cannot qualify.
`verify_no_host_dependency` also requires a complete dynamic-section report.
The additive `inspection_complete` result field distinguishes a completed
inspection from an inconclusive one; `ok` and positive absence claims fail
closed when it is false. Existing valid canonical artifacts remain accepted.
Previously misqualified artifacts must be rebuilt or corrected before retrying.

The MCP ELF01--ELF06 regressions inspect non-executed copies of a canonical
ELF, including all eight permission-bit combinations and an AArch64 header
with a misleading x86-64 filename. Controlled reports cover malformed and
incomplete inspections. The real MCP checksum workflow separately verifies
its generated artifact through the same public inspection tool.

These host checks establish the stated target/linkage/stack properties of the
inspected artifact, not semantic compiler provenance, safe behavior of arbitrary
machine code, or isolation against an artifact changed concurrently by the
same user. Canonical seed bytes, pins and bootstrap topology are unchanged.
