# NolQu-L C0.32 — laporan pengembangan 2026-10-25

Kemampuan native OS eksperimental telah diimplementasikan, ditinjau, dan
diintegrasikan pada worktree terisolasi. Penutupan bukti diperbarui pada
2026-10-26; waktu dan identitas setiap run sebelumnya tetap dipertahankan.
Gate yang terdampak perbaikan diagnostic terakhir lulus, termasuk actual
component generations dan profil assurance. Full main yang lulus berasal dari
checkpoint sebelum patch formatter; full main belum dijalankan ulang pada
checkpoint laporan ini. [Kelanjutan reliability](C032_RELIABILITY_REPORT.md)
kemudian menyelesaikan baseline1079 dan revisi host observer1080 dengan semua
label baseline dipertahankan. Bukti historis di bawah tetap dipertahankan.
**Kesiapan stable/security: BELUM SIAP.** Satu kejadian SIGKILL pada backend
pembanding lama belum dapat dijelaskan; run berikutnya yang lulus bukan fix.
Tidak ada rilis, perubahan versi publik, commit, push, atau merge.

## 0. Update classification dan release impact

```text
Requested Mode: pengembangan menyeluruh; lanjutkan hasil nyata
Actual Update Class: Major C0.32 + Minor assurance + Patch diagnostic formatter
Risk Level: HIGH
Primary Scope: native OS interface canonical dan assurance berbatas
Affected Subsystems: frontend, NQAF, backend/runtime, bootstrap artifacts,
                     utility, public acceptance, MCP proof, test, dokumentasi
Public Contract Impact: additive experimental; CLI/default/stable ABI dipertahankan
Bootstrap Impact: pin dua komponen berubah; predecessor/topology dipertahankan
Security/Trust Impact: explicit unsafe boundary dan validasi/proof independen;
                       tidak memperkenalkan sandbox atau full Safety
Compatibility Impact: legacy source/AST/ELF corpus dipertahankan
Version Impact: milestone komponen C0.32; VERSION1.0.2a1/CHANNELdev tetap
Release Maturity: DEVELOPMENT; fitur EXPERIMENTAL
RFC Required: substantive design review dipenuhi oleh spesifikasi tertulis;
              tidak ada nomor/approval RFC publik yang dikarang
ADR Required: keputusan internal dicatat dalam spesifikasi dan NATIVE_OS.md
Migration Required: pasangan frontend/backend/pin harus dipasang bersama;
                    tidak ada migrasi source pengguna lama
Changelog Required: YES; Unreleased diperbarui
Rollback/Revert Required: tersedia; tidak dijalankan tanpa bukti source defect
Release Blocking Issues: C032-SIGNAL-01 OPEN; kualifikasi stable/security belum lengkap
Release Performed: NO
Version Bump: NONE
```

Klasifikasi Major mengikuti syntax, wire, permission, runtime ABI, codegen dan
koordinasi lintas subsistem. Assurance host merupakan Minor. Audit diagnostic
kemudian menemukan bug format lokal: Patch / Repair berisiko HIGH karena pin
backend canonical ikut berubah. Penutupan dokumentasi ini tidak mengubah code,
pin, kontrak atau klasifikasi keseluruhan menjadi update kecil. Ukuran diff
bukan dasar versi.
Rencana sebelum implementasi: [design](../superpowers/specs/2026-10-24-canonical-native-os-design.md)
dan [implementation plan](../superpowers/plans/2026-10-24-canonical-native-os.md).

Impact matrix: syntax **MEDIUM**, semantics/Safety/frontend/backend/runtime/
bootstrap/reproducibility/security **HIGH**; tooling **MEDIUM**; source/behavior
compatibility **LOW** karena goldens lama dipertahankan; ABI internal **HIGH**,
ABI publik lama dipertahankan; standard library/module **NONE**; performance/
resource **MEDIUM** untuk biaya image/test; dokumentasi **HIGH**; migration **LOW**.
Tidak ada stable IR baru; NQAF adalah wire AST internal versioned.

## 1. Baseline test

Baseline immutable adalah worktree pada revision
`66b92a4ce9e5491e570d292fe1b0320f04ba1907` ditambah working tree yang sudah
berubah sebelum sesi. Snapshot file, bukan HEAD saja, menjadi pembanding.
Main asli `/home/Axelly/Downloads/NolquASM` tidak diedit oleh pekerjaan ini.
Implementasi akhirnya berada di `/home/Axelly/.codex/worktrees/4878/NolquASM`.

| Command baseline yang telah selesai | Passed | Failed / skipped / timeout |
| --- | ---: | --- |
| `make -k test` | 1078 marker PASS | 0 / 0 / 0 |
| interpreter MCP, `-B -m unittest discover -s tests/mcp -v` setelah fix milestone sebelumnya | 112 metode | 0 / 0 / 0 |
| `make release-check` | 9 check | 0 / 0 / 0 |

Tidak ada failure baseline terbuka saat C0.32 dimulai. Warning dependency
Pydantic `lifespan` sudah ada; bukan failure compiler. Gate beririsan, sehingga
angka di atas tidak dijumlahkan sebagai jumlah test unik. Snapshot dan log ada
di `/tmp/nql-canonical-cli-20261023.5odyvxyg`; baseline tidak diubah sesudahnya.

## 2. Baseline bootstrap

Machine Foundation, Stage0, B0, emitter C0.25, frontend/backend C0.31 dan tujuh
hash artifact sudah PASS. Full Compiler, full-language Self-Hosting `nqlc`, dan
Verified `nqlc` NOT IMPLEMENTED. Referensi manifest tetap
[`bootstrap/manifest.tsv`](../../bootstrap/manifest.tsv); R0 bukan tahap canonical.

## 3. Evaluasi kesiapan

**BELUM SIAP untuk stable/security-qualified promotion.** Kemampuan native yang
ditargetkan dapat digunakan pada subset eksperimental; kelulusan lokal tidak
menutup insiden signal atau mengimplementasikan target bahasa lengkap.

- **Stability:** run serial akhir lulus; satu run penuh sebelumnya gagal pada
  proses pembanding C0.30. Atribusi signal dan konsistensi lintas lingkungan belum terbukti.
- **Memory/resource:** arena default 64 KiB, profil eksplisit 16 MiB RW/NX;
  bounded source/token/node/control/call/frame dipertahankan. Ini bukan audit
  alokasi atau kebocoran seluruh repository.
- **Error handling:** located diagnostic, invalid source/wire tanpa artifact,
  checked arithmetic/range, status runtime 70 dan I/O 74. Raw syscall mengembalikan
  rax kernel; programmer memiliki kebijakan error/retry/resource.
- **Architecture/bootstrap:** source NolQu-L dibangun predecessor B0, langsung
  menghasilkan ELF. Hash/pin dan generation comparisons nyata; tidak ada stage
  semantik Python/LLVM/NASM/linker baru.
- **Pipeline:** lexer/parser, indexed AST, name/scope/arity, scalar i64, bounded
  permission/range checks dan direct codegen ada. General type system, full
  Safety/ownership/lifetime, stable lower IR, optimizer canonical, modules dan
  compiler CLI yang sepenuhnya ditulis NolQu-L belum ada.
- **CLI/toolchain:** nama canonical dan alias tetap; default R0/NASM tetap.
  `--backend canonical` eksplisit. Shell/Python orchestration masih ada.
- **Testing:** baseline lengkap, negative/mutation, ABI/runtime, actual component
  rebuild dan SDK sudah dijalankan. Coverage-guided fuzzing, sanitizer NolQu-L,
  RSS/allocation pressure dan hardware-native x86 qualification belum tersedia/dijalankan.
- **Compatibility/debt:** corpus lama dan oracle independen dipertahankan;
  finite test coverage, monolithic B0-compatible compiler sources, raw caller
  obligations dan legacy installer precondition tetap debt nyata.

## 4. Rencana perubahan menurut dependency

| Priority | Problem / root cause | Files / perubahan / alasan sekarang | Risk dan required tests |
| --- | --- | --- | --- |
| 1 | source belum memiliki native scope/argv/OS contract | `frontend.nql`, wire decoder/test; contextual unsafe + NQAF/6 | HIGH; RED, source anchors, malformed, shadows, legacy byte parity |
| 2 | AST/native permission tidak boleh dipercaya hanya dari producer | `backend.nql`, native backend/runtime tests; source containment independen, argv/span/frame guards, syscall ABI | HIGH; forged wire, r10/r9, both profiles, nested calls, runtime faults |
| 3 | kemampuan harus menghasilkan program nyata dan generasi berikutnya | `native_cat.nql`, independent predecessor fixtures, generation/public tests, pasangan pin | HIGH; file/binary/stdin, I/O progress, fd0/close-once, A1/A2 dan B==C, relocation |
| 4 | metadata/probe tidak boleh mengeklaim keberhasilan parsial | MCP consumer/test + docs; exact stream/artifact/selector identities dan fail-closed flags | HIGH; forged/stale/missing evidence, fresh SDK, full regression/protocol |
| 5 | finite hardening perlu evidence dan batas operasional | `tests/security/`; bounded host runner, persistent corpus, deterministic mutations dan pure semantic oracle | HIGH validation scope; real timeout/signal/output controls, malformed boundaries, exact expected behavior |
| 6 | audit menemukan separator diagnostic C0R-008/009 ganda | backend suffix pointer/length dan assertion format; source fix melalui B0, bukan patch ELF | HIGH identity impact; RED enam subcase, A1/A2, runtime, review, generation/proof, impacted public/MCP |

Gate internal bukan pengiriman fitur kecil terpisah. Source/pin tidak
dipromosikan sebelum pasangan, rebuild dan review konsisten.

## 5. Implementasi nyata

`frontend.nql` mengenali `unsafe` hanya sebagai opener pada batas statement;
nama local/function `unsafe` tetap sah. First-comment invariant harus substantif.
Call raw diperiksa menurut owning statement dan exact global function resolution.
NQAF/6 memakai record 32 byte, dialect 5, profile 0/1 dan marker kind 45/46.

`backend.nql` memvalidasi framing, topology, unique ownership, header dan brace
source secara independen sebelum emission. Memindahkan close record yang sah
melewati raw call di luar source scope ditolak C0B-010. C0B-009 profil lama tetap.

Runtime dihasilkan langsung dari source codegen NolQu-L. Semantik pentingnya:

```text
arg_copy(i, offset, capacity):
    validate destination, positive capacity and argv index
    locate NUL within capacity before writing any destination byte
    copy exact bytes plus NUL; return length excluding NUL

syscall6(number, frame_offset):
    validate complete arena span [frame_offset, frame_offset + 48)
    rax = number
    rdi,rsi,rdx,r10,r8,r9 = six little-endian 64-bit frame words
    syscall; result = raw rax
```

`native_cat.nql` memakai API itu untuk membuka file literal dan menyalin byte;
retry read/write, partial progress dan single-close berada dalam source utility,
bukan tersembunyi dalam intrinsic. MCP memvalidasi proof lengkap serta menyalin
16 native evidence files sebelum temporary cleanup. Lima fungsi process-boundary
yang telah direview sebelumnya tidak diubah.

Daftar source/kontrak/test ada di [NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md),
[panduan toolchain](../compiler/CANONICAL_TOOLCHAIN.md) dan
[assurance test guide](../../tests/security/README.md). Tidak ada placeholder
Full Compiler yang dipromosikan.

## 6. Fitur baru dan biaya

| Syntax/API | Semantics / cost / safety |
| --- | --- |
| `arg_count()` | argc termasuk argv0; tidak memerlukan arena jika berdiri sendiri |
| `arg_copy(i,o,n)` | exact binary argv, checked destination/index; bounded scan lalu copy, tidak ada partial destination pada capacity error |
| `unsafe { # safety: ... }` | explicit lexical responsibility, required invariant; tidak membuktikan isi invariant atau menghapus compiler diagnostics |
| `byte_address(o,n)` | checked arena span lalu raw i64 pointer; one-past hanya sah untuk empty span; unsafe wajib |
| `syscall6(number,frame)` | satu instruction syscall memakai enam word/48 byte; unsafe wajib, tanpa hidden retry/errno conversion/allowlist |

Invalid invariant: C0P-014; source raw call di luar scope: C0S-001; malformed
wire/ownership: C0B-001/002/010; arity/name: C0B-008; runtime range/index/capacity:
C0R-004/008/009. General `safe`/`unsafe fn` dan safety modes penuh bukan fitur C0.32.

## 7. Bug dan insiden

| Bug / lokasi / cause | Severity dan status | Fix / regression proof |
| --- | --- | --- |
| candidate frontend menganggap condition variable `unsafe` sebagai opener | correctness HIGH, FIXED sebelum promosi | contextual pre-scan diperbaiki; RED delapan subtest lalu legacy AST/ELF parity dan independent rereview |
| candidate runtime helper target 576 byte terlalu awal | correctness HIGH, FIXED sebelum promosi | actual wide pool origin `0x5fa240` dipakai; native runtime dan 123 backend/legacy metode lulus; bukan manual ELF patch |
| C0R-008/009 menulis `: : error` setelah lokasi | diagnostic defect, FIXED; canonical identity risk HIGH | shared prefix sudah menulis separator; suffix pointer +2 dan length -2 memperbaiki empat immediate; enam strict-format subcase RED lalu runtime GREEN |
| supplemental runner belum menjamin cleanup/capture pada cancellation dan partial setup | host validation gaps, FIXED setelah independent review | private Linux subreaper, deferred cancellation sampai handle terdaftar, fail-closed control dan corpus retention; 11 control methods PASS |
| budget assurance 300 detik tidak cukup setelah private supervisor diperketat | harness configuration, CORRECTED dengan pengukuran | failed run tetap disimpan; total budget menjadi600, per-target5 dan semua594 kasus tetap; completion335.867s |
| C032-SIGNAL-01: frozen C0.30 comparison backend exit -9 saat compile nested call | reliability/assurance OPEN, severity keamanan belum ditetapkan | no source fix; failed run, exact-method pass dan identical-input serial pass dipertahankan; sender/cause tidak direkam |
| legacy combined installer dari foreign cwd tanpa prebuilt R0 | inherited reliability limitation OPEN di luar native semantics | normal `make compiler` prerequisite membuat unchanged scoped relocation lulus; canonical-only mode lulus tanpa host compiler |

Tidak ada confirmed vulnerability yang ditetapkan oleh pekerjaan scoped ini.
Ini bukan pernyataan bahwa repository bebas vulnerability. Bug candidate yang
telah diperbaiki tidak diatribusikan pada release publik tanpa bukti.

Insiden signal tidak di-quarantine atau dinyatakan flaky yang aman. Reproduction
rate belum terukur sebagai eksperimen terkontrol. Tidak ada klaim OOM. Owner
tindak lanjut belum ditetapkan; CODEOWNERS menyediakan routing maintainer.
Exit criterion: cause/mitigation yang dapat dibuktikan beserta regression dan
full relevant gate; kelulusan retry saja tidak memenuhi criterion itu.

## 8. Hasil test setelah implementasi

Tabel ini adalah checkpoint native **sebelum** patch formatter yang ditemukan
oleh audit diagnostic. Hasil tetap dipertahankan dengan identitas aslinya.
Post-patch gate menguji identitas baru secara terpisah; tidak mengubah baseline.

| Gate aktual | Hasil | Durasi / interpretasi |
| --- | --- | --- |
| final serial `make -k test` pada frozen runtime tree | 1079 PASS markers; 0 failed/skipped/timeout | 4524.151s; semua 1078 baseline labels tetap |
| full MCP discovery unittest, audit enabled, ResourceWarning error | 124 metode PASS; 0 fail/skip | 544.600s; semua 112 baseline methods tetap |
| `make release-check` | 9 PASS | 6.190s pada installed execution closure |
| actual component generations | 6 metode PASS | 648.759s; 722 stages/275 checks/475 artifacts |
| public full-source/CLI/project/install | CLI35/project32 metode pada main; scoped native/relocation checks pass | counts beririsan; bukan ditambahkan kembali |
| fresh installed SDK combined probe | PASS untuk enam bounded capability flags | 1903.670s; cleanup dan 16 retained evidence files |
| protocol/resource checkpoint | 120 tools/8 resources/5 prompts; schemas preserved; delapan resource dibaca | proses baru dari cwd lain; tidak mengeksekusi mutating tool |
| supplemental assurance first run | 4 metode PASS, 594 invocations; 0 signal/timeout | 125.130s; 24 corpus/profile, 132 source mutations, 360 wire rejects, 12 pure runtime oracles |
| runner failure controls | 6 metode PASS | 0.983s; sengaja memicu timeout/signal/output limit pada host children |

Run penuh pertama pada milestone ini memang **FAILED**: make exit2, 1603.220s,
frozen old backend -9 sementara candidate 0. Tidak dihapus atau diganti oleh
run akhir. **Regression detected: YES pada konsistensi proses pembanding;
cause OPEN. Deterministic regression pada source candidate belum terbukti.**
Tidak ada crash/timeout candidate pada run akhir dan profile assurance terbatas;
hal ini tidak menyangkal kejadian signal sebelumnya.

Hasil berikut memakai **source/pin setelah patch diagnostic**, bukan hash
checkpoint sebelumnya. Perintah dan streams lengkap ada pada receipt yang
dicantumkan di evidence index.

| Gate setelah patch | Hasil aktual | Durasi / batas klaim |
| --- | --- | --- |
| full MCP discovery, audit enabled, `ResourceWarning` sebagai error | 124 metode PASS, 0 fail/skip; seluruh112 baseline methods tetap | unittest455.916s, command458.235s |
| fresh-process installed SDK combined probe | PASS, enam bounded flags true; 722 stages/275 checks, dua B/C oracle pairs masing-masing41 metode, 475 artifacts diperiksa | SDK1591.327s; tujuh hash bootstrap tetap; temporary cleanup dan16 native evidence files ditahan |
| impacted public CLI | 2 metode PASS, 0 fail/skip | 46.553s; native utility/literal arguments dan permission error/output preservation |
| impacted public project/install | 3 metode PASS, 0 fail/skip | 157.327s; invariant/cache, binary files/profile cache, canonical-only relocation tanpa host compilers |
| bounded runner failure controls | 11 metode PASS, 0 fail/skip | command6.737s; real cancellation, detached owned descendant, unrelated sibling survival, timeout/signal/output, partial setup |
| hardened deterministic assurance profile | 4 metode PASS; 594 target invocations; 0 fail/error/skip/timeout/signal/supervisor failure | command335.867s, budget600s; 24 seed/profile +132 source mutations (96 wajib ditolak) +360 wire rejects +12 pure semantic oracles |
| retained public B/C compiler images | empat image aktual; frontend B==C, backend B==C | enam parse/compile commands exit0; images, AST dan raw streams ditahan |
| diagnostic samples / metadata resources / release checks | dua actual runtime errors sesuai kontrak; 7 metadata methods PASS; 9 release checks PASS | 4.314s / command13.329s /3.279s |

Full `make -k test` **NOT RERUN setelah patch empat immediate**. Audit dependency
mengikat424 input main yang tetap sama, ditambah25 foundation/version inputs dan
69 input canonical/MCP yang cocok dengan run baru. Perubahan source/codegen
ditutup oleh fresh backend/native/generation/proof/public/MCP checks; R0 tidak
berubah. Ini alasan pemilihan impacted gates, bukan waiver insiden signal atau
klaim full-main baru. `final-evidence-audit.json` memeriksa identitas tersebut.

Run hardened assurance dengan budget300s memang **FAILED**: 473 target sempat
diluncurkan;122 unittest errors terdiri dari satu target yang hanya mendapat
sisa0.066649s, lalu121 kasus tidak diluncurkan karena budget habis. Deadline
runner menjelaskan terminasi target itu; ini kejadian berbeda dari SIGKILL
lama. Budget dikoreksi menjadi600s berdasarkan proyeksi sekitar377s. Tidak ada
kasus, corpus, assertion, atau per-target5s yang dikurangi. Audit membuktikan
473 input prefix sama dan472 outcome yang selesai sama, serta hanya literal
total-budget300→600 berubah pada kode profil. Receipt batch sebelumnya tetap
`passed=false`; kelulusan completion tidak menulis ulang hasil gagal.

## 9. Bootstrap verification

A1 dan A2 dibangun ulang B0 secara independen, dibandingkan sebelum pin dipasang.
Full-source B dan C dibangun oleh generasi sebelumnya dan dibandingkan seluruh
bytes, streams, hashes, selectors dan kedua profile traces.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| selected frontend A1==A2 | 124215 | `9da819d6ea3017d39135532f0b4c3f0cd3105d31e4450802302bb9422e2f5e5b` |
| selected backend A1==A2 | 315593 | `303d2b21bcac54d4961acf451968f09a657a15b833a699ba368148f2dc43b65d` |
| full frontend B==C | 6361360 | `65e2f7de291a0dd735424014d28def990cdeaa46697b5d196edda17c9f1a79bc` |
| full backend B==C | 6475137 | `da2abbe63d97e2cfddfde798c791b44b9cc459b0295ed6df7de61a6a4495b0b8` |

B==C membuktikan bounded component generation, bukan Full Compiler atau
full-language verified self-hosting; A tidak diklaim sama dengan B. Source
frontend 80300 byte dan backend 199852 byte. Foundation/Stage0/B0/C0.25/successor
identities tetap; tidak ada capacity bridge atau hidden toolchain dependency baru.

Tabel artifact di atas juga merekam checkpoint sebelum perbaikan diagnostic.
Backend yang sudah direview dan dimaterialisasi setelah fix tetap315593 byte,
SHA-256 `b169f9ee8890d306c080f299980c352bbabc5518052355dd0148a7878b9f51b1`.
Source backend kini199908 byte,
SHA-256 `bc230a170b8742a26b98b03d6cc36c5878a9a38c0dd4c4fbc0450b70eb64157f`.
Hanya empat byte immediate pada selected image berubah; seluruh image sebelum
patch tetap tersimpan. A1/A2 baru identik, satu metode strict diagnostic RED pada
enam subcase sebelum fix, lalu seluruh enam metode runtime GREEN41.452s. Review
independen patch Spec/Quality Approved. Full-source generation dan proof
post-patch mempunyai receipt sendiri, bukan mengambil hash lama sebagai bukti baru:

| Artifact saat ini | Bytes | SHA-256 |
| --- | ---: | --- |
| selected frontend A1==A2 | 124215 | `9da819d6ea3017d39135532f0b4c3f0cd3105d31e4450802302bb9422e2f5e5b` |
| selected backend A1==A2 | 315593 | `b169f9ee8890d306c080f299980c352bbabc5518052355dd0148a7878b9f51b1` |
| full frontend B==C | 6361360 | `65e2f7de291a0dd735424014d28def990cdeaa46697b5d196edda17c9f1a79bc` |
| full backend B==C | 6475137 | `c789a3442691dd4f51f51ecb594265ff7b106a45313b8f6e91c7ec233bd29f85` |

Empat B/C image executable benar-benar disimpan di `current-generation-images/`,
bukan hanya digest. B dibangun melalui public `nqlc --backend canonical
--compiler-profile`; B frontend/backend membangun C dari source lengkap yang
sama. Python hanya mengatur framing/streams/file. Semua enam command exit0,
stderr kosong; B==C dihitung dari seluruh bytes. Source frontend tetap80300 byte,
backend kini199908 byte. Bounds/predecessor tidak berubah.

## 10. Resource/memory validation

Yang benar-benar diuji meliputi argv binary/non-UTF8/empty, arena edge dan zero
length, two-profile mmap/munmap, frame end, callee-save/alignment, closed/error
streams, real binary file copy, fd0 ownership, single close, partial output,
explicit synthetic EINTR/short-write injections, unique temporary publication,
preservasi output lama dan owned-process cleanup pada suite relevan.

Harness tambahan memakai per-target wall5s/total600s, input3MiB, output kurang
dari8MiB/stream dan Linux file/CPU/core controls. Setiap invocation memiliki
private subreaper; owned descendants, termasuk yang membuat session baru,
dibunuh/direap saat timeout maupun setelah leader selesai. Main-thread
SIGINT/SIGTERM/SIGHUP/SIGALRM ditunda selama akuisisi handle dan cleanup agar
proses yang sudah diluncurkan tidak kehilangan owner. Unrelated sibling tetap
hidup pada test. Ini bukan sandbox atau jaminan cleanup setelah supervisor
sendiri SIGKILL/kernel hang. 594 adalah jumlah target invocations, bukan jumlah
seluruh proses OS karena ada supervisor host tambahan.
First evidence folder sekitar223MiB. RSS cap, allocation fault injection,
ASan/MSan/UBSan, arbitrary native resource pressure dan hardware-native x86
execution tidak diklaim. CPU guard dikonfigurasi; bukan kampanye CPU-pressure.
Python ResourceWarning error membantu memeriksa host FD/process handling;
tidak menggantikan sanitizer memory.

Selected images bertambah dibanding predecessor C0.31 (frontend99256 ->124215,
backend261451 ->315593 byte). Tidak ada klaim lebih cepat/hemat memori. Runtime
arena bounds tidak naik; wall times di atas adalah evidence durasi, bukan benchmark.

## 11. Diagnostic validation

Contoh berikut berasal dari retained compiler invocation streams, bukan teks
yang dikarang untuk dokumentasi:

```text
input:1:16: error[C0P-001]: invalid byte; use ASCII identifiers and decimal expressions
input:1:28: error[C0P-006]: expected operand; use identifier, decimal or grouped expression
input:1:18: error[C0B-008]: invalid function binding or call; check unique names, main() and argument counts
input:2:23: error[C0S-001]: raw native call outside unsafe scope; wrap its owning statement in unsafe
input:1:11: error[C0P-014]: invalid unsafe invariant; add a nonempty first safety: comment
input:1:1: error[C0B-001]: invalid NQAF stream; regenerate the complete AST with C0 frontend
input:1:18: error[C0R-004]: byte range out of bounds; check offset and count
input:1:18: error[C0R-008]: argument index out of bounds; check arg_count and index
```

Cases memeriksa code, lokasi nonzero/expected, cause/suggestion, status dan
empty stdout. Runtime range/index diagnostic juga dieksekusi terpisah pada
known fixed programs, exit70 dengan stdout kosong; hasil setelah fix ada di
`diagnostic-samples-fixed/summary.json`. `diagnostic-samples/` tetap menyimpan
reproducer separator ganda sebelum patch. C0R-009 juga diperiksa oleh strict
runtime regression; tidak mengklaim contoh yang belum dieksekusi.
Tidak ada canonical external linker untuk menginjeksi link-failure; jalur itu N/A.

## 12. Compatibility report

Tidak ada intentional breaking change pada stable public contract. Pasangan
komponen/pin versioned harus dipasang bersama; rollback harus coherent.

| Axis | Status | Evidence / migration |
| --- | --- | --- |
| Source syntax | Additive experimental; compatible lama | contextual unsafe/nama intrinsic shadows; frozen predecessor corpus |
| Source semantics | Compatible lama | old AST/ELF byte parity dan semua baseline labels |
| CLI/tooling | Compatible; native proof fields additive | command/alias/default/schema preserved; CLI/project/SDK tests |
| Standard library/API | N/A | belum menambahkan stdlib; native intrinsic internal experimental |
| ABI/FFI | ABI lama compatible; native internal additive | six-register actual mmap, callee state/alignment; bukan stable foreign ABI |
| Binary/object artifact | old successful corpus compatible | direct ELF; tidak ada object/linker contract baru; pin baru eksplisit |
| Runtime behavior | Compatible lama/additive explicit raw behavior | kedua profiles, guards dan owned utility tests |
| Bootstrap chain | Preserved | B0 predecessor sama; source/pin baru reviewed; B==C |
| Reproducibility | byte comparisons PASS, reliability OPEN | artifact equality terukur; satu process SIGKILL belum dijelaskan |
| Diagnostic contract | Preserved/additive; local format repaired | C0B-009 tetap; C0B-010/C0S-001/C0P-014/new runtime codes; separator C0R-008/009 diperbaiki |
| Project/module format | Preserved | nql.toml/.nql unchanged; general module belum ada |

## 13. Final architecture status

CURRENT canonical path:

```text
*.nql (+ optional explicit NQSC/1 compiler profile)
  -> native C0.32 frontend
  -> validated NQAF/1..6 indexed AST
  -> native C0.32 name/scope/arity + checked direct backend
  -> ELF64 Linux x86_64, syscall-only, no dynamic interpreter
  -> execution on target (QEMU adapter on this aarch64 host)
```

Public default tetap R0/NASM; explicit canonical path tidak fallback ke R0.
TARGET Full Compiler/type/resource/module/optimizer/full Safety dan toolchain
sepenuhnya NolQu-L tidak disajikan sebagai CURRENT.

## 14. Final bootstrap chain status

```text
Machine-Level Foundation    PASS
  -> Stage0                PASS
  -> Bootstrap Compiler B0  PASS
  -> Core Compiler          PASS (C0.25 emitter + C0.32 components)
  -> Full Compiler          NOT IMPLEMENTED
  -> Self-Hosting nqlc       NOT IMPLEMENTED
  -> Verified nqlc           NOT IMPLEMENTED
```

PASS mencerminkan concrete functional/hash/generation gates dan manifest,
bukan pembuktian formal. Overall stable/security qualification tetap PARTIAL
karena incident dan checks yang belum dijalankan.

## 14A. Release/changelog/governance status

| Field | Status |
| --- | --- |
| Release Candidate / Release Ready | tidak ada; NO |
| Changelog / Migration / Deprecation / Removal | Unreleased updated; coherent pair install; tidak ada deprecation/removal |
| Review Required / Status | HIGH-risk independent implementation/source, formatter patch dan scoped assurance reviews Approved; separate signal investigation OPEN; bukan approval release |
| Review owner mapping | existing CODEOWNERS default @Nadzil; tidak mengarang approval maintainer manusia |
| CI Required Checks / Status | local relevant main/MCP/release/bootstrap/protocol/assurance evidence; remote required-check/branch protection NOT VERIFIED |
| Scheduled compiler/security CI | NOT IMPLEMENTED pada workflow checkout yang diperiksa; workflow React bukan bukti compiler CI |
| Flaky Test Status | unexplained signal incident OPEN; no quarantine/no assertion weakening |
| Dependencies / supply chain | tidak ada dependency semantik/runtime baru; Python stdlib/QEMU host test only |
| SBOM / provenance / artifact signing | NOT IMPLEMENTED untuk hasil ini; local hashes/rebuild bukan signature/provenance |
| Support lifecycle | DEVELOPMENT; tidak ada support-duration/EOL atau release baru |
| Security advisory | tidak diperlukan berdasarkan confirmed finding saat ini; private reporting policy sudah ada |
| Release authority | metadata project creator-led; tidak ada release approval yang dilakukan sesi ini |
| Target tier / downstream suite | formal tier NOT FORMALLY DEFINED; official sources/examples tested, broad ecosystem suite NOT YET ESTABLISHED |
| Retention | PARTIAL; full raw evidence lokal dan 16 MCP evidence files ditahan, tidak ada retention period formal |
| Rollback | exact owned before/after bytes/modes disimpan; tidak menyentuh unrelated inherited edits |

## 15. Ringkasan dan prioritas

- **Perubahan:** satu kemampuan native OS utuh beserta actual utility,
  source/wire/runtime guards, coherent pins, full-source generation proof,
  public/MCP integration dan supplemental bounded assurance.
- **Dampak:** explicit machine control bertambah tanpa hidden canonical compiler
  dependency; full Safety dan seluruh toolchain NolQu-L belum tercapai.
- **Baseline:** seluruh test labels baseline ditemukan pada final passing runs.
  Full main1079 merupakan checkpoint sebelum formatter patch; post-patch MCP124
  dan impacted canonical/public gates lulus pada checkpoint ini. Kelanjutan
  reliability membuktikan baseline pasca-formatter1079, lalu1080 pada revisi
  host observer dengan semua label tetap; lihat [laporan baru](C032_RELIABILITY_REPORT.md).
  Tidak ada klaim penyebab SIGKILL lama sudah diketahui.
  Konsistensi semua run belum hijau karena insiden signal; bukan no-regression claim.
- **Failure di luar scope:** inherited legacy installer precondition tetap
  terdokumentasi, tidak ditutup sebagai hasil canonical-only tests.
- **Tahap bootstrap:** functional Core components; bukan Full Compiler atau
  verified full-language self-hosting.
- **Prioritas berikut:** atribusi/mitigasi SIGKILL dengan metadata proses/resource
  yang memadai; perluas assurance/target qualification; baru pilih prerequisite
  type/module/toolchain berikut dari source nyata. Tidak menambah fitur baru untuk
  menyembunyikan gate stabilitas yang belum terselesaikan.

## Security assurance report — additive

```text
Security Review Scope: experimental canonical native source/wire/runtime,
                       publication and MCP boundary; not repository-wide audit
Threat Model Updated: YES, fresh scoped source-backed model + independent review
Affected Invariants/Test IDs: tests/security/README.md maps real IDs;
                             native frontend/backend/runtime/proof tests retained
Attack Surfaces/Boundaries: source -> AST -> checked codegen -> explicit raw OS;
                           direct compile paths vs project config vs native execution
Test Profiles Executed: PR/manual bounded profile; relevant main/SDK/bootstrap;
                        no extended fuzz or full release qualification
Fuzz Targets/Corpus/Budget: deterministic source/NQAF mutation; native-boundary-v1,
  SHA-256: 1f30672e7085104130363f346c4b07f069306fb7f2f1a6ce62da0162db516bee;
  seed0x4e514c32, wall5s/target+600s total, output8MiB/stream, input3MiB;
  4 methods/594 invocations PASS, 96 forbidden source mutations and360 bad wires
  require rejection; LIMITED, no coverage measurement; failed300s run retained
Sanitizer/Static Analysis: ResourceWarning-as-error host tests and independent
  source reviews; NolQu-L ASan/UBSan/MSan UNSUPPORTED by this custom codegen;
  TSan N/A for this single-process compiler/runtime scope, no concurrency claim
Negative/Boundary/Resource: malformed source/wire, scope restoration, limits,
  ABI/registers, argv/ranges/I/O/descriptors/temp/process paths as scoped above
Oracle/Miscompilation: frozen independent predecessor, actual B/C named oracles,
  exact independent pure outputs; no optimizer comparison because none exists
Confirmed Vulnerabilities: none established by this scoped work; not a clean scan
Open Risks/Mitigations: SIGKILL attribution, finite coverage, raw caller obligations,
  trusted project/pin/launcher assumptions, no OS sandbox; stable promotion held
Security Finding Regressions: no new confirmed vulnerability; candidate correctness
  regressions and host failure-detector controls are permanent tests
Required Security Gate: BLOCKED for stable/security-qualified promotion;
                        bounded native execution profile PASS within stated scope
Unrun/Unsupported: coverage-guided fuzz, NolQu-L sanitizer, hardware-native target,
  allocation/RSS pressure, dependency advisory rescan, signing/provenance/SBOM
Release Security Decision: NO RELEASE; no VERIFIED/SECURITY-QUALIFIED overall claim
```

Scoped threat model retained through Codex Security artifact storage:
`hardening/native-os-c032-threat-model-post-diagnostic.md`, SHA-256
`55e14771aca757b8cb38d8c077e3326b6172a9523c50cb23c71ccb4bb30fe462`.
The original `native-os-c032-threat-model.md` remains historical evidence.
The current model binds twelve source files to snapshot
`c612f7fd86738e75912d06601f57a90b0989dd6c36a29c092a2a908a78b0edf7`;
the four-immediate diagnostic patch changes identity, not architecture.
Its source citations are checked against the matching scoped snapshot.
Architecture hypotheses are not vulnerability findings. The model is not the
shared repository cache and does not replace the user's normative master prompt.

## Evidence index

Local evidence root: `/tmp/nql-next-compiler-v7wdgsfr`.

- `frozen-inputs.json`, `whole-before/`, `whole-candidate-review/`,
  `integration-receipt.json`: immutable baseline, exact review/install/rollback.
- `task3-generations/.../receipt.json`: actual component lineage; receipt SHA-256
  `9d3349af18eb8226012d6019ba98f22bcd426971ef2788ed2bcfbc3b9fdccf23`.
- `main-full/`, `main-failure-diagnostic/`, `main-serial-final/`: failed and
  successful observations, with command/status/raw stream identities.
- `task4-proof/full-mcp/`, `installed-execution-gates/`,
  `installed-combined-probe/`, `execution-audit.json`: full local executed gates.
- `protocol-installed-checkpoint/`, `protocol-installed-comparison.json`:
  initial installed protocol/resource capture; final doc capture is additional.
- `security-assurance-first/`, `assurance-runner-{red,green}.stderr`,
  `diagnostic-samples/`: historical assurance and original diagnostic reproducer.
- `diagnostic-patch-{red,green,build,before}/`,
  `diagnostic-patch-integration.json`: RED/GREEN, exact four-byte image delta,
  deterministic rebuild, materialization and rollback evidence.
- `post-diagnostic-fix/receipt.json`: post-patch MCP/proof/public/runner gates
  plus the failed300s assurance run; the batch is not relabeled PASS.
- `post-diagnostic-probe/receipt.json`, `current-generation-images/receipt.json`:
  fresh actual proof, source hashes, raw streams and four retained B/C images.
- `security-assurance-final/`, `security-assurance-completion/`,
  `assurance-completion/receipt.json`, `final-evidence-audit.json`: failed budget,
  unchanged-case completed profile and cross-receipt identity audit.
- `diagnostic-samples-fixed/`, `final-small-checks/`: actual corrected runtime
  diagnostics, metadata/resource tests and nine release checks.
- `.nolqu-mcp/evidence/` in the worktree retains sixteen real native proof files
  after consumed temporary directories are gone.
- `.superpowers/sdd/2026-10-24-canonical-native-os/` retains task reports,
  independent source reviews and signal investigation. These are engineering
  records, not human maintainer approval, published release or signing evidence.
