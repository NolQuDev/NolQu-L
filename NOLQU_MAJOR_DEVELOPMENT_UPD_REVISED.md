# NOLQU-L — DEVELOPMENT / ARCHITECTURE MASTER PROMPT

Lanjutkan pengembangan **NolQu-L** secara menyeluruh.

**Checkpoint kandidat native OS C0.32 — 2026-10-25:** frontend/backend kandidat
menambah blok `unsafe` berinvariant, argv native, alamat arena terperiksa serta
raw `syscall6`. NQAF/6 dialect5 memeriksa ownership dan containment source secara
independen; `C0B-010` baru mempertahankan diagnostic profil `C0B-009`. Utilitas
`native_cat.nql` membuka file literal dan menyalin binary/stdin dengan retry
read/write, partial progress dan single-close fd yang eksplisit dalam NolQu-L.

Generasi aktual lulus enam metode, 722 stage/275 check/475 artefak dan 41 oracle
per B/C tanpa skip. CLI publik membangun kedua source lengkap identik B/C.
Gate eksekusi akhir lulus: 1079 marker main, 124 metode MCP, sembilan
release-check, protokol dan probe gabungan installed-set. Source/pin ditinjau
independen. SIGKILL backend pembanding pada run sebelumnya tetap OPEN karena
penyebab belum diketahui; kesiapan stable/security masih PARTIAL. Lihat
[laporan sesi](docs/project/C032_SESSION_REPORT.md); retry bukan perbaikan. VERSION1.0.2a1/CHANNELdev tidak berubah; emitter monolitik C0.25
tetap berbeda. Ini belum full Safety, Full Compiler atau self-hosting penuh.
LLVM legacy serta Python MCP/test dan shell belum dimigrasikan. Lihat
[kontrak native](bootstrap/compiler/c0/NATIVE_OS.md) dan
[identitas terukur](bootstrap/compiler/c0/CAPACITY.md). Seluruh checkpoint/hash
C0.31 berikut dipertahankan sebagai sejarah dengan scope buktinya sendiri.

Penutupan bukti2026-10-26 membedakan main1079 sebelum patch formatter dari
source/pin saat ini. Setelah perbaikan empat immediate diagnostic C0R-008/009,
MCP124, proof aktual722 stage/275 check, lima impacted public tests, sebelas
runner controls dan594 assurance invocations lulus. Full main setelah patch
NOT RUN. Backend selected kini `b169f9ee…`; full backend B==C `c789a344…`.
Budget assurance300s sempat gagal; evidence tetap, budget600s terukur memakai
kasus/ekspektasi sama selesai335.867s. SIGKILL lama tetap OPEN; bukan rilis
atau kualifikasi keamanan keseluruhan. Hash lengkap tersedia di laporan sesi.

**Checkpoint verifikasi akses toolchain 2026-10-24:** akses aditif
`--backend canonical` pada `nqlc`, proyek `nql`, installer dan MCP telah terhubung
untuk subset C0.31 eksperimental; default tetap `nasm`/R0. Initializer hanya
menyimpan backend. Profil compiler 16 MiB diminta eksplisit pada build/run/test/
check, tidak diinferensikan atau dipersistenkan. Build memakai cache tervalidasi;
canonical `run` tetap mengompilasi ulang melalui `nqlc --run` setelah cache hit.

Gate teknis lulus: main 1.078 marker dengan seluruh 1.076 baseline dipertahankan,
33 pengujian CLI, 30 proyek/install relokasi, 112 MCP tanpa skip, sembilan
release-check dan tujuh hash bootstrap. Kedua source compiler lengkap berhasil
dibangun melalui CLI publik dengan byte identik artefak C0.31 tersimpan. Probe
C0 gabungan baru memverifikasi kapasitas, profil dan generasi komponen; seluruh
cleanup selesai dan identitas sumber tidak berubah. Perbaikan artefak/audit MCP
sudah ditinjau dan diuji penuh; panduan menjelaskan pemakaian ulang bukti main
pada dependensi yang tetap identik.

Ini checkpoint akses eksperimental teruji, bukan rilis. Full Compiler,
self-hosting dan Verified tetap false; VERSION/CHANNEL tidak berubah. LLVM tetap
legacy; target migrasi tetap toolchain sepenuhnya NolQu-L tanpa Python/LLVM.
Python MCP/pengujian dan orkestrasi shell saat ini belum dimigrasikan. Compiler
canonical sendiri menghasilkan ELF langsung tanpa semantik compiler host.
Lihat [panduan akses](docs/compiler/CANONICAL_TOOLCHAIN.md) untuk dependency host,
bukti dan batas single-unit/i64. Bukti kapasitas C0.31 dan checkpoint historis
di bawah tetap berlaku.

**Tambahan otoritas 2026-10-16:** ikuti juga
[kontrak Assembly-Level](NOLQU_MAJOR_DEVELOPMENT_ASSEMBLY_LEVEL.md) dan konsep
v10 yang dirujuk di sana. Kontrak tersebut menambah target desain, bukan
menghapus bukti C0.30 atau membatalkan pekerjaan kapasitas C0.31. Status historis
yang lebih lama di salinan Assembly-Level tidak menggantikan hasil terverifikasi.

**Status instalasi 2026-10-23:** set C0.31 telah dibangun dan dipasang koheren
setelah delapan pemeriksaan pra-instalasi lulus dan tiga review independen
menyetujui. Delapan pemeriksaan pascainstalasi juga lulus; kapasitas komponen
TERVERIFIKASI DAN COMPLETE dalam kontrak kapasitas C0.31. Review whole-change
akhir telah menyetujui penutupan tanpa temuan terbuka.
Lihat [checkpoint instalasi](#checkpoint-instalasi-c031-2026-10-23) dan
[CAPACITY.md](bootstrap/compiler/c0/CAPACITY.md). Tidak ada perubahan VERSION/
CHANNEL, promosi Full Compiler/self-hosting, atau penggantian CLI publik R0.

Tujuan jangka panjang NolQu-L adalah menjadi **general-purpose systems programming language** yang dapat digunakan pada berbagai tingkat kompleksitas:

- skrip sederhana,
- utilitas command-line,
- aplikasi umum,
- library,
- program modular berukuran besar,
- software dengan kebutuhan performa tinggi,
- runtime,
- tooling,
- FFI,
- sistem tingkat rendah,
- kernel,
- driver,
- hingga software yang memerlukan kontrol langsung terhadap mesin,

sambil tetap mempertahankan identitas utama NolQu-L:

**sederhana di permukaan, kuat di dalam, mudah dibaca, dekat dengan mesin, predictable, dan memiliki safety model yang eksplisit.**

Prompt ini adalah **MASTER DEVELOPMENT / ARCHITECTURE PROMPT**.

Prompt ini dapat digunakan untuk sesi Patch / Repair, Minor Development, Major Development,
Architecture Reset, Security / Correctness Hotfix, maupun Release Preparation.

**Konsistensi terminologi dan otoritas konsep:** `NolQu-L` adalah nama bahasa, sedangkan `NolQu` sendiri hanya merujuk ekosistem ketika konteks memang membahas ekosistem. Model keamanan resmi disebut `NolQu-L Safety`. Nine Pillars pada bagian `# 1. NINE PILLARS OF NOLQU-L` dalam dokumen ini merupakan filosofi normatif terkini; aturan historis yang bertentangan harus diperlakukan sebagai catatan sejarah, bukan instruksi untuk membatalkan Pillar 8. Jangan mengganti identifier CLI, nama artifact, hash, nama file, atau bukti historis hanya karena perubahan terminologi.

**Sebelum mengubah codebase, klasifikasikan kebutuhan aktual terlebih dahulu.**
Jangan menganggap sesi harus menjadi Major Update hanya karena prompt ini mempunyai scope luas.

Perubahan boleh mencakup banyak subsistem sekaligus apabila memang diperlukan, termasuk:

- Machine-Level Foundation,
- Stage 0,
- bootstrap compiler,
- compiler frontend,
- lexer,
- parser,
- AST,
- semantic analysis,
- type system,
- NolQu-L Safety,
- ownership,
- resource management,
- IR,
- optimizer,
- backend,
- code generator,
- runtime,
- standard library,
- linker integration,
- ABI,
- FFI,
- CLI,
- testing infrastructure,
- bootstrap verification,
- build system,
- dokumentasi arsitektur,
- dan toolchain lain yang relevan.

Namun perubahan besar **tidak boleh berarti perubahan sembarangan**.

Setiap perubahan harus:

1. memiliki alasan teknis,
2. memiliki tempat yang jelas dalam arsitektur,
3. memiliki test,
4. tidak menimbulkan regresi yang tidak disengaja; intentional breaking change harus mengikuti Pillar 8,
5. tidak menambah kompleksitas yang tidak diperlukan,
6. menjaga kemungkinan NolQu-L menjadi self-hosting,
7. tetap konsisten dengan Nine Pillars,
8. tetap dapat ditelusuri sampai ke perilaku mesin di bawahnya.

Jika ada bagian fundamental yang belum ditentukan oleh spesifikasi tetapi diperlukan agar implementasi dapat menjadi kokoh, **tentukan dan sempurnakan sekarang**.

Jangan sengaja meninggalkan fondasi yang jelas-jelas dibutuhkan hanya untuk sesi berikutnya.

Namun jangan pula mengarang hasil implementasi, hasil test, benchmark, atau kondisi repository.

Jika repository, compiler, toolchain, atau file yang diperlukan tidak tersedia, katakan secara eksplisit bagian mana yang tidak dapat diverifikasi.

---

# DEVELOPMENT CHANGE & RELEASE GOVERNANCE

Bagian ini mengatur **kapan perubahan harus dianggap kecil, besar, breaking, hotfix,
atau membutuhkan keputusan arsitektur formal**.

Aturan ini berada di atas keinginan untuk "menambah banyak fitur".

Prinsip utama:

> **Ukuran update ditentukan oleh perubahan contract, blast radius, risk, dan migration cost — bukan oleh jumlah baris kode atau jumlah file.**

Contoh:

```text
20 baris yang mengubah ABI
→ dapat menjadi Major Development.

2.000 baris test baru tanpa mengubah contract
→ dapat tetap Minor Development.
```

Development classification juga **berbeda** dari release version.

```text
Development Class
≠
Release Version
≠
Bootstrap Milestone
≠
Feature Maturity
```

Satu sesi dapat menghasilkan banyak commit tanpa harus menaikkan public version.
Sebaliknya, satu perubahan kecil secara diff dapat memerlukan major release apabila
memutus stable public contract.

---

## A. WAJIB: CLASSIFY BEFORE MODIFY

Sebelum implementasi, tuliskan:

```text
Requested Mode:
Actual Update Class:
Risk Level:
Primary Scope:
Affected Subsystems:
Public Contract Impact:
Bootstrap Impact:
Compatibility Impact:
Version Impact:
RFC / ADR Required:
Release Blocking:
Reason:
```

Jika repository belum diperiksa, `Actual Update Class` boleh sementara:

```text
PENDING BASELINE INSPECTION
```

tetapi harus diputuskan setelah baseline dan dependency nyata diketahui.

Agent **boleh dan harus** menurunkan atau menaikkan klasifikasi jika evidence menuntut.

Contoh:

```text
Requested Mode : Major Development
Actual Need    : Patch / Repair

Reason:
Failure berasal dari stale milestone assertion.
Architecture dan semantics tidak berubah.
```

atau:

```text
Requested Mode : Minor Development
Discovery      : Parser change membutuhkan perubahan AST + semantic + IR + ABI.

Decision:
STOP SCOPE EXPANSION
→ Reclassify as Major Development
→ Update plan
→ Continue only after impact review
```

---

# UPDATE CLASSIFICATION

## 1. PATCH / REPAIR UPDATE

Gunakan **Patch / Repair Update** jika perubahan memperbaiki perilaku yang seharusnya
sudah benar tanpa mengubah stable contract.

Contoh:

- bug lokal;
- stale test;
- diagnostic typo;
- cleanup/resource leak;
- manifest/hash/documentation drift;
- deterministic-build bug;
- implementation defect dengan semantics yang sudah ditentukan;
- regression yang root cause dan scope-nya lokal;
- build script fix tanpa perubahan canonical architecture;
- performance regression fix tanpa observable semantic change.

Patch tidak boleh diam-diam:

- menambah syntax baru;
- mengubah stable semantics;
- mengubah ABI;
- mengubah bootstrap topology;
- mengubah public CLI contract;
- mengubah ownership/safety model;
- mengubah object format contract.

Flow minimum:

```text
Reproduce
→ Root Cause
→ Minimal Correct Fix
→ Targeted Test
→ Impacted Regression Test
→ Documentation Sync
→ Close
```

Patch harus sekecil yang diperlukan, tetapi **bukan berarti asal minimal**.
Jika root cause membutuhkan perubahan fundamental, reclassify.

---

## 2. MINOR DEVELOPMENT UPDATE

Gunakan **Minor Development** jika perubahan menambah kemampuan nyata tetapi masih
berada di dalam architecture dan stable contract yang sudah disepakati.

Contoh:

- menambah satu construct yang additive dan backward-compatible;
- memperluas parser di bawah grammar architecture yang sama;
- menambah intrinsic bounded;
- menambah runtime primitive yang mengikuti resource model yang sama;
- menambah backend capability mengikuti ABI yang sudah ada;
- memperluas diagnostics;
- menambah test/fuzz coverage;
- menaikkan bounded capacity berdasarkan evidence terukur;
- menambah optimization yang tidak mengubah observable semantics;
- menambah CLI capability yang additive;
- melanjutkan milestone bootstrap incremental.

Required:

```text
Defined Scope
Defined Success Criteria
Affected Contracts
Targeted Tests
Subsystem Tests
Relevant Regression Tests
Compatibility Check
Documentation Update
Measured Next Blocker
```

Minor development tidak boleh berubah menjadi architectural rewrite secara diam-diam.

---

## 3. MAJOR DEVELOPMENT UPDATE

Gunakan **Major Development** jika perubahan menyentuh fondasi utama atau mempunyai
blast radius lintas-subsystem.

Trigger Major antara lain:

### Architecture

- canonical compiler pipeline berubah;
- frontend/backend boundary berubah secara fundamental;
- representation utama compiler berubah;
- runtime architecture berubah substantif;
- memory/resource architecture berubah;
- toolchain contract berubah luas.

### Language Semantics

- syntax fundamental berubah;
- stable semantics berubah;
- type system berubah substantif;
- ownership/resource model berubah;
- safety model berubah;
- error/concurrency/module model diperkenalkan atau dirombak;
- compile-time/runtime boundary berubah.

### Machine / Binary Contract

- ABI berubah;
- calling convention berubah;
- object format contract berubah;
- memory layout contract berubah;
- FFI model berubah;
- stable IR semantics berubah;
- target strategy berubah secara fundamental.

### Bootstrap / Trust

- canonical bootstrap stage berubah;
- stage baru ditambahkan atau stage lama dihapus;
- Core → Full Compiler transition;
- Full Compiler → self-hosting;
- self-host generation A → B;
- verified generation B → C;
- trusted bootstrap boundary berubah;
- hidden host dependency ditemukan dalam canonical path.

### Cross-Subsystem

Jika satu perubahan nyata membutuhkan coordinated changes seperti:

```text
Lexer
+
Parser
+
AST
+
Semantic Analysis
+
IR
+
Codegen
```

maka perlakukan sebagai Major kecuali analisis membuktikan contract tetap lokal.

Major Development membutuhkan:

```text
Architecture Review
Impact Analysis
Compatibility Matrix
Migration Plan
Implementation Plan
Test Plan
Regression Plan
Performance/Resource Check
Bootstrap/Trust Check
Documentation Plan
Rollback/Revert Plan
Evidence
Measured Next Blocker
```

---

## 4. ARCHITECTURE RESET / BREAKING DEVELOPMENT

Gunakan kategori ini lebih jarang daripada Major Development.

Architecture Reset diperlukan bila contract fundamental lama terbukti tidak layak
dipertahankan.

Contoh:

- bootstrap chain sebelumnya salah secara arsitektural;
- compiler architecture terbukti menghalangi self-hosting;
- IR harus diganti, bukan sekadar diperluas;
- ABI perlu redesign;
- ownership/safety architecture lama tidak dapat diperbaiki secara incremental;
- canonical naming/toolchain contract perlu diganti secara menyeluruh;
- dependency yang dianggap canonical ternyata melanggar trust model.

Architecture Reset wajib menulis:

```text
Old Architecture:
Observed Failure:
Evidence:
Why Incremental Fix Is Insufficient:
New Architecture:
Preserved Contracts:
Broken Contracts:
Deprecated Components:
Migration Strategy:
Compatibility Cost:
Bootstrap/Trust Impact:
Test Migration:
Rollback Possibility:
```

Jangan melakukan silent architecture reset.

---

## 5. SECURITY / CORRECTNESS HOTFIX

Security / Correctness Hotfix **mengalahkan feature priority** jika ditemukan masalah
yang dapat:

- menghasilkan miscompile;
- menyebabkan silent data corruption;
- melanggar memory/resource safety yang dijanjikan;
- merusak bootstrap trust chain;
- merusak reproducibility secara diam-diam;
- menghasilkan artifact berbeda tanpa detection;
- membuka tool/sandbox/permission boundary yang tidak semestinya;
- memasukkan hidden host dependency;
- menyebabkan privilege boundary tooling terlewati;
- membuat stable compiler menerima invalid program sebagai valid;
- membuat valid program berubah semantics tanpa diagnostic.

Flow:

```text
Freeze Relevant Feature Work
        ↓
Reproduce
        ↓
Contain
        ↓
Root-Cause Analysis
        ↓
Fix
        ↓
Regression Test
        ↓
Relevant Full Gate
        ↓
Security/Correctness Documentation
        ↓
Resume Development
```

Jangan memakai "hotfix" untuk melewati test atau review.

---

# CHANGE IMPACT MATRIX

Setelah memilih Update Class, nilai blast radius pada setiap axis:

```text
Language Syntax:
Language Semantics:
Type/Safety:
Compiler Frontend:
IR:
Backend/Codegen:
Runtime:
Standard Library:
CLI/Tooling:
Source Compatibility:
Behavior Compatibility:
ABI/Binary:
Bootstrap:
Reproducibility:
Security/Trust:
Performance:
Documentation:
Migration:
```

Gunakan:

```text
NONE
LOW
MEDIUM
HIGH
CRITICAL
```

## Risk Level

### LOW

- lokal;
- contract tidak berubah;
- failure mudah dideteksi;
- rollback sederhana.

### MEDIUM

- satu subsystem;
- additive behavior;
- compatibility tetap terjaga;
- membutuhkan regression test lebih luas.

### HIGH

- beberapa subsystem;
- public contract dapat berubah;
- bootstrap/runtime/ABI/safety dapat terdampak;
- migration atau compatibility work diperlukan.

### CRITICAL

- miscompile;
- security/trust issue;
- bootstrap chain;
- ABI break;
- silent corruption;
- safety invariant break;
- reproducibility trust failure;
- architecture reset.

Rule:

```text
Highest relevant axis
→ minimum risk floor.
```

Jangan menurunkan risk hanya karena diff kecil.

---

# CHANGE ESCALATION / DE-ESCALATION

## Escalation

Jika pekerjaan melewati boundary klasifikasi:

1. hentikan scope expansion;
2. catat discovery;
3. ukur blast radius;
4. reclassify;
5. update plan/test/migration requirements;
6. baru lanjut.

Contoh:

```text
Minor Parser Update
        ↓
Needs AST Contract Change
        ↓
Needs Semantic + IR Changes
        ↓
STOP
        ↓
Major Development
```

## De-escalation

Jika dugaan masalah besar ternyata lokal:

```text
Major Investigation
        ↓
Root Cause = stale test
        ↓
Patch / Repair
```

Pilih perubahan terkecil yang **benar**, bukan perubahan terbesar yang mungkin dilakukan.

---

# PUBLIC CONTRACT DEFINITION

Release version hanya bermakna jika **public contract** NolQu-L didefinisikan.

Untuk versioning, public contract dapat mencakup bagian yang sudah dinyatakan stable:

```text
Source Syntax
Language Semantics
Type/Safety Behavior
Standard Library API
CLI Commands / Stable Flags
Project File Format
ABI / Calling Convention
FFI Contract
Object/Artifact Contract jika dipublikasikan
Runtime Observable Behavior
Stable Diagnostic Codes jika dijanjikan
Package/Module Contract jika sudah ada
```

Bukan semua detail internal adalah public contract.

Contoh internal yang biasanya bukan public contract kecuali sengaja dijanjikan:

```text
AST Node Layout
Private IR Implementation Detail
Internal Function Names
Temporary Compiler Pass Ordering
Private Cache Format
Test-Only Helpers
```

Namun bootstrap artifact/hash dapat tetap menjadi **canonical trust contract**
meskipun bukan user-facing API.

---

# VERSIONING POLICY

NolQu-L menggunakan makna versioning yang mengikuti prinsip:

```text
MAJOR.MINOR.PATCH
```

tetapi **jangan mengubah format version string yang sudah digunakan repository
secara diam-diam**.

Jika tool sekarang menampilkan bentuk prerelease seperti:

```text
1.0.2a1
```

format tersebut tetap dapat dipertahankan sampai ada keputusan release-format formal.

Perubahan format version string sendiri harus diperlakukan sebagai compatibility/release
decision apabila user/tooling sudah bergantung padanya.

## PATCH

Contoh:

```text
1.4.2 → 1.4.3
```

Untuk:

- backward-compatible bug fix;
- compiler correctness fix yang memulihkan documented behavior;
- compatible security fix;
- diagnostic/documentation correction;
- compatible performance improvement;
- internal cleanup tanpa stable semantic change.

Patch **tidak boleh** menyembunyikan intentional breaking change.

## MINOR

Contoh:

```text
1.4.3 → 1.5.0
```

Untuk:

- additive backward-compatible functionality;
- stable feature baru yang tidak merusak source lama;
- additive library/tooling API;
- target baru yang tidak mengubah semantics target lama;
- public feature yang mulai deprecated;
- substantial compatible capability.

## MAJOR

Contoh:

```text
1.x → 2.0.0
```

Pertimbangkan jika stable public contract berubah incompatible:

- language semantics break;
- incompatible syntax redesign;
- ABI break;
- module/package contract break;
- ownership/safety model break;
- stable CLI contract break;
- source compatibility break yang disengaja;
- runtime observable behavior break yang menjadi contract.

Jangan menaikkan Major hanya karena:

- repository membesar;
- banyak file berubah;
- benchmark naik;
- compiler lebih cepat;
- milestone internal berganti;
- implementation dirombak tetapi public contract tetap kompatibel.

## RELEASE IMMUTABILITY

Setelah versi resmi dipublikasikan:

```text
released version contents
→ immutable
```

Perbaikan harus menjadi release baru.
Jangan mengganti artifact dari nomor versi yang sama secara diam-diam.

---

# PRERELEASE / RELEASE MATURITY

Pisahkan **version number** dari **maturity**.

Lifecycle yang disarankan:

```text
Development
→ Alpha
→ Beta
→ Release Candidate
→ Stable
```

## Development

- aktif berubah;
- belum layak dijanjikan compatibility;
- incomplete capability boleh ada jika statusnya eksplisit;
- tidak boleh dipresentasikan sebagai stable.

## Alpha

- architecture utama sudah terlihat;
- feature masih dapat berubah;
- bug dan compatibility break masih mungkin;
- cocok untuk early evaluation.

Contoh existing-style:

```text
1.0.2a1
```

## Beta

- feature scope sebagian besar dibekukan;
- fokus beralih ke correctness, compatibility, performance, diagnostics, migration;
- breaking change baru harus mempunyai alasan kuat.

## Release Candidate

- candidate untuk stable;
- tidak ada feature expansion biasa;
- hanya release-blocking fix, regression fix, documentation/release correction;
- setiap change harus menjelaskan mengapa RC masih valid atau perlu RC baru.

## Stable

- seluruh release gate yang diwajibkan hijau;
- public contract terdokumentasi;
- migration/deprecation diketahui;
- artifact dan version tidak boleh diganti diam-diam.

Jangan menyebut build `Stable` hanya karena compile berhasil.

---

# FEATURE MATURITY

Feature dapat mempunyai status:

```text
PLANNED
EXPERIMENTAL
PREVIEW
STABLE
DEPRECATED
REMOVED
```

## PLANNED

Hanya design/roadmap. Jangan dokumentasikan seolah implemented.

## EXPERIMENTAL

Implemented untuk eksperimen tetapi:

- contract belum stable;
- dapat berubah;
- harus jelas tidak menjadi compatibility promise.

Jika feature-gating belum ada, jangan mengarang flag.
Gunakan mekanisme nyata yang tersedia atau jangan expose sebagai public stable feature.

## PREVIEW

- implementation cukup lengkap untuk broader testing;
- semantics hampir stabil;
- migration risk masih harus disebut.

## STABLE

- semantics dan contract jelas;
- tests lengkap;
- compatibility commitment berlaku.

## DEPRECATED

Masih bekerja tetapi tidak direkomendasikan untuk penggunaan baru.

Harus menyebut:

```text
Deprecated:
Reason:
Replacement:
Migration:
Earliest Removal:
Compatibility Notes:
```

## REMOVED

Penghapusan stable feature biasanya membutuhkan major-version compatibility decision,
kecuali feature memang belum stable atau penghapusan mendesak karena security/correctness.

---

# DEPRECATION POLICY

Stable capability **jangan langsung dihapus** tanpa transition kecuali terdapat
security/correctness reason yang kuat.

Deprecation harus:

1. mempunyai rationale;
2. mempunyai replacement jika ada;
3. mempunyai migration path;
4. mempunyai diagnostic/warning jika feasible;
5. menyebut earliest removal;
6. dicatat dalam changelog;
7. diuji selama compatibility window jika masih supported.

Jangan membuat deprecated path hidup selamanya jika sudah ada removal decision,
tetapi jangan menghapusnya diam-diam.

---

# RFC / ADR / DESIGN DECISION THRESHOLD

Tidak semua perubahan membutuhkan dokumen desain formal.

## RFC REQUIRED / STRONGLY REQUIRED

Gunakan proposal desain formal untuk perubahan substantif seperti:

- syntax/semantics baru yang bukan bugfix;
- penghapusan stable language feature;
- type/safety/ownership redesign;
- ABI/FFI change;
- module/package model;
- canonical bootstrap topology;
- new stable IR contract;
- concurrency/error model;
- public CLI architecture;
- stable runtime contract;
- major standard-library foundation;
- architecture reset.

Proposal harus mencakup:

```text
Summary
Motivation
Current Problem
Goals
Non-Goals
Detailed Design
Alternatives
Compatibility
Migration
Safety
Machine/Runtime Cost
Bootstrap Impact
Testing
Performance/Resource Impact
Security/Trust Impact
Drawbacks
Unresolved Questions
Rollout
Rollback
```

## ADR APPROPRIATE

Gunakan Architecture Decision Record untuk keputusan internal signifikan yang perlu
diingat jangka panjang tetapi tidak selalu membutuhkan RFC publik penuh.

Contoh:

- memilih internal representation;
- menentukan stage boundary;
- memilih deterministic data structure;
- menetapkan bootstrap trust assumption;
- memindahkan subsystem boundary.

ADR minimal:

```text
Context
Decision
Alternatives
Consequences
Status
Evidence
```

## RFC / ADR NOT REQUIRED

Biasanya tidak diperlukan untuk:

- typo;
- local bugfix;
- refactor tanpa meaning change;
- test coverage;
- cleanup;
- objective performance improvement tanpa contract change;
- internal rename yang tidak user-facing.

Namun dokumentasi code/test tetap wajib bila diperlukan.

Jangan mengarang nomor RFC/ADR seolah sudah accepted.
Jika repository belum mempunyai sistem RFC/ADR, tulis `PROPOSED` dan tentukan mekanisme
sebelum mengklaim decision formally accepted.

---

# COMPATIBILITY MATRIX

Jangan menulis hanya:

```text
Backward compatible: yes/no
```

Untuk perubahan signifikan, evaluasi axis berikut:

| Axis | Status | Evidence / Migration |
| --- | --- | --- |
| Source syntax | Compatible / Additive / Breaking / N/A | ... |
| Source semantics | Compatible / Behavior Change / Breaking / N/A | ... |
| CLI/tooling | Compatible / Additive / Breaking / N/A | ... |
| Standard library/API | Compatible / Additive / Breaking / N/A | ... |
| ABI/FFI | Compatible / Breaking / N/A | ... |
| Binary/object artifact | Compatible / Breaking / N/A | ... |
| Runtime behavior | Compatible / Behavior Change / Breaking / N/A | ... |
| Bootstrap chain | Preserved / Changed / N/A | ... |
| Reproducibility | Preserved / Changed / Not Tested | ... |
| Diagnostic contract | Preserved / Changed / N/A | ... |
| Project/module format | Preserved / Changed / N/A | ... |

Jika satu stable public axis breaking:

```text
Version Impact
→ evaluate MAJOR
```

kecuali project secara eksplisit masih berada pada unstable/pre-release contract dan
break tersebut memang diizinkan.

---

# MILESTONE VERSIONING VS PUBLIC RELEASE VERSION

Bootstrap milestone seperti:

```text
B0.7r
C0.24
C0.25
```

adalah **development milestone identifiers**.

Mereka bukan otomatis:

```text
NolQu-L 0.24
NolQu-L 0.25
```

Contoh:

```text
C0.24
→ lexical coalescing milestone

C0.25
→ source-driven parser milestone
```

Public language/compiler version harus diputuskan berdasarkan release contract,
bukan nomor bootstrap subphase.

---

# RELEASE CHANGELOG

Setiap public release atau prerelease yang berarti harus mempunyai changelog.

Kategori minimum:

```text
Added
Changed
Deprecated
Removed
Fixed
Security
```

Tambahkan jika relevan:

```text
Performance
Compatibility
Bootstrap
Tooling
Known Issues
Migration
```

Changelog harus menjelaskan dampak user-visible, bukan dump commit.

Jangan menulis:

```text
Fixed stuff
Updated compiler
Various improvements
```

Jika perubahan tidak user-visible tetapi penting untuk trust/bootstrap/reproducibility,
tetap dokumentasikan di kategori internal/release engineering yang sesuai.

---

# RELEASE GATES

Sebuah release tidak boleh dipromosikan hanya karena implementation selesai.

## Patch Release Gate

Minimum sesuai impact:

```text
Targeted Test
Impacted Regression Tests
Compatibility Check
Diagnostic/Error Check
Artifact/Version Check
Changelog
```

Jika patch menyentuh bootstrap/security/reproducibility, gate area tersebut wajib.

## Minor Release Gate

```text
Baseline
Targeted Tests
Subsystem Tests
Full Relevant Regression
Compatibility Matrix
Migration if Needed
Documentation
Changelog
Performance/Resource Check if Affected
Bootstrap Check if Affected
Security/Trust Check if Affected
```

## Major Release Gate

```text
Full Baseline
Full Regression
Bootstrap Verification
Compatibility Matrix
Migration Guide
Deprecation/Removal Audit
ABI/FFI Review
Safety Review
Security/Trust Review
Reproducibility
Performance/Resource Comparison
Downstream Compatibility Check if ecosystem exists
Supported Target Qualification if multi-target
Artifact Integrity / Hashes
Provenance / Signing / SBOM status documented
Release Branch / Freeze policy satisfied if used
Backport review if stable branch is affected
Documentation Audit
Changelog
Release Notes
Known Issues
Rollback/Revert Strategy
```

## Stable Release Gate

Selain gate sesuai version class:

```text
No unexplained regression
No release-blocking open bug
No fake/placeholder implementation
Public contract documented
Version consistent across tooling
Artifacts reproducible as required
Artifact hashes recorded
Provenance state documented
Signing state documented
SBOM state documented
Required merge/review gates satisfied
Required CI checks green
No unresolved critical flaky-test issue
Dependency state documented
Changelog complete
Migration documented
Support lifecycle declared
Known limitations explicit
```

---

# MERGE & REVIEW GOVERNANCE

Tidak semua perubahan membutuhkan level review yang sama, tetapi perubahan high-risk
harus mempunyai gate yang lebih kuat daripada perubahan lokal.

Prinsip:

> **Merge permission follows risk, not author confidence.**

## Review Requirement by Risk

### LOW

- self-review wajib;
- targeted test wajib;
- second-person review dianjurkan jika mudah tersedia, tetapi tidak harus menjadi
  blocker apabila repository memang dikelola satu maintainer;
- tidak boleh bypass test hanya karena scope kecil.

### MEDIUM

- self-review wajib;
- impacted subsystem tests wajib;
- compatibility check wajib;
- independent review atau explicit maintainer review sangat dianjurkan sebelum merge.

### HIGH

- independent review wajib jika workflow repository memungkinkan;
- seluruh required status checks harus hijau;
- architecture/compatibility impact harus tertulis;
- unresolved review comment yang menyentuh correctness tidak boleh diabaikan;
- perubahan tidak boleh langsung didorong ke protected/release branch tanpa gate.

### CRITICAL

- review oleh lebih dari satu pihak dianjurkan apabila maintainer tersedia;
- security/correctness/bootstrap evidence harus dilampirkan;
- merge harus diblokir selama blocker belum diselesaikan;
- emergency bypass hanya boleh terjadi bila proses repository memang mendefinisikannya,
  dan bypass tersebut harus dicatat serta diaudit setelahnya.

Jika platform menyediakan branch/ruleset protection, pertimbangkan untuk menerapkan:

```text
Required Status Checks
Required Review
Conversation Resolution
Restricted Direct Push
Force-Push Protection
Deletion Protection
Optional Signed Commits
```

Jangan mengarang bahwa protection tersebut sudah aktif apabila belum diverifikasi dari
repository hosting configuration.

## CODE OWNERSHIP / REVIEW OWNERSHIP

Jika repository mempunyai ownership map seperti `CODEOWNERS` atau mekanisme setara:

- perubahan pada bootstrap, ABI, safety, compiler trust, release pipeline, atau build
  reproducibility harus meminta review dari owner yang relevan;
- absence of owner tidak boleh menjadi alasan untuk mengklaim review sudah terjadi;
- ownership file membantu routing review, tetapi **tidak menggantikan test**.

Jika repository belum mempunyai ownership map, jangan membuat nama owner palsu.
Sebagai gantinya, laporkan:

```text
Review Owner Mapping: NOT DEFINED
Recommended Areas:
- Bootstrap / Trust
- Frontend / Semantics
- IR / Backend
- Runtime / Safety
- Build / Release
- Tooling / CLI
```

---

# CI / TEST GOVERNANCE

Continuous Integration adalah evidence automation, bukan sumber kebenaran absolut.
Test yang benar tetap harus memiliki kontrak yang dapat dipahami dan direproduksi.

## Required CI Properties

CI yang digunakan sebagai merge/release gate harus sebisa mungkin:

```text
Deterministic enough to interpret
Re-runnable
Fail-closed for required checks
Log commands and environment
Preserve relevant artifacts/logs
Distinguish test failure from infrastructure failure
Run the test suite appropriate to change risk
```

Jangan menganggap status hijau sebagai bukti fitur bekerja jika check yang relevan
ternyata tidak dijalankan.

## Test Scope by Change Class

```text
Patch
→ Targeted + Impacted Regression

Minor
→ Targeted + Subsystem + Relevant Regression

Major
→ Full Relevant Regression + Architecture/Compatibility Gates

Hotfix
→ Reproducer + Fix Regression + Full Relevant Security/Correctness Gate

Architecture Reset
→ Baseline Re-establishment + Full Validation
```

## FLAKY TEST POLICY

Flaky test tidak boleh:

- dihapus diam-diam;
- di-skip permanen hanya agar CI hijau;
- dianggap PASS hanya karena retry akhirnya sukses;
- disembunyikan sebagai infrastructure noise tanpa evidence.

Jika test terindikasi flaky:

```text
Test:
Observed Failure Pattern:
Reproduction Rate:
Environment:
Root Cause Known:
Quarantined:
Quarantine Reason:
Owner / Follow-up:
Exit Criteria:
```

Quarantine hanya boleh dipakai sementara jika:

1. test tidak lagi dapat dipercaya sebagai merge gate;
2. failure sudah dicatat;
3. feature correctness masih mempunyai coverage alternatif yang cukup;
4. ada follow-up yang jelas untuk memperbaiki atau mengganti test.

Jika test menyangkut:

```text
Miscompile
Bootstrap Trust
Memory Safety
ABI
Artifact Integrity
```

jangan quarantine sebagai cara melewati release blocker.

## CI INFRASTRUCTURE FAILURE

Bedakan:

```text
TEST FAILURE
```

dengan:

```text
INFRASTRUCTURE FAILURE
```

Infrastructure failure dapat mencakup runner hilang, disk penuh, network dependency
outage, permission problem, atau service eksternal unavailable.

Jangan mengubah expected result test hanya karena CI infrastructure bermasalah.

---

# DEPENDENCY & SOFTWARE SUPPLY-CHAIN POLICY

NolQu-L ingin mempunyai bootstrap chain yang dapat ditelusuri, sehingga dependency
policy harus lebih ketat daripada sekadar "build berhasil".

Klasifikasikan dependency menjadi:

```text
Canonical Build Dependency
Host Inspection/Test Dependency
Runtime Dependency
Development Dependency
Optional Tooling Dependency
Legacy/Reference Dependency
```

Setiap dependency baru yang relevan harus menjawab:

```text
Name:
Purpose:
Class:
Required at Build Time:
Required at Runtime:
Version Constraint:
Source / Origin:
License if relevant:
Security/Trust Impact:
Bootstrap Impact:
Reproducibility Impact:
Removal / Replacement Possibility:
```

## Canonical Dependency Rule

Dependency baru **tidak boleh masuk canonical bootstrap chain** hanya karena praktis.

Sebelum dependency canonical baru diterima, evaluasi:

```text
Can this be removed?
Can this be reproduced?
Can this be audited?
Does it introduce hidden compilation?
Does it weaken traceability?
Does it change the trust root?
Can previous stage still explain the next stage?
```

Host tool untuk inspection/test tidak otomatis menjadi semantic dependency.
Dokumentasikan perbedaannya secara eksplisit.

## Dependency Drift

Jika dependency version berubah:

- catat alasan;
- jalankan impacted tests;
- periksa artifact/reproducibility impact;
- periksa behavior/ABI jika dependency dapat mempengaruhi output;
- jangan menerima "latest" yang tidak pinned pada release-critical build jika hal itu
  membuat hasil tidak dapat direproduksi.

Jangan membuat pin palsu jika repository saat ini memang belum mempunyai dependency
locking mechanism.

## SBOM / BOM

Untuk public release yang mempunyai dependency nontrivial, pertimbangkan menghasilkan
Software Bill of Materials atau Bill of Materials dengan format standar yang sesuai.

SBOM **bukan pengganti** dependency review, vulnerability handling, atau provenance.

Jika SBOM belum diimplementasikan:

```text
SBOM Status: NOT IMPLEMENTED
```

jangan mengklaim release mempunyai SBOM hanya karena dependency list ada di README.

---

# RELEASE ARTIFACT INTEGRITY & PROVENANCE

Release artifact harus dapat ditelusuri ke source dan build process yang menghasilkan
artifact tersebut.

Minimum release-artifact metadata yang dianjurkan:

```text
Release Version
Source Revision / Commit
Source Tree State
Build Command
Build Environment
Target
Artifact Filename
Artifact Size
Cryptographic Hash
Compiler / Bootstrap Generation
Relevant Build Flags
Reproducibility Status
Provenance Status
Signing Status
SBOM Status
```

## Hashes

Public binary/archive release sebaiknya mempunyai cryptographic hash yang dipublikasikan
bersama artifact.

Hash membuktikan identity/integrity bytes yang dibandingkan, tetapi **tidak sendiri
membuktikan siapa yang membangun artifact atau dari source mana artifact berasal**.

## Provenance

Jika provenance tersedia, provenance harus menghubungkan artifact dengan informasi build
seperti:

```text
Source Revision
Build Definition
Builder / Build Environment
External Parameters
Produced Artifact
```

Gunakan provenance untuk meningkatkan traceability, bukan sebagai label marketing.

Jika belum tersedia:

```text
Provenance: NOT IMPLEMENTED
```

## Artifact Signing

Signing adalah optional capability sampai NolQu-L menetapkan signing policy formal.

Jika signing digunakan:

- verification procedure harus didokumentasikan;
- identity/trust model signer harus jelas;
- signature tidak boleh menggantikan reproducibility;
- keyless/signing service atau local-key model boleh dipilih berdasarkan architecture
  repository, tetapi jangan mengarang sistem yang belum digunakan.

Status harus eksplisit:

```text
Artifact Signing: ENABLED / DISABLED / NOT IMPLEMENTED
```

## Release Artifact Promotion

Artifact hanya boleh dipromosikan menjadi official release artifact jika:

```text
Version matches source
Hash recorded
Release gate passed
Artifact not replaced after publication
Known provenance/signing state documented
```

Jika artifact harus diganti setelah publish:

```text
DO NOT silently overwrite.
→ create corrected release/version
→ explain reason
→ publish new hashes/evidence
```

---

# SECURITY VULNERABILITY HANDLING

Bagian ini mengatur lifecycle vulnerability pada compiler, runtime, tooling, package
infrastructure, dan release process.

## Security Report Classification

Bedakan:

```text
Security Vulnerability
Correctness Bug
Reliability Bug
Hardening Opportunity
False Positive
```

Jangan menaikkan severity hanya karena issue terdengar serius, dan jangan menurunkannya
untuk menjaga release schedule.

## Minimum Vulnerability Record

```text
Affected Component:
Affected Versions:
Impact:
Preconditions:
Severity / Priority:
Reproduction Status:
Root Cause:
Fix Status:
Regression Test:
Disclosure Status:
Release Required:
Backport Required:
Known Workaround:
```

Jangan mempublikasikan detail exploit operasional yang tidak diperlukan untuk pengguna
memperbaiki sistem. Security advisory publik harus fokus pada impact, affected versions,
fix, mitigation, dan upgrade path.

## Security Release Rule

Jika stable release terdampak vulnerability nyata:

```text
Assess
→ Contain
→ Fix
→ Regression Test
→ Determine Backport
→ Prepare Security Release
→ Publish Advisory / Changelog
```

Security patch yang backward-compatible biasanya dapat menjadi patch release, kecuali
fix membutuhkan breaking contract change.

## Embargo / Private Handling

Jika repository mempunyai private vulnerability-reporting process, ikuti process itu.
Jika tidak ada, jangan mengarang channel atau SLA.

Laporkan:

```text
Private Security Reporting: DEFINED / NOT DEFINED
```

---

# SUPPORT, MAINTENANCE & END-OF-LIFE POLICY

Versioning tanpa support policy dapat membuat status "stable" ambigu.

Jika NolQu-L belum mempunyai jangka support numerik formal, jangan mengarang tanggal.
Gunakan status lifecycle terlebih dahulu:

```text
DEVELOPMENT
SUPPORTED
MAINTENANCE
SECURITY-ONLY
END-OF-LIFE
```

## SUPPORTED

- bugfix normal diterima;
- security fix diterima;
- compatibility commitment sesuai release maturity berlaku.

## MAINTENANCE

- fokus pada correctness, compatibility, dan important regression;
- feature baru biasanya diarahkan ke line yang lebih baru.

## SECURITY-ONLY

- hanya vulnerability/security-critical correctness fix yang direncanakan;
- behavior ini harus diumumkan eksplisit.

## END-OF-LIFE

- tidak ada janji maintenance/security update;
- dokumentasi harus mengarahkan pengguna ke supported line jika tersedia;
- EOL tidak berarti artifact lama harus dihapus dari history.

Jika support duration nantinya dibuat formal, dokumentasikan:

```text
Release Line:
Support Start:
Maintenance Until:
Security Until:
EOL Date:
Upgrade Target:
```

Perubahan support policy sendiri adalah release/project governance decision dan harus
dicatat dalam dokumentasi publik.

---

# DOCUMENTATION & COMPATIBILITY LIFECYCLE

Dokumentasi harus mengikuti maturity yang sama dengan implementation.

Untuk setiap capability penting, bedakan:

```text
Designed
Implemented
Tested
Documented
Stable
Deprecated
Removed
```

Jangan memakai satu status untuk menggantikan status lain.

Contoh:

```text
Implemented: YES
Tested: YES
Stable: NO
```

adalah status yang valid untuk feature experimental/preview.

## Documentation Version Scope

Dokumentasi user-facing harus menyebut versi atau maturity scope jika behavior dapat
berbeda antar release.

Jika docs menggambarkan target architecture yang belum implemented, labeli:

```text
TARGET / PLANNED
```

bukan:

```text
CURRENT
```

## Compatibility Promise Lifecycle

Sebuah behavior baru tidak otomatis menjadi stable compatibility promise saat pertama
implemented.

Flow yang dianjurkan:

```text
Experimental
→ Preview
→ Stable
→ Deprecated
→ Removed
```

Promosi ke `Stable` harus mempertimbangkan:

```text
Semantics clear
Tests complete
Diagnostics adequate
Compatibility understood
Documentation complete
Implementation mature
No known critical blocker
```

## Documentation Drift

Jika code/test dan docs berbeda:

1. tentukan source of truth sesuai bagian otoritas;
2. jangan otomatis mengubah test hanya agar cocok docs;
3. jangan otomatis mengubah docs hanya agar cocok implementation yang mungkin bug;
4. selesaikan conflict melalui evidence dan design intent;
5. update seluruh reference yang terdampak setelah keputusan final.


---


# RELEASE BRANCH, FEATURE FREEZE & BACKPORT POLICY

Release preparation membutuhkan boundary yang berbeda dari normal development.
Jangan terus memasukkan feature baru hanya karena branch release masih dapat dibangun.

## Release Branch

Jika repository menggunakan release branch, statusnya harus eksplisit:

```text
Release Branch:
Source Revision:
Release Line:
Branch Created From:
Release Candidate:
Allowed Change Classes:
Required Review:
Required Test Gate:
```

Jangan mengarang release branch jika repository belum memilikinya.

## Feature Freeze

Feature freeze berarti:

```text
New ordinary features
→ STOP for this release line

Bugfix / regression fix / release-blocking correction
→ MAY continue under release gate
```

Setelah freeze:

- feature baru yang belum selesai harus ditunda, dinonaktifkan, atau dikeluarkan dari release;
- perubahan besar yang tidak release-blocking tidak boleh masuk hanya karena sudah hampir selesai;
- risk tolerance harus semakin kecil ketika release mendekati final;
- documentation, migration, regression, packaging, dan release evidence menjadi prioritas.

Stage yang dianjurkan:

```text
Development
→ Feature Complete
→ Feature Freeze
→ RC1
→ RC2 / later RC if required
→ Final
```

Jangan menggunakan jadwal ini sebagai klaim bahwa repository sudah menjalankan release process tersebut.

## Release Candidate Change Budget

### Before RC1

Boleh mempertimbangkan:

- bugfix;
- completion fitur yang memang sudah masuk release scope;
- low-risk performance fix;
- documentation/release correction.

### RC1 → RC2

Prioritaskan:

- regression fix;
- correctness fix;
- compatibility fix;
- release-blocking diagnostic/build issue;
- security fix.

### Late RC → Final

Batasi pada:

```text
Critical Correctness
Critical Regression
Security
Release Packaging / Metadata Correction
```

Perubahan besar menjelang final lebih baik ditunda daripada memaksa release dengan
surface area baru yang belum mendapat burn-in cukup.

## Backport Policy

Backport ke stable/release branch harus lebih konservatif daripada perubahan di mainline.

Sebelum backport:

```text
Original Change:
Target Release Line:
Reason:
User Impact:
Risk:
API Compatibility:
ABI Compatibility:
Bootstrap Impact:
Regression Test:
Conflicts / Adaptation:
```

Backport tidak boleh dipakai untuk menyelundupkan feature baru ke stable line.

---

# COMPILER VALIDATION STRATEGY — FUZZ, PROPERTY & DIFFERENTIAL TESTING

Unit/integration tests tidak cukup untuk menemukan seluruh kelas compiler bug.
Gunakan metode tambahan secara bertahap ketika infrastructure sudah memungkinkan.

## Fuzz Testing

Fuzzing dapat digunakan untuk mencari:

```text
ICE / compiler crash
Parser non-progress
Infinite loop
Malformed input handling
Bounds failure
Unexpected acceptance
Unexpected rejection
Miscompile candidates
```

Fuzzer-generated failure harus direduksi menjadi reproducer minimal bila memungkinkan.

Catat:

```text
Seed / Corpus:
Generator / Fuzzer:
Target:
Build:
Reproducer:
Expected:
Observed:
Minimized:
Regression Test Added:
```

Jangan menyebut fuzzing berhasil hanya karena menjalankan fuzzer beberapa detik tanpa crash.

## Property-Based Testing

Jika sesuai, definisikan invariant yang dapat diuji terhadap banyak generated input.

Contoh property compiler:

```text
parse(print(AST)) preserves intended structure
valid normalization remains semantically equivalent
optimization does not change observable behavior
same source + same build inputs → deterministic artifact
invalid bounded input never causes compiler crash
```

Property harus merupakan invariant nyata, bukan sekadar test yang dibuat generik.

## Differential Testing

Jika terdapat independent reference/oracle yang cukup dipercaya, gunakan differential testing
untuk menemukan divergence.

Contoh NolQu-L:

```text
Reference Compiler R0
vs
Canonical Compiler Stage
```

atau:

```text
Unoptimized
vs
Optimized
```

Bandingkan hanya behavior yang memang berada pada semantic overlap kedua implementation.

Divergence tidak otomatis berarti compiler baru salah. Lakukan triage:

```text
New Compiler Bug
Reference Bug
Undefined / Unspecified Behavior
Test Bug
Intentional Semantic Change
```

Jangan menjadikan R0 sebagai canonical dependency hanya karena dipakai sebagai oracle test.

---

# SUPPORTED TARGET TIERS & RELEASE QUALIFICATION

Target support harus dibedakan dari "backend code exists".

Gunakan maturity support yang eksplisit jika multi-target mulai berkembang:

```text
TIER 1 — Release Blocking / Fully Qualified
TIER 2 — Supported / Regularly Tested
TIER 3 — Experimental / Best Effort
UNSUPPORTED — No Compatibility Promise
```

Jangan membuat tier palsu jika project masih hanya mempunyai satu target utama.

## Tier 1

Sebuah target dapat dianggap Tier 1 hanya jika:

- build/test rutin tersedia;
- release artifact dapat divalidasi jika project memang mendistribusikannya;
- ABI/system assumptions terdokumentasi;
- regression pada target tersebut dapat memblokir release sesuai policy;
- maintainer/support capability nyata tersedia.

## Tier 2

- backend dianggap supported;
- testing reguler ada;
- release artifact dapat optional;
- failure penting harus ditangani, tetapi tidak setiap infrastructure issue otomatis release-blocking.

## Tier 3

- experimental;
- dapat berubah;
- tidak boleh dipresentasikan setara Tier 1;
- breakage harus tetap dicatat jika diketahui.

Jika target belum diklasifikasikan:

```text
Target Support Tier: NOT FORMALLY DEFINED
```

---

# DOWNSTREAM & ECOSYSTEM COMPATIBILITY CHECKS

Compiler dapat terlihat benar pada test suite internal tetapi tetap merusak source nyata.
Ketika ecosystem sudah cukup besar, tambahkan downstream/canary validation.

Candidate downstream set dapat mencakup:

```text
Standard Library
Runtime
Official Tools
Representative Example Projects
Known Large NolQu-L Programs
Bootstrap Sources
FFI Fixtures
Package/Module Fixtures
```

Untuk perubahan compiler signifikan:

```text
Internal Tests
        +
Bootstrap Tests
        +
Downstream Canary Builds
        ↓
Compatibility Confidence
```

Jangan memasukkan third-party project ke required gate tanpa izin, reproducibility,
dan maintenance plan yang jelas.

Jika belum ada ecosystem downstream yang cukup:

```text
Downstream Compatibility Suite: NOT YET ESTABLISHED
```

---

# ARTIFACT & EVIDENCE RETENTION POLICY

Evidence release/bootstrap tidak berguna jika hilang setelah beberapa minggu.

Untuk release penting atau bootstrap promotion, pertahankan bila feasible:

```text
Source Revision
Release Notes
Checksums
Canonical Artifact
Build Logs
Test Summary
Bootstrap Hashes
Reproducibility Result
Provenance / Attestation if available
SBOM if available
Security Advisory if applicable
Migration Guide if applicable
```

## Retention Rule

Jangan mengarang retention period numerik jika project belum menetapkannya.
Gunakan status:

```text
Retention Policy: DEFINED / PARTIAL / NOT DEFINED
```

Artifact lama boleh dipindah ke archive, tetapi archive harus tetap membedakan:

```text
SUPPORTED
EOL
HISTORICAL / BOOTSTRAP EVIDENCE
```

Jangan menghapus artifact/hash yang masih diperlukan untuk menjelaskan canonical bootstrap chain.

---

# SIGNING TRUST & KEY LIFECYCLE

Jika artifact signing tidak digunakan, bagian ini tetap `NOT IMPLEMENTED` dan tidak menjadi blocker
kecuali release policy secara eksplisit mewajibkannya.

Jika signing diaktifkan, definisikan:

```text
Signing Model:
Trust Root:
Who/What May Sign:
Verification Method:
Key / Identity Rotation:
Compromise Procedure:
Revocation / Replacement Procedure:
Historical Verification:
```

Key/identity rotation tidak boleh membuat release lama menjadi tidak dapat diverifikasi tanpa penjelasan.

Jika signing credential dicurigai compromised:

```text
STOP normal signing
→ contain credential
→ identify affected artifacts
→ rotate / revoke according to actual system
→ publish correction/advisory if needed
→ preserve forensic evidence
```

Jangan menyimpan private key material di dokumentasi, repository, test fixture, atau prompt ini.

---

# INCIDENT REVIEW & CORRECTIVE-ACTION POLICY

Bug besar, security incident, bootstrap trust failure, atau release regression serius
harus menghasilkan pembelajaran yang dapat mencegah pengulangan.

Setelah containment/fix, lakukan review yang proporsional.

Template:

```text
Incident:
Impact:
Affected Versions / Stages:
Detection:
Timeline:
Root Cause:
Contributing Factors:
Why Existing Tests/Gates Missed It:
Containment:
Fix:
Regression Test:
Corrective Actions:
Owner / Tracking:
Completion Evidence:
```

Post-incident review bukan tempat mencari kambing hitam.
Fokus pada system/process failure dan tindakan preventif.

Corrective action dapat berupa:

```text
New Test
New Invariant
New Static Check
New Review Gate
Documentation Clarification
Architecture Change
Dependency Policy Change
Release Gate Change
```

Jangan menutup corrective action hanya karena original bug sudah fixed.

---

# GOVERNANCE EXCEPTION / WAIVER POLICY

Governance yang tidak mempunyai exception process cenderung dilanggar diam-diam ketika keadaan darurat.
Karena itu exception harus **eksplisit, terbatas, dan dapat diaudit**.

Waiver hanya boleh digunakan jika:

- ada alasan teknis/operasional yang jelas;
- normal gate benar-benar tidak dapat dipenuhi pada saat itu;
- risiko dipahami;
- scope waiver sekecil mungkin;
- ada compensating control bila memungkinkan;
- ada expiry atau follow-up condition.

Template:

```text
Waiver:
Rule Bypassed:
Reason:
Scope:
Risk:
Compensating Control:
Approved By / Authority:
Start:
Expiry / Exit Condition:
Follow-up:
Evidence:
```

Waiver tidak boleh digunakan untuk:

```text
Hide known regression
Fake PASS
Ignore miscompile
Ignore silent corruption
Bypass bootstrap trust failure
Suppress security issue
Avoid migration for intentional breaking change
```

Jika project belum mempunyai governance authority formal:

```text
Waiver Authority: NOT FORMALLY DEFINED
```

Jangan mengarang approval.

---

# RELEASE AUTHORITY & PROMOTION RESPONSIBILITY

Release harus mempunyai satu authority yang jelas, walaupun project hanya dikelola satu orang.

Role dapat berupa:

```text
Release Maintainer
Release Manager
Project Maintainer
```

Nama role dapat disesuaikan dengan repository yang nyata.

Responsibility minimum:

- memastikan release gate dijalankan;
- memastikan version/tag/artifact konsisten;
- memastikan blocker tidak disembunyikan;
- memastikan changelog/migration/known issues siap;
- memutuskan promotion RC → Final berdasarkan evidence;
- mencatat exception/waiver jika ada.

Jika belum ada role formal:

```text
Release Authority: NOT FORMALLY DEFINED
```

Jangan mengarang nama orang atau approval yang tidak ada.

---

# RELEASE-BLOCKING CRITERIA

Perubahan/release harus dihentikan jika ada:

```text
Unexplained Miscompile
Silent Data Corruption
Critical Safety Invariant Failure
Bootstrap Trust Failure
Unexpected Non-Determinism
Unresolved Security Boundary Failure
Unexplained ABI Break
Regression from Baseline
Artifact/Version Mismatch
Missing Migration for Intentional Breaking Change
Fake PASS / Placeholder Evidence
```

`DEFERRED` tidak boleh digunakan untuk release blocker.

---

# PERFORMANCE / RESOURCE REGRESSION POLICY

Dokumen ini sudah mewajibkan benchmark untuk klaim performa.
Tambahkan aturan:

- jangan menetapkan threshold numerik palsu jika belum ada baseline;
- gunakan baseline nyata;
- bandingkan workload yang sama;
- catat environment;
- bedakan compile-time, runtime, peak memory, binary size, startup, dan I/O;
- regression signifikan harus dijelaskan dan diterima eksplisit atau diperbaiki;
- improvement satu metric tidak boleh menyembunyikan regression besar metric lain.

Template:

```text
Metric:
Baseline:
After:
Workload:
Environment:
Variance:
Expected:
Observed:
Regression:
Accepted:
Reason:
```

Untuk bootstrap, ukur juga bila relevan:

```text
Artifact Size
Source Capacity
Patch/Table Capacity
Build Determinism
Generation Time
```

Jangan menaikkan capacity hanya "untuk jaga-jaga".
Capacity bridge harus mempunyai kebutuhan terukur seperti aturan bootstrap yang sudah ada.

---

# ROLLBACK / REVERT POLICY

Tidak semua failure harus dipaksa diperbaiki di atas perubahan yang sudah terlalu besar.

Pertimbangkan revert/rollback jika:

- regression root cause belum dipahami;
- change memutus stable contract tanpa approval;
- security/correctness risk meningkat;
- bootstrap chain menjadi tidak dapat diverifikasi;
- migration ternyata tidak feasible;
- implementation meninggalkan repository dalam mixed architecture;
- fix membutuhkan workaround baru yang lebih buruk daripada perubahan awal.

Rollback bukan kegagalan proses.

```text
Unsafe / Unclear Change
        ↓
Revert to Known-Good Baseline
        ↓
Preserve Evidence
        ↓
Redesign / Re-plan
```

Jangan menghapus evidence failure hanya karena perubahan direvert.

---

# BASELINE IMMUTABILITY DURING SESSION

Setelah baseline dicatat, jangan mengubah definisi baseline agar perubahan terlihat berhasil.

Catat:

```text
Baseline Commit / Snapshot:
Working Tree State:
Known Failures:
Canonical Manifest State:
Compiler Version:
Bootstrap Milestone:
Relevant Artifact Hashes:
Test Commands:
```

Jika baseline berubah karena alasan eksternal, catat sebagai baseline baru dan jelaskan.

---

# CHANGE COMPLETION RULE

Sebuah update belum selesai hanya karena code compile.

Update selesai jika sesuai scope:

```text
Implementation
+
Targeted Tests
+
Relevant Regression
+
Compatibility Check
+
Documentation
+
Architecture Consistency
+
Evidence
+
Known Limitations
+
Next Measured Blocker
```

Tambahan sesuai class:

```text
Patch
→ root cause + regression proof

Minor
→ capability + compatibility + subsystem proof

Major
→ architecture + migration + cross-subsystem proof

Hotfix
→ containment + correctness/security regression proof

Architecture Reset
→ old/new contract + migration + full validation
```

---

# WHEN TO STOP ADDING FEATURES

Berhenti dan stabilisasi jika:

- regression meningkat;
- test coverage tertinggal;
- contract belum terdokumentasi;
- blocker belum dipahami;
- complexity tumbuh lebih cepat daripada capability;
- milestone scope terlewati;
- determinism belum terbukti;
- error path belum diuji;
- capacity dinaikkan tanpa kebutuhan terukur;
- semantic behavior tidak mempunyai evidence/oracle;
- terlalu banyak feature experimental saling bergantung.

Gunakan:

```text
Capability
→ Stabilize
→ Verify
→ Document
→ Measure Next Blocker
→ Continue
```

bukan:

```text
Capability
→ More Features
→ More Features
→ More Features
→ Unknown State
```

---

# WHEN TO REDESIGN

Redesign diperbolehkan jika evidence menunjukkan architecture sekarang:

- menghalangi milestone berikutnya secara fundamental;
- menghasilkan complexity debt yang terus bertambah;
- melanggar Nine Pillars;
- tidak dapat diverifikasi;
- membuat self-hosting praktis mustahil;
- membutuhkan hidden host dependency;
- menyebabkan semantic ambiguity;
- tidak dapat mempertahankan predictable machine behavior;
- membutuhkan workaround khusus baru untuk setiap feature.

Redesign tidak dibenarkan hanya karena solusi lain terlihat lebih modern/elegan.

Required:

```text
Observed Problem
Evidence
Architectural Cause
Alternatives
Migration Cost
Compatibility Cost
Expected Benefit
Failure Modes
Rollback Plan
```

---

# GOVERNANCE DECISION TREE

Gunakan decision tree ini sebelum implementation:

```text
Apakah ada security/correctness/trust failure kritis?
│
├── YES → Security / Correctness Hotfix
│
└── NO
     │
     ▼
Apakah hanya memperbaiki documented behavior tanpa contract change?
│
├── YES → Patch / Repair
│
└── NO
     │
     ▼
Apakah additive dan tetap di architecture/contract yang sama?
│
├── YES → Minor Development
│
└── NO
     │
     ▼
Apakah mengubah semantics, ABI, bootstrap, safety, public contract,
atau beberapa subsystem secara substantif?
│
├── YES → Major Development
│
└── NO
     │
     ▼
Apakah contract fundamental lama harus diganti?
│
├── YES → Architecture Reset
│
└── NO → Re-evaluate scope/evidence
```

Version decision dilakukan **setelah** technical classification:

```text
Public contract unchanged bugfix
→ Patch version candidate

Backward-compatible public addition/deprecation
→ Minor version candidate

Backward-incompatible stable public contract
→ Major version candidate
```

Tidak setiap development session harus menghasilkan release.

---

# GOVERNANCE OUTPUT REQUIRED

Setiap sesi development harus menutup dengan:

```text
Update Class:
Risk Level:
Primary Scope:
Affected Subsystems:
Public Contract Impact:
Compatibility Matrix:
Bootstrap Impact:
Security/Trust Impact:
Performance/Resource Impact:
RFC Required:
ADR Required:
Version Impact:
Release Maturity:
Release Blocking Issues:
Changelog Required:
Migration Required:
Rollback/Revert Required:
Review Required:
Review Status:
CI Required Checks:
CI Status:
Flaky Test Status:
Dependency/Supply-Chain Impact:
SBOM Status:
Provenance Status:
Artifact Signing Status:
Support Lifecycle Impact:
Security Advisory Required:
Tests Required:
Tests Executed:
Evidence:
Known Limitations:
Next Measured Blocker:
```

Jangan menyatakan `NONE` tanpa alasan jika axis tersebut secara jelas terdampak.


---

# CURRENT ARCHITECTURE RESET

Bagian ini mencatat keputusan repository yang berlaku mulai 2026-08-21.
Otoritas desain aktif diselaraskan pada 2026-10-12 ke `NolQu-LConcept.docx`
dan dokumen revisi ini, termasuk Pillar 8 tentang evolusi kompatibilitas;
sedangkan test yang valid tetap menjadi otoritas perilaku implementasi.

## Nama dan Identitas

- Nama formal bahasa dan arsitektur adalah **NolQu-L**.
- Ejaan lama dipertahankan hanya di history, evidence, dan nama artifact
  bootstrap yang belum dapat dimigrasikan tanpa mengubah kontrak byte.
- `.nql` adalah extension source canonical.
- `nql` adalah executable project manager/run command; `nolqul` adalah symlink
  nama panjang yang menunjuk ke `nql`.
- `nqlc` adalah executable compiler; `nolqulc` adalah symlink nama panjang yang
  menunjuk ke `nqlc`.
- Tidak ada command publik `nq`, `nqc`, `nolqu`, atau `nolquc`. Khususnya,
  `nqc -> nolquc` bukan bagian arsitektur NolQu-L dan tidak boleh dibuat.
- Source `.nq` yang masih ada merupakan corpus/bootstrap historis, bukan
  penentu nama CLI canonical.

## Jalur Canonical

Satu-satunya jalur bootstrap canonical adalah:

```text
Machine-Level Foundation
        ↓
Stage 0
        ↓
NolQu-L Bootstrap Compiler
        ↓
NolQu-L Core Compiler
        ↓
Full NolQu-L Compiler (`nqlc`)
        ↓
Self-Hosting `nqlc`
        ↓
Verified `nqlc`
```

LLVM, Python, NASM, C, C++, Rust, GCC, Clang, dan compiler bahasa lain tidak
boleh menjadi tahap tersembunyi dalam rantai canonical tersebut. Tool host
boleh dipakai untuk inspeksi, test, atau merekonstruksi seed yang bytes-nya
sudah ditetapkan, tetapi dependency itu harus disebut eksplisit dan tidak
boleh disamakan dengan dependency semantik compiler.

## Klasifikasi Implementasi Repository

| Komponen | Status | Bukti / Peran |
| --- | --- | --- |
| Machine-Level Foundation x86_64 Linux | **PASS** | `bootstrap/machine/x86_64-linux/hex0.seed`, hash, self-decoding, dan `tests/bootstrap/machine_foundation.sh` |
| Stage 0 | **PASS** | `bootstrap/stage0/x86_64-linux/stage0.seed`, dibangun oleh `hex0.seed`, self-reconstruction, symbol resolution, runnable ELF generation, dan `tests/bootstrap/stage0.sh` |
| NolQu-L Bootstrap Compiler | **PASS** | `bootstrap/compiler/b0/x86_64-linux/b0.seed`, dibangun oleh Stage 0, hash cocok, dan `tests/bootstrap/bootstrap_compiler_b0.sh` |
| NolQu-L Core Compiler | **PASS** | `bootstrap/compiler/c0/x86_64-linux/c0.seed`, dibangun secara semantik oleh B0, hash cocok, dan `tests/bootstrap/core_compiler_c0.sh` |
| C0.30 source frontend | **PASS** | `c0-frontend.seed`, B0-built, NQAF/1..4 dan `tests/bootstrap/c0_frontend.sh` |
| C0.30 AST backend/runtime | **PASS** | `c0-backend.seed`, B0-built, ELF langsung, byte/stream I/O dan `tests/bootstrap/c0_backend.sh` |
| Full NolQu-L Compiler canonical | **NOT IMPLEMENTED** | Compiler di `src/*.asm` bukan tahap canonical |
| Self-Hosting `nqlc` | **NOT IMPLEMENTED** | Belum dapat dibangun oleh generasi NolQu-L sebelumnya |
| Verified `nqlc` | **NOT IMPLEMENTED** | Belum ada reproducible multi-generation comparison |

Compiler x86_64 NASM yang sudah ada di `src/*.asm` diklasifikasikan sebagai
**Reference Compiler R0**. R0 tetap dipertahankan karena mempunyai coverage
test luas dan berguna sebagai semantic oracle, tetapi R0 tidak boleh disebut
Stage 0 atau bukti self-hosting.

Semua jalur LLVM dan Python di `tools/`, `tests/llvm/`, dan `tests/ir/`
diklasifikasikan sebagai **legacy compatibility/reference paths**. Jalur itu
boleh dipelihara agar test lama tetap hijau, tetapi tidak lagi dikembangkan
sebagai arah arsitektur NolQu-L dan tidak berada dalam rantai canonical.

## Milestone Aktif

Stage 0 yang aktif sejak Machine-Level Foundation sekarang selesai dan tetap
dibatasi sebagai symbolic flat-binary emitter yang kecil serta dapat diaudit.
Implementasinya telah membuktikan:

1. membaca format input bootstrap yang terdokumentasi,
2. melakukan basic instruction emission,
3. menangani memory operation dan control flow minimum,
4. menyelesaikan symbol secara deterministik,
5. menghasilkan executable atau compiler generasi berikutnya,
6. menolak input invalid dengan exit code non-zero dan diagnostic jelas,
7. dan dibangun dari `hex0.seed` tanpa compiler, assembler, linker, Python,
   atau LLVM eksternal.

Kontrak Stage 0 berada di `bootstrap/stage0/README.md`. Source menerima byte
heksadesimal, definisi label, patch `rel32`, virtual address berbasis
`0x400000`, dan file offset. Stage 0 memakai dua pass, buffer berbatas tetap,
diagnostic dengan byte offset, serta `mmap`/`munmap` eksplisit. Manifest
`stage0.hex` dibangun oleh `hex0.seed`, dan `stage0.seed` menghasilkan ulang
manifest itu menjadi executable yang byte-for-byte identik.

Core Compiler emitter sampai subfase C0.25 sekarang PASS; frontend/backend
aktif adalah C0.30. `frontend.nql` dibangun oleh B0 menjadi `c0-frontend.seed`:
source lengkap menjadi AST precedence NQAF/1..4, dengan `let`, assignment,
`return`, perbandingan, kontrol alur, function, call bersarang dan call statement.
`backend.nql` memvalidasi AST/nesting, menyelesaikan local/parameter mutable i64,
dan menghasilkan ELF syscall-only dengan checked arithmetic, branch dan call
native, termasuk rekursi. Runtime byte/stream memakai arena stack 65.536 byte,
range checks dan syscall langsung; user function tetap mendahului intrinsic.
Batas saat ini enam parameter dan 64 frame aktif.
Kedua komponen dibangun B0; belum Full Compiler atau self-hosting. Kontrak ada
di `bootstrap/compiler/c0/FRONTEND.md`, `BACKEND.md`, `CONTROL_FLOW.md` dan
`FUNCTIONS.md` serta `RUNTIME_IO.md`. Hasil gate C0.30 dicatat pada work unit
di akhir dokumen.
Artifact emitter C0.25 tidak berubah; kedua seed komponen diupgrade dengan pin.
B0 membangun `compiler.nq`
menjadi `c0.seed` tanpa compiler atau assembler host. C0 sekarang melakukan
tokenisasi bounded, menyimpan offset source, memeriksa expression u8 `+`/`*`
dengan precedence, memproses beberapa `let` local integer, menyelesaikan
binding secara collision-free, mendecode string bounded, dan menurunkan
`write` menjadi executable syscall-only. C0.3a menambah byte-memory runtime
256 byte, `input_read`, `byte_store`, dan `byte_load` dengan pemisahan segment
RX/RW. C0.3b menambah assignment byte dinamis dan `while` non-nested dengan
conditional exit serta backward `rel32` nyata. C0.3c menambah
`output_write(offset, count)` yang ordered, bounded, complete-write, dan aman
terhadap `SIGPIPE`, termasuk di dalam loop. C0.3d menyatukan literal `write`
dengan operation stream runtime dan membangun successor source-consuming
pertama. C0.4 menambah `byte_assert_range`, mengganti source mesin satu byte
dengan grammar textual exact `<digit> LF EOF`, serta membuktikan artifact
valid dan penolakan invalid secara deterministik. B0.7j hanya menaikkan arena
source ke 131.072 byte agar C0.4 tetap dapat dibangun oleh predecessor.
C0.5 memperluas source itu menjadi grammar located exact
`return SP <digit> LF EOF` dan menaikkan bound source C0 menjadi 1.536 byte.
C0.6 menerima `return SP <digit><digit> LF EOF`, menurunkan nilai `00..99`
melalui dua loop byte-memory bounded, dan menaikkan bound token dari 192 ke
240 tanpa mengubah batas 32 operation. C0.7 menambahkan intrinsic mesin
`byte_parse_u8`, memperluas grammar successor menjadi satu sampai tiga digit
untuk seluruh `0..255`, serta memindahkan enam tabel token ke arena disjoint
setelah gate high-offset membuktikan overlap lama. B0.7k hanya menaikkan arena
output ke 196.608 byte agar artifact C0.7 sebesar 134.891 byte tetap dibangun
oleh predecessor. C0.8 menjalankan probe rebuild nyata, menambahkan intrinsic
`byte_parse_u8_then`, dan memperluas successor sampai envelope exact
`fn main(){ LF return SP <decimal-u8> } LF EOF`. Pertumbuhan codegen membuka
overlap laten antara code target dan scratch literal; scratch tersebut sudah
dipindahkan ke arena byte 18.000 yang disjoint. Probe ulang sekarang melewati
envelope fungsi dan berhenti tepat pada construct pertama baris kedua,
`byte_store`. C0.9 menambahkan intrinsic `byte_parse_stmts`, menerima maksimal
tiga statement `byte_store(u8,u8)` sebelum literal `return`, dan mengulang
probe sampai construct berikutnya, `input_read` pada baris kelima. C0.10
memperluas dispatcher menjadi 385 byte agar menerima tepat satu
`input_read(32,96)` setelah nol sampai tiga dead store, menulis metadata
return/no-input/input-present, dan menurunkan jalur input successor menjadi
artifact 377 byte yang identik dengan output langsung C0. Arena source C0
sekarang 3.072 byte dan arena literal total 1.024 byte, dengan batas 255 byte
per literal. Pertumbuhan konkret ini membutuhkan capacity bridge B0.7l:
tabel patch byte-access 2.560 entry dan arena output 262.144 byte, keduanya
tetap bounded dan memiliki gate exact/overflow. C0.11 memperluas dispatcher
menjadi 499 byte untuk menerima tepat satu `byte_parse_stmts(32,0)` setelah
input exact, menambah metadata parser byte keempat, dan menghasilkan artifact
parser 949 byte yang identik antara C0 langsung dan successor. Source successor
3.905 byte memakai escape `\0`; kapasitas source menjadi 4.096 byte dan total
literal 1.536 byte. Kenaikan source membuktikan overlap laten dengan scratch
`3080..3999`, sehingga scratch dipindahkan ke `13080..13999`. Probe generasi
berikutnya sekarang melewati parser dan berhenti pada construct baris keempat,
`byte_store(4,184)`. C0.12 melewati blocker itu tanpa memperbesar dispatcher:
jalur parser memakai kembali body `byte_store(u8,u8)` yang sudah ada dan
menerima tepat satu dead store pascaparser. Bound source intrinsic diperketat
menjadi `<=109`, destination tetap `<=252`, metadata tetap empat byte, dan
artifact successor tetap 3.081 byte. Probe sekarang berhenti pada dead store
pascaparser kedua, `byte_store(5,60)` di baris kelima. C0.13 melewati blocker
kedua itu dengan mengubah satu immediate counter pada stub parser, tetap tanpa
memperbesar dispatcher 499 byte atau menambah metadata. Jalur yang sama kini
menerima dua dead store pascaparser dan menolak yang ketiga. Bound source
intrinsic diperketat lagi menjadi `<=89`, destination tetap `<=252`, source
successor tetap 3.903 byte, dan artifact successor tetap 3.081 byte. Probe
berhenti pada `byte_store(9,15)` di baris keenam. C0.14 membuktikan bahwa empat
store awal successor bukan semantik parser yang perlu diperluas, melainkan
setup untuk sepuluh byte tail ELF yang konstan. Kedua jalur return/input kini
menulis satu byte return dinamis lalu literal tail tetap; empat store setup
dihapus. Source successor menjadi 3.902 byte, artifact menjadi 3.165 byte,
dan C0 sendiri tidak berubah. Probe sekarang melewati lokasi lama dan berhenti
pada construct nyata berikutnya, `while byte_load(1)` di baris keempat.
C0.15 menambahkan matcher mesin 80 byte hanya untuk loop lengkap dan
terminating `while byte_load(1) { LF byte_store(1,0) LF } LF`. Dispatcher
menjadi 579 byte, bound source intrinsic menjadi `<=50`, dan bentuk loop lain
tetap ditolak. Payload parser successor menjadi 1.029 byte, source successor
4.079 byte, dan artifact successor 3.371 byte. Total literal C0 dinaikkan
secara bounded dari 1.536 ke 2.048 byte. Pertumbuhan source `compiler.nq`
menjadi 136.042 byte membuktikan batas input B0 lama tidak cukup; B0.7m hanya
menaikkan `INPUT_CAP` dari 131.072 ke 196.608 byte dengan gate exact/overflow.
Probe sekarang memasuki matcher loop dan berhenti pada `write` di baris kelima.
C0.16 menangani blocker tersebut sebagai satu construct canonical exact, bukan
sebagai grammar `write` atau loop umum. Matcher 477-byte menerima seluruh loop
return-emitter pertama pada baris 4--9, melakukan refill source bounded sampai
512 byte, dan menambah metadata kelima hanya setelah perbandingan penuh cocok.
Artifact parser menjadi 1.625 byte dengan private BSS 1 KiB di `0x402000` agar
RX yang membesar tidak tumpang-tindih dengan RW; artifact runtime biasa tetap
memakai 256 byte di `0x401000`. Destination bound menjadi `<=251`, source input
C0 menjadi 8.192 byte, dan arena literal total menjadi 3.072 byte. Source tail
di atas offset 4.096 dibersihkan sebelum sparse ELF emission agar source lama
tidak mengotori field target yang harus nol. Pertumbuhan ini memerlukan B0.7n,
yang hanya menaikkan output predecessor menjadi 393.216 byte dan patch
byte-access menjadi 3.072 entry tanpa mengubah grammar B0. Probe sekarang
melewati seluruh return-emitter pertama dan berhenti bersih pada
`while byte_load(3)` di baris 10. C0.17 kemudian mengenali loop
parser-emitter canonical secara bounded: literal canonical didecode per byte,
dibandingkan dengan ELF parser yang sedang berjalan, dan hanya metadata
keenam yang diaktifkan setelah seluruh payload serta tail clear cocok. Private
BSS parser menjadi 8 KiB, destination metadata menjadi `<=250`, dan mismatch
payload tetap gagal tanpa artifact. Pertumbuhan source memerlukan B0.7o yang
hanya menaikkan input predecessor menjadi 262.144 byte serta patch byte-access
menjadi 4.096 entry. Probe kemudian melewati seluruh parser-emitter dan
berhenti bersih pada `while byte_load(2)` di baris 23. C0.18 mengenali tepat
loop input-emitter canonical tersebut, termasuk payload ELF, clear byte input,
`output_write(0,1)`, literal tail, dan terminatornya. Metadata parser menjadi
tujuh byte, destination maksimum menjadi 249, private BSS parser menjadi 16
KiB, input source menjadi 9.984 byte, dan arena literal total menjadi 4.096
byte. Pertumbuhan terukur itu memerlukan B0.7p dengan kapasitas input 327.680
byte, output 524.288 byte, dan 5.120 patch byte-access. Parser direct 3.216
byte sekarang menerima seluruh source successor canonical 8.295 byte secara
deterministik. Hal ini membuktikan grammar bounded successor telah lengkap,
tetapi belum menghasilkan compiler baru; blocker aktif berikutnya adalah full
compiler emission, bukan lagi construct atau nomor baris source.
C0.19 menambahkan jalur self-image mesin 229 byte yang hanya aktif pada
fixture marker canonical dan metadata tujuh byte yang lengkap. Jalur itu
membaca `p_filesz` ELF dirinya sendiri, menulis seluruh image dengan retry,
serta mempertahankan exit 74 dan diagnostic exact pada kegagalan output.
Generasi bounded B, C, dan D sekarang identik byte-for-byte. Pertumbuhan
successor sampai 8.631 byte sekaligus membuktikan overlap RX dengan private BSS
lama di `0x402000`; BSS parser dipindah ke `0x403000` dan gate ELF kini
menghitung bahwa kedua segment disjoint. Token cap naik terukur menjadi 248,
operation record menjadi 40 dengan seluruh tabel metadata disjoint. Bukti ini
belum merupakan Full Compiler atau formal self-hosting karena generasi B masih
dibangun dari fixture marker, bukan dari source compiler general yang sama.
C0.20 kemudian menambahkan `byte_load_at(pointer_slot, destination)` sebagai
primitive indirect-read bounded pertama. Runtime kini dapat menelusuri source
berdasarkan pointer byte, bukan hanya offset yang dibekukan saat compile.
Fixture scan membaca source ke offset 32, berjalan sampai sentinel nol, dan
menghasilkan ulang byte input persis ke stdout tanpa hang. Successor C0.19
tetap byte-identik. Blocker yang terukur setelah C0.20 adalah indirect byte
store yang dibutuhkan token table dan patch table source-driven.
C0.21 melengkapi pasangan tersebut dengan
`byte_store_at(pointer_slot, source_slot)`. Gate runtime membuktikan store ke
offset 255 dan copy tabel `NQL!` byte-for-byte melalui pointer dinamis. Source
C0.21 menghasilkan artifact 527.503 byte, melewati batas output B0.7p sebesar
524.288 byte; B0.7q menaikkan hanya `OUTPUT_CAP` menjadi 589.824 byte tanpa
perubahan grammar atau semantik. Blocker aktif sekarang adalah tokenisasi
source-driven nyata, bukan lagi primitive akses tabel.
C0.22 kemudian menambahkan program canonical `source_byte_tokenizer.nql`,
bukan intrinsic tersembunyi. Program itu memakai indirect load/store C0.20 dan
C0.21 untuk mengubah maksimal 16 byte source runtime menjadi satu count byte
dan enam belas record `[kind, offset, length]`. Kind pada layer pertama tetap
raw source byte dan length selalu satu. Input byte ke-17 ditolak sebelum
output, sehingga blocker aktif sekarang lebih spesifik: klasifikasi serta
coalescing identifier, integer, punctuation, dan whitespace.
C0.23 menambahkan primitive mesin bounded
`byte_classify_ascii(source_slot, destination)` dan memakainya dari source
tokenizer canonical. Setiap byte kini dipetakan ke kind stabil untuk
whitespace, identifier, decimal integer, dan sebelas punctuation Core-0;
byte tidak dikenal serta non-ASCII mencapai diagnostic runtime exact sebelum
output. Record masih satu-per-byte, sehingga blocker aktif berikutnya hanya
coalescing identifier/integer dan penghilangan whitespace secara bounded.
C0.24 menyelesaikan blocker lexical tersebut melalui primitive
`byte_token_push(kind_slot, offset_slot, table_base)`. Whitespace sekarang
dilewati, run identifier serta decimal digabung secara kontinu, digit setelah
identifier tetap menjadi bagian identifier, dan punctuation tetap satu record
per byte. Tabel output tetap 49 byte dan dibatasi 16 token. Pertumbuhan patch
byte-access membutuhkan B0.7r yang hanya menaikkan `BYTE_ACCESS_CAP` dari
5.120 ke 5.376; kapasitas input, output, grammar, dan semantik B0 tidak berubah.
Blocker pada akhir C0.24 adalah parser source-driven di atas token yang sudah
tergabung, bukan lagi klasifikasi atau coalescing lexical.
C0.25 membuktikan parser source-driven pertama sebagai program NolQu-L
`source_token_parser.nql`, tanpa intrinsic parser baru. Program itu membaca
tabel token C0.24, memvalidasi rantai `primary (operator primary)*`, menjaga
lokasi setiap token, menjamin setiap iterasi mengonsumsi dua token, dan
menambahkan satu root CST datar. Input genap atau malformed ditolak sebelum
counter dapat wrap sehingga tidak ada hang maupun output parsial. Source parser
ini juga mengungkap batas internal token C0 pada token ke-249. Enam tabel token
internal karena itu diperlebar secara struktural menjadi 512 byte per tabel,
decoded-literal arena dipindah ke `20000..24095`, dan gate exact kini menerima
512 token serta menolak token ke-513 di `input:1:524`. B0.7r tidak berubah dan
successor lama tetap byte-identik. Blocker pada akhir C0.25 bukan lagi parser
exact satu bentuk, melainkan pembangunan node ber-precedence, keyword
resolution, dan grammar statement/function sebelum Full Compiler emission.

C0.26 kini menyelesaikan kontrak source-to-AST tersebut melalui komponen
`frontend.nql` yang dibangun oleh B0, tanpa memperluas primitive C0.25. Lexer
membaca source sampai EOF; parser menghasilkan tree `+ - * /`, grouping,
`let`, assignment, final `return`, serta envelope `fn main()`. AST NQAF/1
menyimpan source asli, anchor lexeme dan link node berindeks. Source dibatasi
8.192 byte, token/node 512. `c0.seed` tetap emitter C0.25 yang byte-identik;
artifact tambahannya `c0-frontend.seed`. C0.27 menghubungkan AST tersebut ke
local resolution dan codegen i64 melalui `c0-backend.seed`, juga dibangun B0.
C0.28 memperluas kedua komponen itu dengan perbandingan signed i64, `if/else`
dan `while` bersarang, lexical scope, serta return dari dalam blok. NQAF/2
memakai delimiter terstruktur yang divalidasi sebelum branch mesin dipatch;
source scalar lama tetap menghasilkan NQAF/1. Batas nesting adalah 64 blok.
Blocker aktif sekarang adalah calls, runtime byte/stream operations, dan coverage
source compiler. Full Compiler dan self-hosting belum dipromosikan. Helper token 49-byte
lama tetap proof historical dengan framing input terbatas, bukan frontend
source yang baru.

## Work Unit Selesai: Bootstrap Compiler B0

Pada fase B0, pekerjaan canonical bukan memperluas R0, LLVM bridge, atau
Python tooling. Pekerjaan fase itu adalah membangun **Bootstrap Compiler B0**
sebagai artifact pertama setelah Stage 0.

B0 adalah compiler awal yang:

1. source-nya ditulis dalam format Stage 0 `.nql0`,
2. dibangun hanya oleh `bootstrap/stage0/x86_64-linux/stage0.seed`,
3. menghasilkan executable compiler generasi berikutnya,
4. memahami satu subset source kecil bernama **NolQu-L Core-0**,
5. dan mempunyai test yang membuktikan output valid secara byte-for-byte atau
   behaviorally equivalent sesuai kontrak yang tertulis.

B0 belum boleh disebut ada sebelum repository mempunyai semua artifact berikut:

| Artifact | Status awal | Syarat PASS |
| --- | --- | --- |
| `bootstrap/compiler/b0/compiler.nql0` | NOT IMPLEMENTED | Source B0 canonical dalam format Stage 0 |
| `bootstrap/compiler/b0/x86_64-linux/b0.seed` | NOT IMPLEMENTED | Dibangun oleh `stage0.seed`, executable, hash terdokumentasi |
| `bootstrap/compiler/b0/x86_64-linux/b0.sha256` | NOT IMPLEMENTED | Hash artifact canonical |
| `bootstrap/compiler/b0/x86_64-linux/materialize.sh` | NOT IMPLEMENTED | Atomic write, hash verification, temp cleanup |
| `tests/bootstrap/bootstrap_compiler_b0.sh` | NOT IMPLEMENTED | Membuktikan build, CLI, compile-pass, compile-fail, determinism |
| `bootstrap/manifest.tsv` row `bootstrap-compiler` | NOT IMPLEMENTED | Berubah ke PASS hanya setelah test B0 hijau |

Semua artifact di atas sekarang telah tersedia dan `bootstrap-compiler` sudah
dipromosikan ke PASS pada B0.6. Scope B0 tetap dibekukan sebagai compiler
bootstrap kecil, kecuali B0.7 Semantic Codegen Bridge yang memang wajib agar
B0 dapat membangun C0 secara semantik. Di luar bridge itu, perluasan fitur baru
harus masuk ke C0 atau merupakan bug fix B0 yang dibuktikan oleh test.

### Batas Kemampuan B0

B0 tidak boleh mencoba menjadi Full NolQu-L. B0 hanya perlu cukup kuat untuk
membangun Core Compiler awal. Scope awal yang diizinkan:

- satu file input;
- output executable ELF64 x86_64 Linux syscall-only;
- entry point tetap;
- integer 64-bit signed;
- literal integer desimal kecil;
- string literal ASCII untuk `write`;
- `fn main()`;
- local binding bounded; `let` mendeklarasikan dan assignment memutasi local
  yang sudah ada;
- `return <int>`;
- `if` sederhana tanpa short-circuit kompleks;
- `while` sederhana jika diperlukan untuk compiler berikutnya;
- pemanggilan intrinsic bootstrap terbatas untuk `write`, `exit`, memory byte
  access, serta bounded stream I/O fd 0/1/2;
- diagnostic source-level minimum: file, line, column, error code, message.

Scope awal yang harus tetap ditolak sampai ada kebutuhan dan test:

- module system;
- generics;
- ownership penuh;
- borrow checking;
- optimizer;
- object file/linker eksternal;
- dependency manager;
- standard library besar;
- multi-target;
- FFI;
- concurrency;
- exception model;
- hidden LLVM/Python/NASM/C/Rust/GCC/Clang dependency.

### Core-0 Source Contract

Core-0 adalah subset sementara untuk membuat compiler berikutnya, bukan bahasa
final. Setiap syntax Core-0 harus sengaja mudah dimigrasikan ke NolQu-L Core.
Kontrak minimum:

```text
program      := function*
function     := "fn" ident "(" ")" block
block        := "{" statement* "}"
statement    := let_stmt | assign_stmt | return_stmt | expr_stmt | if_stmt | while_stmt
let_stmt     := "let" ident "=" expr
assign_stmt  := ident "=" expr
return_stmt  := "return" expr
expr_stmt    := expr
if_stmt      := "if" expr block ("else" block)?
while_stmt   := "while" expr block
expr         := integer | string | ident | call | binary | "(" expr ")"
call         := ident "(" (expr ("," expr)*)? ")"
binary       := expr op expr
op           := "+" | "-" | "*" | "/" | "==" | "!=" | "<" | "<="
```

Parser Core-0 boleh memakai precedence climbing sederhana, tetapi setiap error
harus menjamin progress atau berhenti dengan diagnostic yang jelas. Tidak boleh
ada recursion tanpa batas pada source invalid.

### B0 Output Contract

B0 harus menghasilkan executable langsung atau format intermediate yang
ditentukan secara eksplisit dan dibuktikan oleh test. Untuk milestone pertama,
jalur paling sederhana adalah:

```text
Core-0 source
        ↓
B0 lexer/parser minimal
        ↓
direct x86_64 ELF64 emission
        ↓
standalone syscall-only executable
```

Jika B0 menghasilkan intermediate sebelum executable, intermediate itu harus
didefinisikan di dokumen dan diuji. Tidak boleh ada intermediate tersembunyi
yang bergantung pada tool host.

### B0 Test Gate

B0 dianggap `PASS` hanya jika test berikut ada dan hijau:

```text
make bootstrap-test
tests/bootstrap/bootstrap_compiler_b0.sh
```

Test B0 minimum:

- `b0-built-by-stage0`: `stage0.seed < compiler.nql0 > b0.seed`;
- `b0-hash`: artifact sesuai `b0.sha256`;
- `b0-help-or-usage`: CLI invalid menghasilkan diagnostic dan exit non-zero;
- `b0-compile-return`: program `fn main() { return 7 }` menghasilkan executable
  yang exit 7;
- `b0-compile-write`: program valid menulis string ke stdout;
- `b0-invalid-token`: karakter invalid ditolak dengan line/column;
- `b0-missing-main`: source tanpa `main` ditolak;
- `b0-deterministic`: input sama menghasilkan output byte-for-byte sama;
- `b0-no-host-toolchain`: test memastikan build canonical tidak memanggil
  assembler, linker, Python, LLVM, C compiler, atau Rust compiler.

Sebelum seluruh gate tersebut hijau, `bootstrap-compiler` di manifest tetap
`NOT_IMPLEMENTED`.

### B0 Non-Goals

B0 tidak boleh:

- memperluas Stage 0 menjadi assembler besar;
- memakai R0 sebagai predecessor canonical;
- memakai LLVM bridge sebagai backend canonical;
- memakai Python script sebagai compiler stage;
- mengklaim self-hosting;
- mengubah status Core Compiler, Full Compiler, Self-Hosting, atau Verified
  Compiler tanpa artifact dan test nyata.

R0 dan legacy LLVM/Python path tetap boleh menjadi oracle pembanding, tetapi
hasil pembanding tidak menggantikan bukti bahwa B0 dibangun dari Stage 0.

### B0 Implementation Phases

Pekerjaan B0 harus bertahap. Jangan mencoba menulis compiler penuh dalam satu
artifact besar karena itu akan sulit diaudit dan sulit dibuktikan dari Stage 0.

Urutan implementasi yang berlaku:

| Fase | Tujuan | Status repository | Batas selesai |
| --- | --- | --- | --- |
| B0.0 Scaffold | Layout canonical dan test harness negatif | PASS | Directory, README, materializer stub, dan test yang masih menandai B0 NOT_IMPLEMENTED tanpa failure palsu |
| B0.1 Fixed Program Emitter | B0 membaca satu Core-0 fixture yang sangat kecil dan menghasilkan ELF exit-code deterministik | PASS | `fn main() { return 7 }` menghasilkan executable exit 7 |
| B0.2 Lexer Minimum | Tokenisasi keyword, identifier, integer, string, punctuation, whitespace, dan comment | PASS | Token invalid menghasilkan line/column, lexer selalu progress |
| B0.3 Parser Minimum | Parse `fn main`, block, return, let, call, binary expression sederhana | PASS | Source valid membentuk struktur internal bounded; malformed source ditolak |
| B0.4 Direct Codegen | Emit ELF64 syscall-only untuk return, write, exit, arithmetic, branch kecil | PASS | Program return/write/arithmetic/if sederhana berjalan |
| B0.5 Determinism & Cleanup | Output deterministik, error path tanpa stdout parsial, materializer atomic | PASS | Test deterministic dan temp cleanup hijau |
| B0.6 Manifest Promotion | Promosi status bootstrap compiler | PASS | `bootstrap-compiler` berubah ke PASS hanya setelah semua gate B0 hijau |
| B0.7 Semantic Codegen Bridge | Hilangkan whole-source fixture matching dari subset yang diperlukan C0 | PASS | Return/write/local/expression/assignment/if/while/byte-memory dan bounded stream I/O sudah diturunkan semantik |
| B0.7e Stderr Diagnostic Bridge | Sediakan output diagnostic C0 tanpa mencampur artifact stdout | PASS | `error_write` memakai fd 2, short-write loop, bounds guard, dan exit 74 pada write failure |
| B0.7f Core Capacity Bridge | Naikkan batas tetap yang dibutuhkan source C0 | PASS | Arena output 65.536 byte dan 512 patch byte-access; tetap bounded dan diuji sampai C0.2c |
| B0.7g C0.3 Capacity Bridge | Naikkan tabel patch byte-access tanpa menambah semantik bahasa B0 | PASS | 1.024 patch byte-access; `c0.seed` C0.3a tetap 65.286 byte di dalam arena output 65.536 byte |
| B0.7h C0.3b Output Bridge | Naikkan arena output setelah C0.3b melampaui batas lama | PASS | Arena output 131.072 byte; `c0.seed` C0.3b berukuran 77.113 byte; semantik bahasa B0 tetap tidak berubah |
| B0.7i C0.3c Byte-Access Bridge | Naikkan tabel patch byte-access setelah source C0.3c melampaui batas lama | PASS | Tepat 2.048 patch byte-access diterima dan entry ke-2.049 ditolak; `c0.seed` C0.3c berukuran 98.215 byte; arena output tetap 131.072 byte dan semantik B0 tidak berubah |
| B0.7j C0.4 Input Capacity Bridge | Naikkan arena source setelah `compiler.nq` C0.4 melampaui batas lama | PASS | Arena source 131.072 byte dengan overflow probe; byte 131.073 ditolak `B0-IO-003`; `c0.seed` C0.4 berukuran 116.545 byte dan arena output tetap 131.072 byte |
| B0.7k C0.7 Output Capacity Bridge | Naikkan arena output setelah decoder u8 C0.7 melampaui batas lama | PASS | Arena output 196.608 byte; artifact 196.598 byte diterima, langkah emisi 18 byte berikutnya ditolak `B0-CG-005`; `c0.seed` C0.7 berukuran 134.891 byte dan semantik B0 tidak berubah |
| B0.7l C0.10 Capacity Bridge | Naikkan patch byte-access dan arena output setelah C0.10 melampaui kedua batas lama | PASS | Tepat 2.560 patch diterima dan patch ke-2.561 ditolak; output 262.136 byte diterima dan langkah emisi berikutnya ditolak `B0-CG-005`; semantik B0 tidak berubah |
| B0.7m C0.15 Input Capacity Bridge | Naikkan arena source predecessor setelah matcher loop C0.15 melampaui batas lama | PASS | Tepat 196.608 byte diterima dan byte ke-196.609 ditolak `B0-IO-003`; output dan byte-access cap serta semantik B0 tidak berubah |
| B0.7n C0.16 Output/Byte-Access Capacity Bridge | Naikkan dua kapasitas predecessor setelah matcher return-emitter C0.16 melampaui batas lama | PASS | Tepat 3.072 patch diterima dan patch ke-3.073 ditolak; output 393.212 byte diterima dan langkah emisi berikutnya ditolak `B0-CG-005`; grammar dan semantik B0 tidak berubah |
| B0.7o C0.17 Input/Byte-Access Capacity Bridge | Naikkan dua kapasitas predecessor setelah matcher parser-emitter C0.17 melampaui batas lama | PASS | Tepat 262.144 byte input dan 4.096 patch diterima; byte ke-262.145 dan patch ke-4.097 ditolak tanpa artifact; output cap 393.216 byte serta semantik B0 tidak berubah |
| B0.7p C0.18 Input/Output/Byte-Access Capacity Bridge | Naikkan tiga kapasitas predecessor setelah matcher input-emitter C0.18 melampaui seluruh batas lama | PASS | Tepat 327.680 byte input, 5.120 patch, dan output 524.288 byte diterima; byte ke-327.681, patch ke-5.121, dan langkah emisi berikutnya ditolak tanpa artifact; grammar dan semantik B0 tidak berubah |
| B0.7q C0.21 Output Capacity Bridge | Naikkan hanya kapasitas output predecessor setelah primitive indirect store C0.21 melampaui batas B0.7p | PASS | Artifact representable 589.808 byte diterima dan langkah 18 byte berikutnya ditolak `B0-CG-005`; input tetap 327.680 byte, patch tetap 5.120, serta grammar dan semantik B0 tidak berubah |
| B0.7r C0.24 Byte-Access Capacity Bridge | Naikkan hanya tabel patch byte-access setelah lowering token-push C0.24 melampaui batas B0.7q | PASS | Batas minimum terukur 5.166 patch; cap 5.376 menerima fixture exact dan patch ke-5.377 ditolak tanpa artifact; input tetap 327.680 byte, output tetap 589.824 byte, serta grammar dan semantik B0 tidak berubah |

Fase B0.0 boleh masuk tanpa `b0.seed` final apabila test-nya secara eksplisit
menyatakan B0 belum diimplementasikan dan manifest tetap `NOT_IMPLEMENTED`.
Fase B0.1 dan seterusnya tidak boleh memakai placeholder success.

### B0 Directory Contract

Layout canonical B0 harus mengikuti pola ini:

```text
bootstrap/compiler/b0/
├── README.md
├── compiler.nql0
└── x86_64-linux/
    ├── materialize.sh
    ├── b0.seed
    └── b0.sha256

tests/bootstrap/
├── bootstrap_compiler_b0.sh
└── fixtures/
    └── b0/
        ├── return7.nql
        ├── write_string.nql
        ├── invalid_token.nql
        └── missing_main.nql
```

Sebelum B0.1 selesai, `b0.seed` boleh belum ada. Jika file tersebut belum ada,
test harus melaporkan status sebagai `NOT_IMPLEMENTED` sesuai manifest, bukan
PASS. Setelah `b0.seed` ada, artifact wajib executable dan hash-nya wajib
diverifikasi.

### B0 CLI Contract

B0 harus mempunyai CLI sekecil mungkin:

```text
b0 <input.nql> -o <output>
b0 --help
```

Aturan:

- tanpa argumen: exit 1 dan diagnostic usage ke stderr;
- `--help`: exit 0, tulis usage ke stdout;
- input hilang: exit 1, diagnostic ke stderr;
- output tidak diberikan: exit 1, diagnostic ke stderr;
- output gagal ditulis: exit 1, output lama tidak boleh rusak;
- source invalid: exit 1, tidak menghasilkan executable;
- internal invariant rusak: exit 2.

Tidak ada `run`, project manager, dependency, atau multi-file mode di B0.

### B0 Memory Model

B0 harus memakai buffer bounded yang ukurannya tertulis. Nilai awal yang
disarankan:

| Buffer | Limit awal |
| --- | ---: |
| source input | 1 MiB |
| token records | 65,536 token |
| string table | 1 MiB |
| node records | 65,536 node |
| output executable | 2 MiB |

Jika limit tercapai, B0 harus berhenti dengan diagnostic yang menyebut limit
yang dilanggar. Limit boleh diubah hanya jika test dan dokumentasi ikut
diperbarui.

### B0 Internal Representation

B0 tidak membutuhkan AST penuh seperti Full NolQu-L. Representasi awal boleh
flat dan bounded:

```text
token  := { kind, offset, length }
node   := { kind, first_child_or_value, next_sibling_or_extra, source_offset }
symbol := { name_offset, name_length, kind, value_or_node }
```

Pointer mentah ke source buffer tidak boleh menjadi format persistent internal.
Gunakan offset dan length supaya deterministik, mudah di-dump, dan mudah
dibandingkan.

### B0 Diagnostic Codes

Diagnostic B0 harus mulai dari kode kecil yang stabil:

```text
B0-LEX-001 invalid character
B0-LEX-002 unterminated string
B0-PAR-001 expected token
B0-PAR-002 expected expression
B0-SEM-001 missing main
B0-SEM-002 duplicate symbol
B0-CG-001 unsupported construct
B0-CG-007 assignment target is not declared
B0-CG-008 byte-memory index is outside the bounded region
B0-IO-001 cannot read input
B0-IO-002 cannot write output
B0-ICE-001 internal invariant failure
```

Format text minimum:

```text
path:line:column: error[B0-XXX-000]: message
```

JSON diagnostic bukan requirement B0.

### B0 Promotion Rule

Status `bootstrap-compiler` dalam `bootstrap/manifest.tsv` hanya boleh berubah:

```text
NOT_IMPLEMENTED -> PASS
```

Tidak ada status sementara `PARTIAL` pada manifest canonical kecuali format
manifest diubah dan semua test manifest ikut diperbarui. Work-in-progress B0
harus dicatat di README atau dokumen ini, bukan dipromosikan sebagai stage
canonical.

### B0.0 Scaffold Contract

B0.0 adalah patch dokumentasi dan test-harness pertama sebelum compiler B0
benar-benar ada. Tujuannya bukan membuat executable compiler, tetapi membuat
ruang kerja B0 eksplisit sehingga patch B0.1 dapat dimulai tanpa menebak
layout, command, atau status manifest.

B0.0 boleh menambahkan:

- `bootstrap/compiler/b0/README.md`;
- `bootstrap/compiler/b0/compiler.nql0` sebagai empty or comment-only source
  yang secara eksplisit belum menghasilkan `b0.seed`;
- `bootstrap/compiler/b0/x86_64-linux/materialize.sh` yang gagal jelas dengan
  pesan `b0: not implemented` apabila `b0.seed` belum tersedia;
- `tests/bootstrap/bootstrap_compiler_b0.sh` yang memverifikasi status
  `bootstrap-compiler` masih `NOT_IMPLEMENTED`;
- fixture kosong di `tests/bootstrap/fixtures/b0/` untuk program valid dan
  invalid yang akan dipakai B0.1 sampai B0.4;
- dokumentasi README yang menyebut B0.0 sebagai scaffold, bukan stage PASS.

B0.0 tidak boleh menambahkan:

- `b0.seed` palsu;
- hash palsu;
- executable yang dibuat oleh compiler host;
- `make bootstrap-test` yang menyembunyikan failure nyata;
- manifest `bootstrap-compiler PASS`;
- test bernama `PASS b0-built-by-stage0` sebelum Stage 0 benar-benar membangun
  artifact B0;
- dependency ke assembler, linker, Python, LLVM, C compiler, Rust compiler, atau
  R0 untuk build canonical.

Test B0.0 yang benar adalah test status negatif. Nama test yang dianjurkan:

```text
PASS b0-manifest-not-implemented
PASS b0-seed-absent-before-implementation
PASS b0-materializer-reports-not-implemented
PASS b0-scaffold-does-not-promote-bootstrap-compiler
```

Pesan `PASS` pada test B0.0 berarti **scaffold belum mengklaim kemampuan yang
belum ada**. Pesan itu bukan bukti bahwa Bootstrap Compiler sudah bekerja.

`tests/bootstrap/run_tests.sh` boleh memanggil `bootstrap_compiler_b0.sh` pada
B0.0 hanya jika test tersebut exit 0 saat manifest masih `NOT_IMPLEMENTED` dan
semua assertion-nya menjaga status negatif di atas.

Setelah B0.6, assertion negatif ini diganti oleh assertion promosi manifest
yang membuktikan artifact B0 benar-benar tercatat sebagai evidence canonical.

Status repository saat B0.0 scaffold dibuat:

```text
B0.0 Scaffold              PASS
B0.1 Fixed Program Emitter PASS
B0.2 Lexer Minimum         PASS
B0.3 Parser Minimum        PASS
B0.4 Direct Codegen        PASS
B0.5 Determinism/Cleanup   PASS
Bootstrap Compiler B0 gates PASS
bootstrap-compiler manifest PASS
```

Bukti B0.0:

```text
bootstrap/compiler/b0/README.md
bootstrap/compiler/b0/compiler.nql0
bootstrap/compiler/b0/x86_64-linux/materialize.sh
tests/bootstrap/bootstrap_compiler_b0.sh
tests/bootstrap/fixtures/b0/return7.nql
tests/bootstrap/fixtures/b0/write_string.nql
tests/bootstrap/fixtures/b0/invalid_token.nql
tests/bootstrap/fixtures/b0/missing_main.nql
tests/bootstrap/fixtures/b0/lexer_core0.nql
tests/bootstrap/fixtures/b0/unterminated_string.nql
make bootstrap-test
```

B0.0 PASS hanya berarti scaffold dan guard test sudah ada. B0.1 PASS berarti
`stage0.seed` sudah dapat membangun `b0.seed` fixed-shape pertama, dan `b0.seed`
dapat mengompilasi fixture `return7.nql` menjadi executable exit 7. Ini belum
bukti parser Core-0 umum. B0.2 PASS berarti B0 sudah mempunyai lexer bounded
untuk token Core-0 minimum dan mode dump-token `--lex`, tetapi belum mempunyai
parser AST atau codegen umum.

### B0.1 First Executable Contract

B0.1 adalah titik pertama di mana `b0.seed` boleh muncul.

Syarat minimal:

- `compiler.nql0` dibaca oleh `stage0.seed` untuk menghasilkan `b0.seed`;
- `b0.seed` adalah ELF64 x86_64 Linux executable;
- `b0.seed --help` exit 0 dan menulis usage minimum;
- `b0.seed tests/bootstrap/fixtures/b0/return7.nql -o <tmp>` menghasilkan
  executable output;
- executable output dari `return7.nql` exit dengan status 7;
- input invalid tidak menghasilkan output executable baru;
- dua build dari input yang sama menghasilkan bytes yang sama;
- materializer memakai temp file dan rename setelah hash cocok.

B0.1 boleh mengimplementasikan fixed-shape compiler untuk fixture `return7.nql`
selama behavior tersebut didokumentasikan sebagai milestone sementara dan test
invalid tetap menolak source lain dengan diagnostic jelas. B0.1 tidak boleh
mengklaim lexer/parser umum sebelum B0.2 dan B0.3 selesai.

Status repository saat ini:

```text
B0.1 Fixed Program Emitter PASS
B0.2 Lexer Minimum         PASS
B0.3 Parser Minimum        PASS
B0.4 Direct Codegen        PASS
B0.5 Determinism/Cleanup   PASS
B0.6 Manifest Promotion    PASS
```

Bukti B0.1:

```text
bootstrap/compiler/b0/compiler.nql0
bootstrap/compiler/b0/x86_64-linux/b0.seed
bootstrap/compiler/b0/x86_64-linux/b0.sha256
bootstrap/compiler/b0/x86_64-linux/materialize.sh
tests/bootstrap/bootstrap_compiler_b0.sh
tests/bootstrap/fixtures/b0/return7.nql
tests/bootstrap/fixtures/b0/write_string.nql
tests/bootstrap/fixtures/b0/lexer_core0.nql
tests/bootstrap/fixtures/b0/unterminated_string.nql
tests/bootstrap/fixtures/b0/unclosed_block.nql
tests/bootstrap/fixtures/b0/leftover_token.nql
tests/bootstrap/fixtures/b0/duplicate_main.nql
make bootstrap-test
```

### B0.2 Lexer Minimum Contract

B0.2 adalah titik pertama di mana B0 boleh mengklaim mempunyai lexer umum untuk
Core-0. Lexer B0.2 harus tetap kecil dan bounded.

Token kind minimum:

```text
EOF
IDENT
INT
STRING
FN
LET
RETURN
IF
ELSE
WHILE
LPAREN RPAREN
LBRACE RBRACE
COMMA
SEMI
EQ
PLUS MINUS STAR SLASH
EQEQ NEQ LT LTE
```

Aturan lexer:

- whitespace ASCII dilewati;
- LF menaikkan line, column kembali ke 1;
- CRLF diterima sebagai satu newline;
- CR tunggal ditolak;
- `#` comment boleh diterima sampai akhir baris untuk bootstrap source;
- identifier hanya ASCII `[A-Za-z_][A-Za-z0-9_]*`;
- integer desimal harus dicek overflow `i64`;
- string literal hanya perlu ASCII printable plus escape minimum `\n`, `\"`,
  dan `\\`;
- unterminated string menghasilkan `B0-LEX-002`;
- karakter tidak dikenal menghasilkan `B0-LEX-001`;
- setiap loop lexer harus consume byte, menghasilkan token, atau berhenti
  dengan diagnostic.

Token record B0.2 harus menyimpan:

```text
kind
source_offset
length
line
column
```

`line` dan `column` boleh dihitung ulang dari offset jika itu membuat artifact
lebih kecil, tetapi diagnostic tetap wajib menampilkan posisi source.

Test B0.2 minimum:

```text
PASS b0-lex-keywords
PASS b0-lex-identifiers
PASS b0-lex-integers
PASS b0-lex-strings
PASS b0-lex-comments-whitespace
PASS b0-lex-invalid-character
PASS b0-lex-unterminated-string
PASS b0-lex-progress-on-invalid-input
```

Jika B0 tidak menyediakan mode dump-token publik, test boleh membuktikan lexer
melalui compile-pass dan compile-fail fixture yang spesifik.

Status repository saat ini:

```text
B0.2 Lexer Minimum PASS
B0.3 Parser Minimum PASS
bootstrap-compiler manifest PASS
```

Bukti B0.2:

```text
bootstrap/compiler/b0/compiler.nql0
bootstrap/compiler/b0/x86_64-linux/b0.seed
bootstrap/compiler/b0/x86_64-linux/b0.sha256
bootstrap/compiler/b0/x86_64-linux/b0.reference.asm
tests/bootstrap/bootstrap_compiler_b0.sh
tests/bootstrap/fixtures/b0/lexer_core0.nql
tests/bootstrap/fixtures/b0/invalid_token.nql
tests/bootstrap/fixtures/b0/unterminated_string.nql
make bootstrap-test
```

B0.2/B0.3 tidak mempromosikan `bootstrap-compiler` sendiri; promosi baru sah
setelah B0.4 codegen, B0.5 hardening, dan B0.6 manifest promotion selesai.

### B0.3 Parser Minimum Contract

B0.3 adalah titik pertama di mana B0 boleh mengklaim memahami struktur Core-0
di luar fixture fixed-shape. Parser harus berjalan di atas token stream B0.2.

Parser B0.3 harus menerima:

- satu atau lebih function declaration;
- `fn main() { ... }`;
- block statement;
- `let name = expr`;
- `name = expr` untuk local yang sudah dideklarasikan;
- `return expr`;
- expression statement untuk call intrinsic;
- `if expr { ... } else { ... }`;
- `while expr { ... }` hanya jika B0.4 membutuhkannya;
- binary expression dengan precedence stabil;
- grouping memakai `(` dan `)`.

Precedence minimum:

```text
highest: call / primary
         * /
         + -
         < <=
         == !=
lowest : assignment is not an expression in Core-0
```

Parser B0.3 harus menolak:

- function tanpa nama;
- block tidak ditutup;
- `let` tanpa initializer;
- `return` tanpa expression;
- expression kosong;
- token sisa setelah parse selesai;
- source tanpa `main`;
- duplicate function name.

Representasi parse boleh flat node array. Node minimum:

```text
PROGRAM
FUNCTION
BLOCK
LET
ASSIGN
RETURN
IF
WHILE
CALL
BINARY
INT
STRING
IDENT
```

Test B0.3 minimum:

```text
PASS b0-parse-return
PASS b0-parse-let
PASS b0-parse-assignment
PASS b0-parse-call
PASS b0-parse-binary-precedence
PASS b0-parse-if-else
PASS b0-parse-missing-main
PASS b0-parse-unclosed-block
PASS b0-parse-leftover-token
PASS b0-parse-duplicate-function
```

Parser error recovery boleh berhenti pada error pertama di B0.3. Yang tidak
boleh terjadi adalah infinite loop, recursive overflow pada source kecil, atau
diagnostic tanpa lokasi.

Status repository saat ini:

```text
B0.3 Parser Minimum PASS
B0.4 Direct Codegen PASS
bootstrap-compiler manifest PASS
```

Bukti B0.3:

```text
bootstrap/compiler/b0/compiler.nql0
bootstrap/compiler/b0/x86_64-linux/b0.seed
bootstrap/compiler/b0/x86_64-linux/b0.sha256
bootstrap/compiler/b0/x86_64-linux/b0.reference.asm
tests/bootstrap/bootstrap_compiler_b0.sh
tests/bootstrap/fixtures/b0/return7.nql
tests/bootstrap/fixtures/b0/lexer_core0.nql
tests/bootstrap/fixtures/b0/missing_main.nql
tests/bootstrap/fixtures/b0/unclosed_block.nql
tests/bootstrap/fixtures/b0/leftover_token.nql
tests/bootstrap/fixtures/b0/duplicate_main.nql
make bootstrap-test
```

B0.3 menyediakan mode `--parse <input.nql>` yang menulis `PARSE OK` saat source
Core-0 valid. Mode compile biasa sekarang menurunkan return, write literal,
local bounded, assignment local, expression integer ber-precedence,
comparison, `if/else`, dan `while` sederhana langsung ke machine code x86_64.
Primitive `byte_load`/`byte_store` juga sudah diturunkan ke region stack
zero-initialized 65.536 byte. `input_read(offset, count)` dan
`output_write(offset, count)` menyediakan jalur source/artifact berbasis fd 0/1
tanpa runtime host. `error_write(offset, count)` melengkapi jalur diagnostic fd
2 tanpa recursive error write. Dengan itu bridge B0 selesai dan C0.1 telah
dibangun oleh predecessor tersebut.

### B0.4 Direct Codegen Contract

B0.4 adalah titik pertama di mana B0 menjadi compiler kecil yang berguna untuk
lebih dari satu fixture. Backend tetap direct ELF64 emission, bukan assembler
internal besar.

Codegen B0.4 harus mendukung:

- `_start` sebagai entry point ELF;
- pemanggilan `main`;
- `return int` menjadi exit status `int & 255`;
- syscall `write(1, ptr, len)` untuk intrinsic `write("text")`;
- arithmetic integer `+`, `-`, `*`, `/` untuk literal/local sederhana;
- comparison `==`, `!=`, `<`, `<=` menghasilkan 0 atau 1;
- `if`/`else` dengan label deterministic;
- local `let` dalam stack frame bounded atau slot statik documented.

Codegen B0.4 harus menolak:

- call ke function yang belum didukung;
- tipe string dipakai sebagai integer arithmetic;
- division by literal zero jika dapat diketahui saat compile-time;
- output melebihi buffer executable;
- unresolved symbol internal.

Konvensi backend:

```text
target              : x86_64-linux
format              : ELF64 executable
dynamic interpreter : absent
runtime             : syscall-only
stack executable    : no
stdlib              : none
linker              : none
```

Test B0.4 minimum:

```text
PASS b0-codegen-return7
PASS b0-codegen-write-string
PASS b0-codegen-arithmetic
PASS b0-codegen-comparison
PASS b0-codegen-if-else
PASS b0-codegen-unknown-call
PASS b0-codegen-type-mismatch
PASS b0-codegen-div-zero
PASS b0-codegen-output-limit
PASS b0-codegen-elf-static
PASS b0-codegen-non-executable-stack
PASS b0-codegen-deterministic-labels
```

B0.4 belum perlu melakukan optimization. Determinism dan correctness lebih
penting daripada ukuran binary.

Status repository saat ini:

```text
B0.4 Direct Codegen PASS
B0.5 Determinism/Cleanup PASS
bootstrap-compiler manifest PASS
```

Bukti B0.4/B0.5:

```text
bootstrap/compiler/b0/compiler.nql0
bootstrap/compiler/b0/x86_64-linux/b0.seed
bootstrap/compiler/b0/x86_64-linux/b0.sha256
bootstrap/compiler/b0/x86_64-linux/b0.reference.asm
tests/bootstrap/bootstrap_compiler_b0.sh
tests/bootstrap/fixtures/b0/return7.nql
tests/bootstrap/fixtures/b0/write_string.nql
tests/bootstrap/fixtures/b0/arithmetic.nql
tests/bootstrap/fixtures/b0/comparison.nql
tests/bootstrap/fixtures/b0/if_else.nql
tests/bootstrap/fixtures/b0/unknown_call.nql
tests/bootstrap/fixtures/b0/type_mismatch.nql
tests/bootstrap/fixtures/b0/div_zero.nql
tests/bootstrap/fixtures/b0/output_limit.nql
make bootstrap-test
```

B0.4 sudah membuktikan direct ELF64 emission untuk `return7.nql` dan
`write_string.nql`, lalu diperluas ke fixture `arithmetic.nql`,
`comparison.nql`, dan `if_else.nql`. Diagnostic codegen untuk unknown-call,
type mismatch, div-zero, dan output-limit juga sudah diuji. B0.5 menambahkan
gate determinism, atomic materializer failure, write-failure diagnostic,
stdout cleanliness, dan FD cleanup stress. Ini belum mempromosikan
`bootstrap-compiler` karena promosi manifest hanya boleh terjadi pada B0.6.

### B0.5 Determinism And Cleanup Contract

B0.5 adalah fase hardening sebelum Bootstrap Compiler boleh dipromosikan.
Tujuannya memastikan hasil B0 dapat direproduksi dan kegagalan tidak merusak
artifact lama.

Sumber nondeterminisme yang harus dilarang:

- timestamp dalam executable;
- temporary path dalam output;
- urutan symbol berdasarkan filesystem;
- alamat memory proses host;
- random seed;
- PID;
- environment variable yang tidak terdokumentasi;
- hash table iteration order yang tidak stabil;
- build ID otomatis;
- locale-dependent formatting.

Jika sebuah field metadata belum dapat dibuat deterministik, field tersebut
tidak boleh dimasukkan ke artifact B0.

Cleanup contract:

- output ditulis ke temp file di directory target;
- temp file dihapus pada source invalid;
- temp file dihapus pada write failure;
- temp file dihapus pada hash mismatch;
- output lama dipertahankan jika build gagal;
- stdout tidak boleh berisi bytes executable pada compile-to-file mode;
- stderr hanya berisi diagnostic/progress;
- semua file descriptor yang dibuka oleh B0 harus ditutup pada success dan
  handled error;
- raw syscall failure harus diterjemahkan menjadi diagnostic B0-IO atau B0-ICE
  sesuai penyebab.

Test B0.5 minimum:

```text
PASS b0-deterministic-two-builds
PASS b0-deterministic-two-materializations
PASS b0-error-preserves-old-output
PASS b0-error-removes-temp-file
PASS b0-hash-mismatch-preserves-old-output
PASS b0-write-failure-diagnostic
PASS b0-no-executable-bytes-on-stdout
PASS b0-fd-cleanup-success
PASS b0-fd-cleanup-error
```

Status repository saat ini:

```text
B0.5 Determinism/Cleanup PASS
B0.6 Manifest Promotion PASS
bootstrap-compiler manifest PASS
```

Bukti B0.5:

```text
tests/bootstrap/bootstrap_compiler_b0.sh
bootstrap/compiler/b0/x86_64-linux/materialize.sh
bootstrap/compiler/b0/x86_64-linux/b0.sha256
make bootstrap-test
```

Jika tracer syscall tidak tersedia di host test, cleanup FD boleh diuji dengan
fixture yang memaksa banyak compile berulang dan memastikan tidak ada failure
karena resource exhaustion. Namun pada host yang punya tracer, test syscall
lebih disukai.

### B0.6 Manifest Promotion Contract

B0.6 adalah satu-satunya fase yang boleh mengubah:

```text
bootstrap-compiler NOT_IMPLEMENTED
```

menjadi:

```text
bootstrap-compiler PASS
```

Syarat promosi:

- B0.0 sampai B0.5 hijau;
- `b0.seed` ada, executable, dan hash cocok;
- `compiler.nql0` benar-benar dibangun oleh `stage0.seed`;
- `bootstrap_compiler_b0.sh` dipanggil oleh `tests/bootstrap/run_tests.sh`;
- `make bootstrap-test` hijau;
- `bootstrap/manifest.tsv` mencatat artifact dan evidence B0;
- README bootstrap menyebut B0 sebagai PASS hanya setelah manifest berubah;
- tidak ada dependency canonical baru ke R0, LLVM, Python, NASM, C, C++, Rust,
  GCC, atau Clang;
- output B0 minimal dapat membangun fixture valid dan menolak fixture invalid;
- status Core Compiler tetap `NOT_IMPLEMENTED` sampai source Core Compiler
  benar-benar ada.

Perubahan manifest yang benar pada B0.6 berbentuk:

```text
bootstrap-compiler    PASS    bootstrap/compiler/b0/x86_64-linux/b0.seed    tests/bootstrap/bootstrap_compiler_b0.sh
```

Spacing final mengikuti format TSV manifest yang ada.

Status repository saat ini:

```text
B0.0 Scaffold PASS
B0.1 Fixed Program Emitter PASS
B0.2 Lexer Minimum PASS
B0.3 Parser Minimum PASS
B0.4 Direct Codegen PASS
B0.5 Determinism/Cleanup PASS
B0.6 Manifest Promotion PASS
bootstrap-compiler manifest PASS
core-compiler manifest NOT_IMPLEMENTED
```

Bukti B0.6:

```text
bootstrap/manifest.tsv
bootstrap/compiler/b0/x86_64-linux/b0.seed
bootstrap/compiler/b0/x86_64-linux/b0.sha256
tests/bootstrap/bootstrap_compiler_b0.sh
make bootstrap-test
```

Promosi B0.6 harus disertai regression run:

```text
make bootstrap-test
make test
```

Jika `make test` mempunyai pre-existing failure, jangan promosi B0 sampai
failure tersebut dipahami dan didokumentasikan. B0 tidak boleh menjadi PASS
dalam repository dengan regresi bootstrap yang belum dijelaskan.

### B0 Evidence Rules

Setiap promosi B0 harus menyertakan bukti yang dapat dijalankan ulang:

```text
command:
expected status:
stdout contract:
stderr contract:
artifact:
hash:
cleanup expectation:
```

Untuk output executable, evidence harus mencakup:

```text
file type:
entry behavior:
exit code:
stdout:
stderr:
dynamic interpreter: absent
stack executable: no
```

Jika salah satu bukti belum tersedia, status tetap `NOT_IMPLEMENTED`.

## Work Unit Selesai: Core Compiler C0.1

Setelah B0.7 PASS, pekerjaan canonical berikutnya adalah **Core Compiler C0**.
C0 adalah compiler pertama yang harus dibangun oleh `b0.seed`, bukan oleh
Stage 0 langsung, R0, LLVM, Python, NASM, C, C++, Rust, GCC, atau Clang.

C0 baru boleh disebut ada setelah repository mempunyai semua artifact berikut:

| Artifact | Status repository | Syarat PASS |
| --- | --- | --- |
| `bootstrap/compiler/c0/README.md` | PASS | Handoff B0 -> C0 terdokumentasi |
| `bootstrap/compiler/c0/compiler.nq` | PASS | Source C0 canonical diterima dan diturunkan semantik oleh B0 |
| `bootstrap/compiler/c0/x86_64-linux/c0.seed` | PASS | Dibangun oleh `b0.seed`, executable, hash terdokumentasi |
| `bootstrap/compiler/c0/x86_64-linux/c0.sha256` | PASS | Hash artifact canonical |
| `bootstrap/compiler/c0/x86_64-linux/materialize.sh` | PASS | Atomic write, hash verification, temp cleanup |
| `bootstrap/compiler/c0/x86_64-linux/compile.sh` | PASS | Adapter path yang menjaga output lama pada source invalid |
| `tests/bootstrap/core_compiler_c0.sh` | PASS | Build predecessor, determinism, ELF, compile-pass/fail, dan atomicity |
| `bootstrap/manifest.tsv` row `core-compiler` | PASS | Artifact dan evidence menunjuk gate C0 nyata |

### C0.0 Scaffold Contract

C0.0 adalah fase guard negatif. Tujuannya bukan menghasilkan compiler, tetapi
memastikan repository sudah mempunyai tempat canonical untuk C0 dan test suite
tidak akan membiarkan Core Compiler dipromosikan tanpa artifact nyata.

Status repository pada fase scaffold ini:

```text
C0.0 Scaffold PASS
core-compiler manifest NOT_IMPLEMENTED
c0.seed absent
c0.sha256 absent
```

Bukti C0.0:

```text
bootstrap/compiler/c0/README.md
tests/bootstrap/core_compiler_c0.sh
tests/bootstrap/run_tests.sh
make bootstrap-test
```

Test C0.0 minimum yang digunakan sebelum promosi:

```text
PASS c0-predecessor-bootstrap-pass
PASS c0-manifest-not-implemented
PASS c0-scaffold-layout
PASS c0-seed-absent-before-implementation
PASS c0-scaffold-no-host-toolchain-source
```

### C0.1 First Core Artifact Contract

C0.1 adalah titik pertama di mana `c0.seed` boleh muncul.

Syarat minimal sebelum implementasi:

- `compiler.nq` harus memakai subset yang benar-benar diterima oleh B0;
- B0 harus menurunkan source C0 secara semantik; pemilihan canned executable
  berdasarkan kecocokan seluruh byte source tidak dihitung sebagai kompilasi;
- `b0.seed` harus membangun `c0.seed` tanpa host compiler atau assembler;
- output C0 harus ELF64 x86_64 Linux syscall-only;
- hash `c0.seed` harus stabil di dua build berturut-turut;
- invalid source tidak boleh mengganti output lama;
- diagnostic minimal harus memiliki kode error dan penyebab jelas;
- manifest `core-compiler` tetap `NOT_IMPLEMENTED` sampai semua gate C0.1
  hijau.

Scope C0.1 boleh kecil. Yang penting adalah membuktikan transisi generasi:

```text
stage0.seed -> b0.seed -> c0.seed
```

Audit C0.1 awal menemukan bahwa jalur B0.4 lama memilih artifact bawaan untuk
fixture arithmetic, comparison, dan `if/else` berdasarkan kecocokan seluruh
source. Jalur sukses tersebut sekarang sudah dihapus dan diganti lowering
semantik B0.7. Primitive runtime I/O yang dibutuhkan untuk source dan artifact
juga sudah tersedia; implementasi source C0.1 kemudian menyelesaikan langkah
canonical tersebut.

Kemajuan B0.7 yang sudah dibuktikan:

- `return <u32>` diturunkan dari token source, termasuk variasi whitespace,
  comment, semicolon, dan nilai yang bukan fixture B0.1;
- `write(<string>); return <u32>` menghasilkan ELF dinamis dengan bytes string,
  panjang write, ukuran segment, dan exit status yang berasal dari source;
- escape `\n`, `\r`, `\t`, `\\`, dan `\"` diturunkan tanpa runtime host;
- string hasil decode dibatasi 2.048 byte dan overflow menghasilkan
  `B0-CG-005` tanpa artifact output;
- sampai 16 local memakai slot stack tetap 128 byte;
- assignment memutasi local yang sudah dideklarasikan dan menolak target yang
  tidak dikenal dengan `B0-CG-007` beserta path, line, dan column aktual;
- literal, local load/store, grouping, `*`, `/`, `+`, `-`, `<`, `<=`, `==`,
  dan `!=` menghasilkan instruction x86_64 dari token source dengan precedence
  stabil;
- division-by-zero juga ditemukan melalui expression/local konstan, bukan
  hanya fixture literal tertentu;
- edge case `INT64_MIN / -1` ditolak dengan `B0-CG-006`, bukan membuat B0
  crash karena machine division trap;
- `if/else` menghasilkan conditional `rel32` nyata dengan patch deterministik,
  dan jalur true maupun false dibuktikan oleh test;
- `while` sederhana menghasilkan conditional exit `rel32` dan unconditional
  backward `rel32` nyata; loop taken, zero-iteration, loop berurutan, beberapa
  mutasi local, invalidasi metadata konstan, dan determinism dibuktikan oleh
  test;
- `byte_store(index, value)` dan `byte_load(index)` memakai region mutable
  zero-initialized 65.536 byte yang terpisah dari 16 slot local; store mengambil
  delapan bit rendah dan load melakukan zero-extension ke integer 64-bit;
- `byte_load` dikenali sebagai intrinsic hanya pada posisi call; local bernama
  `byte_load` tetap diselesaikan sebagai binding biasa, dan bentuk
  `byte_store` yang belum lengkap ditolak sebagai syntax unsupported sebelum
  pemeriksaan bounds sehingga diagnostic tidak menyesatkan;
- index konstan di luar `0..65535` ditolak di lokasi source aktual dengan
  `B0-CG-008`, sedangkan index dinamis dijaga oleh unsigned bounds check yang
  menuju satu handler bersama, menulis diagnostic ke stderr, lalu exit 70;
- test byte-memory membuktikan loop read/write dinamis, truncation ke satu byte,
  zero-extension, zero initialization, batas maksimum tanpa menimpa slot local,
  seluruh patch guard load/store menuju tepat satu handler, output deterministik,
  preservasi output lama pada error, dan runtime out-of-bounds tanpa hang;
- `input_read(offset, count)` melakukan satu raw `read` dari fd 0 ke rentang
  byte-memory dan mengembalikan jumlah byte atau 0 saat EOF;
- `output_write(offset, count)` menulis seluruh rentang byte-memory ke fd 1,
  termasuk melanjutkan short write sampai semua byte terkirim;
- kedua primitive I/O memakai pemeriksaan rentang unsigned yang sama dengan
  byte-memory, menolak rentang konstan invalid dengan `B0-CG-008`, dan untuk
  kegagalan syscall menulis diagnostic ke stderr lalu exit 74;
- metadata rentang disimpan per parse invocation, sehingga nested
  `input_read(...)` tidak dapat menimpa bukti konstan milik call di luarnya;
- generated prologue memasang `SIG_IGN` untuk `SIGPIPE` dengan
  `rt_sigaction`; kegagalan setup memiliki diagnostic sendiri, sedangkan broken
  pipe mencapai handler write normal dan exit 74, bukan terminasi diam-diam 141;
- test I/O membuktikan binary byte roundtrip pada nonzero offset, EOF, byte
  terakhir dan seluruh 65.536 byte region, call-position binding, nested
  constant validation, determinism, preservasi output lama, bounds konstan,
  dinamis, dan negatif, beberapa patch output, malformed call, closed fd, serta
  broken pipe tanpa hang;
- tidak ada lagi whole-source identity check pada compile path; program valid
  diturunkan semantik dan unsupported zero-argument call dikenali struktural;
- tabel patch byte-access B0 dinaikkan secara bounded dari 512 menjadi 1.024
  entry setelah source C0.3a terbukti melampaui batas lama;
- arena output B0 dinaikkan dari 65.536 menjadi 131.072 byte setelah artifact
  C0.3b yang dapat direproduksi mencapai 77.113 byte; perubahan B0.7h hanya
  capacity bridge dan tidak memindahkan syntax/semantik bahasa baru ke B0;
  gate batas menerima artifact 131.060 byte lalu membuktikan langkah emisi
  18 byte berikutnya ditolak dengan `B0-CG-005` tanpa meninggalkan output;
- tabel patch byte-access B0 dinaikkan lagi secara bounded dari 1.024 menjadi
  2.048 entry setelah source C0.3c terbukti melampaui batas lama; perubahan
  B0.7i hanya capacity bridge, arena output tetap 131.072 byte, dan `c0.seed`
  C0.3c yang dapat direproduksi berukuran 98.215 byte; gate batas menerima
  tepat 2.048 patch, lalu menolak patch ke-2.049 dengan `B0-CG-005` tanpa
  artifact parsial atau output stdout;
- arena source B0 dinaikkan dari 65.536 menjadi 131.072 byte setelah
  `compiler.nq` C0.4 mencapai 73.815 byte; B0.7j menambah overflow probe satu
  byte agar source lebih besar tidak terpotong diam-diam, dan gate menolak
  byte 131.073 dengan `B0-IO-003` tanpa artifact output;
- arena output B0 dinaikkan dari 131.072 menjadi 196.608 byte setelah decoder
  `byte_parse_u8` membuat artifact C0.7 reproducible berukuran 134.891 byte;
  B0.7k menerima output 196.598 byte lalu menolak langkah emisi 18 byte
  berikutnya dengan `B0-CG-005` tanpa artifact parsial dan tanpa menambah
  semantik bahasa B0;
- tabel patch byte-access B0 dinaikkan dari 2.048 menjadi 2.560 entry dan
  arena output dari 196.608 menjadi 262.144 byte setelah C0.10 membuktikan
  kedua batas lama tidak cukup; B0.7l menerima tepat 2.560 patch dan artifact
  262.136 byte, lalu menolak patch ke-2.561 serta langkah emisi berikutnya
  dengan `B0-CG-005` tanpa artifact parsial atau perubahan semantik B0;
- arena source B0 dinaikkan dari 131.072 menjadi 196.608 byte setelah source
  C0.15 mencapai 136.042 byte; B0.7m menerima tepat 196.608 byte dan menolak
  byte 196.609 dengan `B0-IO-003`, sedangkan arena output, tabel patch, grammar,
  dan semantik B0 tetap tidak berubah;
- arena output B0 dinaikkan dari 262.144 menjadi 393.216 byte dan tabel patch
  byte-access dari 2.560 menjadi 3.072 entry setelah C0.16 melampaui kedua
  batas lama; B0.7n menerima tepat 3.072 patch dan output 393.212 byte, lalu
  menolak patch ke-3.073 serta langkah emisi 18 byte berikutnya dengan
  `B0-CG-005` tanpa artifact parsial atau perubahan grammar B0;
- artifact B0 tetap dibangun oleh `stage0.seed`, mempunyai hash baru, dan lulus
  gate bootstrap B0.

Kontrak I/O bootstrap sengaja berbasis stream. C0 membaca source dari fd 0 dan
menulis artifact ke fd 1; materializer luar bertanggung jawab atas path, temp
file, hash, dan atomic rename. Pemisahan ini membuat generated compiler tetap
syscall-only dan tidak menyembunyikan filesystem policy di dalam B0.

B0.7n dan Core Compiler sampai C0.16 sekarang `PASS`. `compiler.nq` membaca
source dari fd 0, melakukan tokenisasi bounded, memvalidasi bentuk function
utama, beberapa deklarasi `let`, dan expression u8 `+`/`*`, lalu menghasilkan
ELF64 x86_64 syscall-only ke fd 1. String `write` bounded diturunkan menjadi
payload mesin yang ditulis ke fd 1 saat program hasil dijalankan. Nilai
expression dan local diturunkan ke immediate machine code, sehingga source
dengan nilai semantik berbeda menghasilkan bytes artifact berbeda. Input
invalid menghasilkan `C0-001` beserta line/column aktual di fd 2 dan exit 1
tanpa bytes artifact. Subset runtime C0.3a menurunkan operasi byte memory dan
raw `read` langsung ke executable target dengan segment data RW terpisah.
C0.3b menurunkan copy/subtract byte dinamis serta loop non-nested menjadi
instruction x86_64 dan patch `rel32` langsung. C0.3c menurunkan output byte
dinamis ordered ke fd 1 dengan complete-write loop, setup `SIGPIPE`, satu
handler error bersama, diagnostic byte-exact, dan exit 74. C0.3d memasukkan
literal `write` ke operation stream yang sama, menempatkan payload literal di
segment RX, dan mem-patch alamat RIP-relative tanpa mengubah bytes artifact
program static-only yang sudah dibekukan. C0.4 menambahkan runtime intrinsic
`byte_assert_range` dengan full-width u8 comparison, satu handler invalid-input
bersama, diagnostic exact, dan exit 1. C0.5 mempertahankan primitive tersebut,
tetapi memvalidasi seluruh keyword `return`, separator satu spasi, digit, LF,
dan EOF sentinel sebelum byte artifact pertama ditulis. Arena source C0 naik
secara bounded menjadi 1.536 byte dan tabel token menjadi 192 entry; byte
1.537 dan token 193 ditolak pada lokasi sebenarnya tanpa artifact. C0.6
menambahkan digit kedua dan menghitung nilai `00..99` melalui dua loop
byte-memory bounded. Kapasitas token menjadi 240, sedangkan kapasitas operation
tetap 32 dan dipakai penuh oleh successor. C0.7 menambahkan decoder decimal u8
bounded untuk satu sampai tiga digit, menolak nilai di atas 255, dan
memindahkan enam tabel token ke rentang 256-byte yang benar-benar disjoint.
Successor C0.7 memakai 22 operation dan menerima seluruh `0..255`.
C0.8 menambahkan decoder suffix `byte_parse_u8_then`, memakai grammar function
envelope exact, dan menghasilkan successor 31-operation yang tetap berada di
bawah batas 32. Probe successor terhadap source-nya sendiri sekarang cocok
sampai `fn main(){` dan LF, lalu ditolak pada `byte_store` baris kedua tanpa
artifact; inilah blocker berikutnya yang dibuktikan, bukan perkiraan.
C0.9 menambahkan dispatcher mesin `byte_parse_stmts` untuk nol sampai tiga
statement exact `byte_store(u8,u8)` sebelum satu literal `return`. Karena
grammar ini tidak memiliki `byte_load`, output, atau observasi memory lain,
store tersebut terbukti dead dan successor boleh menghasilkan artifact return
188-byte yang sama. Successor turun menjadi 24 operation; probe aktual sekarang
melewati tiga `byte_store` dan berhenti pada `input_read` baris kelima. C0.10
memperluas dispatcher menjadi grammar optional-input bounded, menambahkan flag
metadata untuk memilih artifact return 188 byte atau artifact `input_read`
377 byte, dan menjaga keduanya byte-identik dengan output langsung C0. Source
successor 2.449 byte menghasilkan artifact 1.802 byte. Probe aktual kini
menerima `input_read(32,96)` lalu berhenti pada `byte_parse_stmts` baris ketiga.
C0.11 menambahkan tail dispatcher bounded untuk exact
`byte_parse_stmts(32,0)`, metadata parser byte keempat, dan jalur artifact
parser 949 byte yang identik dengan output langsung. Source successor 3.905
byte memakai `\0`, kapasitas source/literal menjadi 4.096/1.536 byte, dan
scratch lama dipindahkan dari `3080..3999` ke `13080..13999` setelah gate
membuktikan overlap. Artifact successor sekarang 3.081 byte; probe aktual
melewati parser dan berhenti pada `byte_store(4,184)` baris keempat.
C0.12 memakai kembali body store generik di dispatcher 499 byte untuk menerima
tepat satu `byte_store(u8,u8)` pascaparser. Stub tujuh byte menggantikan bagian
NOP yang memang dicadangkan, metadata tetap empat byte, dan tidak ada operation
kind maupun capacity predecessor baru. Bound source intrinsic diperketat ke
`<=109` agar lookahead store terpanjang tetap berada dalam memory 256 byte;
destination tetap `<=252`. Source successor hasil regenerasi berukuran 3.903
byte, artifact tetap 3.081 byte, dan probe sekarang berhenti pada store kedua
`byte_store(5,60)` di baris kelima. C0.13 mengubah immediate counter stub dari
dua menjadi satu sehingga body store yang sama menerima dua store pascaparser
dan menolak yang ketiga. Dispatcher tetap 499 byte, metadata tetap empat byte,
dan bound source intrinsic diperketat ke `<=89`; destination tetap `<=252`.
Source successor tetap 3.903 byte, artifact tetap 3.081 byte, dan probe
berhenti pada store ketiga `byte_store(9,15)` di baris keenam. C0.14 tidak
memperlebar grammar store: empat store setup tail dihapus, sedangkan setiap
jalur return/input sekarang mengeluarkan satu byte return dinamis dengan
`output_write(0,1)` diikuti literal tail ELF konstan sepuluh byte. Perubahan
ini mempertahankan output target byte-for-byte, mengurangi state runtime, dan
memindahkan probe ke `while byte_load(1)` di baris keempat. Source successor
menjadi 3.902 byte dan artifact 3.165 byte; artifact C0 tetap identik karena
semantik compilernya tidak berubah.

C0.15 memperluas default branch dispatcher dengan matcher exact 80 byte untuk
satu bentuk clear-loop lengkap: `while byte_load(1)`, body
`byte_store(1,0)`, dan brace/newline penutup. Matcher menyimpan dan memulihkan
`RSI`/`RDI`, membandingkan 39 source byte, kembali ke dispatch setelah match,
dan menuju handler invalid bersama setelah mismatch. Loop itu terminating dan
tidak mengubah output successor, sehingga lowering successor menghapusnya
tanpa mengklaim loop umum. Dispatcher menjadi 579 byte; source bound intrinsic
menjadi `<=50` sementara destination tetap `<=252`. Payload parser hasil direct
C0 dan successor sama-sama 1.029 byte. Source successor 4.079 byte dan artifact
3.371 byte. Total literal C0 naik bounded menjadi 2.048 byte, sedangkan source
C0 tetap dibatasi 4.096 byte. Karena source compiler sendiri tumbuh menjadi
136.042 byte, B0.7m menaikkan hanya input predecessor ke 196.608 byte; byte
196.609 ditolak dan kapasitas output/patch tidak berubah. Probe self-source
sekarang gagal bersih pada `write` di body loop baris kelima.

C0.16 menambahkan matcher exact untuk seluruh return-emitter pertama successor
sebagai satu construct 477-byte pada baris 4--9. Matcher melakukan refill
bounded sampai 512 byte, membandingkan sequence penuh, lalu menulis metadata
kelima hanya pada full match. Destination bound menjadi `<=251`; artifact
parser direct dan successor sama-sama 1.625 byte. Parser-bearing artifact
memakai private BSS 1 KiB di `0x402000`, sementara artifact runtime biasa tetap
memakai 256 byte di `0x401000`. Source input C0 naik bounded menjadi 8.192 byte
dan total literal menjadi 3.072 byte. Successful source tail di atas offset
4.096 dibersihkan sebelum sparse ELF emission. Source successor menjadi 5.088
byte, artifact successor 4.655 byte, source compiler 176.953 byte, dan artifact
C0 298.359 byte. B0.7n menaikkan hanya output/patch predecessor seperti dicatat
di atas. Probe self-source kini mengonsumsi seluruh construct pertama dan gagal
bersih pada `while byte_load(3)` di baris 10.

Bukti C0.1 sampai C0.16 yang dapat dijalankan ulang:

```text
bootstrap/compiler/c0/compiler.nq
bootstrap/compiler/c0/successor.nq
bootstrap/compiler/c0/x86_64-linux/c0.seed
bootstrap/compiler/c0/x86_64-linux/c0.sha256
bootstrap/compiler/c0/x86_64-linux/c0-successor.seed
bootstrap/compiler/c0/x86_64-linux/c0-successor.sha256
bootstrap/compiler/c0/x86_64-linux/materialize.sh
bootstrap/compiler/c0/x86_64-linux/materialize-successor.sh
bootstrap/compiler/c0/x86_64-linux/compile.sh
tests/bootstrap/core_compiler_c0.sh
tests/bootstrap/fixtures/c0/
make bootstrap-test
```

Gate membuktikan dua build B0 identik, dua materialisasi identik, hash
canonical, ELF statis tanpa interpreter, stack non-executable, beberapa nilai
return, precedence multiplication-before-addition, associativity addition,
beberapa local dan dependency chain, duplicate/unknown binding, batas delapan
local, batas u8, batas 8.192 byte/240 token, diagnostic line/column exact sampai
empat digit, string/binary output termasuk `\0`, batas 255 byte per literal dan
3.072 byte total literal, byte memory bounded,
runtime input pada offset nonzero, EOF, closed-fd exit 74, batas rentang,
dynamic output binary/zero-length/loop-order, broken pipe nyata melalui FIFO,
complete-write machine bytes, literal/runtime order, segment RX/RW tanpa RWX,
successor source function-envelope dengan textual satu sampai tiga digit untuk nilai
0/7/`00`/42/`099`/100/255 yang menghasilkan artifact source-dependent dan
cocok dengan output langsung C0, bounded dead-store statement dispatch,
optional exact `input_read(32,96)` serta dependent exact
`byte_parse_stmts(32,0)` dengan runtime/closed-fd behavior yang sama,
bentuk source successor invalid tanpa artifact,
`byte_parse_u8_then`, `byte_parse_stmts`, exact source/destination metadata
bounds `50/51` dan `251/252`, dua dead store pascaparser, split return-tail
dinamis/konstan dengan parity return/input/parser, exact terminating clear-loop,
exact return-emitter beserta malformed rejection, private parser BSS 1 KiB,
source-tail clearing, probe rebuild yang berhenti pada `while byte_load(3)`
di baris 10, high-offset token-table
isolation, cleanup temp, dan preservasi
output lama pada kegagalan. Gate juga
menolak malformed `let`,
malformed escape/string, whitespace di dalam keyword/angka, keyword tanpa
separator lexical, operator yang belum didukung, arithmetic di atas dynamic
load, overflow expression, seed C0 yang hash-nya
berubah, dan target output berbentuk direktori. Status PASS berarti transisi
generasi dan subfase sampai C0.16 nyata sudah terbukti, bukan bahwa Full
NolQu-L selesai.

### Work Unit Selesai: C0.2 Structured Core

C0.2 harus dikembangkan di `compiler.nq`, bukan dengan memperbesar scope B0.
Status bertahap saat ini:

```text
C0.2a bounded lexer + located diagnostic + u8 expression precedence PASS
C0.2b multiple statement + local integer                           PASS
C0.2c bounded write + successor emitter built by C0                PASS
```

C0.2b menggunakan lexer state-machine satu pass dengan tabel paralel bounded
untuk kind, nilai u8, panjang token, dan offset source 16-bit. Grammar
expression yang sudah dibuktikan adalah `term ("+" term)*` dan
`factor ("*" factor)*`, dengan factor berupa u8 atau local. Parser menerima
beberapa deklarasi `let` immutable sebelum `return`. Bootstrap contract
membatasi delapan local bernama satu huruf ASCII kecil; lookup langsung ini
bounded, exact, dan collision-free, bukan batas identifier Full NolQu-L. Setiap
intermediate harus tetap di `0..255`; subtraction, division, grouping, dan
assignment masih ditolak secara eksplisit.

C0.2c menambah token string, escape `\n`/`\r`/`\t`/`\\`/`\"`/`\xNN`,
beberapa statement `write`, dan payload decoded maksimum 255 byte. Program
tanpa payload mempertahankan ELF 188 byte; program output menghasilkan ELF
`212 + payload` byte yang memakai syscall `write`. `c0.seed` membangun
`c0-successor.seed` dua kali secara identik, lalu successor tersebut
menghasilkan ELF return-42 yang byte-for-byte sama dengan output langsung C0.
Seluruh transisi memakai artifact canonical tanpa compiler, assembler, linker,
Python, atau LLVM host.

Pada C0.2c successor tersebut masih fixed semantic emitter. C0.3d telah
menggantinya dengan successor source-consuming bounded, tetapi belum membangun
dirinya sendiri. Karena itu bukti C0.2c tetap sejarah transisi generasi nyata,
bukan self-hosting.

### Work Unit Selesai: C0.3 Runtime Compiler Substrate

Status bertahap C0.3:

```text
C0.3a bounded byte memory + runtime input_read   PASS
C0.3b assignment + minimum control flow          PASS
C0.3c dynamic output_write                       PASS
C0.3d source-consuming successor                 PASS
```

C0.3a menerima subset runtime berikut:

```text
runtime_stmt  := "input_read" "(" u8 "," u8 ")" ";"?
               | "byte_store" "(" u8 "," u8 ")" ";"?
runtime_return := "return" "byte_load" "(" u8 ")" ";"?
```

Executable runtime mempunyai region byte memory zero-initialized 256 byte.
`input_read(offset, count)` melakukan satu syscall `read(0, ...)`, mewajibkan
`offset + count <= 256`, mengizinkan EOF, memblokir `SIGPIPE` sebelum menulis
diagnostic tetap secara complete-write ke fd 2, dan exit 74 pada error syscall
termasuk ketika fd diagnostic tidak dapat ditulis.
`byte_store` menyimpan satu byte dan `byte_load` zero-extend byte menjadi exit
status. Artifact memakai satu `PT_LOAD` RX, satu `PT_LOAD` RW tanpa file bytes,
serta GNU stack non-executable; tidak ada segment RWX.

C0.3b memperluas subset runtime secara bounded:

```text
dynamic_store := "byte_store" "(" u8 "," "byte_load" "(" u8 ")"
                 ("-" u8)? ")" ";"?
runtime_leaf  := "input_read" "(" u8 "," u8 ")" ";"?
               | "byte_store" "(" u8 "," u8 ")" ";"?
               | dynamic_store
while_stmt    := "while" "byte_load" "(" u8 ")" "{"
                 runtime_leaf* "}"
runtime_stmt  := runtime_leaf | while_stmt
```

Dynamic store menyalin satu byte atau mengurangi immediate dengan wrap modulo
256. `while` menguji byte memory terhadap nol, memakai conditional forward
`rel32`, dan kembali dengan unconditional backward `rel32`. Beberapa loop
berurutan diterima, tetapi nested loop sengaja ditolak di lokasi keyword
`while` terdalam agar C0 tetap mempunyai state parser bounded tanpa stack.
Tabel operasi tetap dibatasi 32 entry termasuk marker awal/akhir loop.

C0.3c memperluas `runtime_leaf` dengan:

```text
output_write := "output_write" "(" u8 "," u8 ")" ";"?
```

`output_write(offset, count)` membaca rentang dari byte memory 256 byte dan
menulisnya ke fd 1 sesuai urutan operation stream, termasuk ketika dipanggil
di dalam `while` non-nested. Rentang wajib memenuhi `offset + count <= 256`;
count nol berhasil tanpa syscall. Artifact target memblokir `SIGPIPE` sekali,
mengulang short write sampai seluruh rentang selesai, lalu pada hasil syscall
nol/negatif menuju satu handler bersama yang menulis
`runtime: output_write failed\n` ke fd 2 secara complete-write dan exit 74.
Jika fd 2 juga gagal, status tetap 74 tanpa recursion atau silent success.
Empat bentuk artifact output dikunci dengan hash dan dua build identik.

Metadata 32 operation target ditempatkan pada byte `10000..10255`: kind dan
argument berada pada `10000..10127`, patch branch output pada
`10128..10191`, dan patch alamat literal pada `10192..10255`. Semuanya
terpisah dari code emitter yang tumbuh dari byte 4.328 dan tetap di bawah
scratch byte 12.000. Pemisahan ini memperbaiki overlap lama pada byte
`6400..6591` yang dapat membuat program panjang menimpa metadata operation
berikutnya. Karena batas 128 token lebih ketat daripada tabel 32 operation
untuk grammar saat ini, gate regresi memenuhi batas yang benar-benar
terjangkau: 19 `input_read` berurutan serta `output_write` setelah 18
`input_read`. Keduanya membuktikan operation terakhir tetap dieksekusi,
branch error tetap ter-patch, dan closed stdout tidak hang.

C0.3d menghapus batas sementara campuran static `write` dan runtime.
Literal non-kosong menjadi operation kind tersendiri, payload-nya disimpan
sekali di RX, dan alamatnya dipatch RIP-relative setelah ukuran code final
diketahui. Literal kosong menjadi no-op. Semua literal dan
`output_write` mengikuti urutan source serta memakai complete-write,
penanganan `SIGPIPE`, diagnostic byte-exact, dan exit 74 yang sama. Program
static-only tetap menghasilkan bytes artifact lama. `byte_load` masih hanya
boleh menjadi seluruh return factor tanpa arithmetic tambahan; bentuk itu
tetap ditolak dengan lokasi source dan tanpa artifact.

Successor canonical C0.3d memakai kontrak source mesin bounded:

```text
byte pertama fd 0 (u8) -> standalone ELF return-u8 188 byte
```

EOF berarti nilai nol dan byte tambahan diabaikan. Successor menulis prefix ELF
177 byte, membaca source, membangun tail machine code 11 byte di byte-memory
eksplisit, lalu menulis tail tersebut. Gate menjalankannya dengan `0x2a` dan
`0x41`, membuktikan kedua artifact berbeda, deterministic, dan byte-for-byte
sama dengan output C0 langsung untuk return 42 dan 65. Closed stdout wajib
mencapai diagnostic output dan exit 74. Ini adalah format source mesin
sementara, bukan grammar textual NolQu-L dan bukan klaim self-hosting.

### Work Unit Selesai: C0.4 Bounded Textual Successor

C0.4 mengganti source mesin satu byte dengan grammar textual exact pertama:

```text
source := digit LF EOF
digit  := "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

Successor membaca maksimum tiga byte setelah memasang sentinel 255. Dua byte
pertama wajib digit ASCII dan LF; sentinel wajib tetap 255 agar trailing ASCII
input ditolak. Input kosong, non-digit, LF hilang, atau trailing byte tidak
menghasilkan artifact, menulis tepat `runtime: invalid source\n` ke fd 2, dan
exit 1. Program `2\n` dan `7\n` menghasilkan ELF return-2 dan return-7 yang
byte-for-byte sama dengan output langsung C0 dan berbeda satu sama lain.

Primitive baru `byte_assert_range(offset, minimum, maximum)` divalidasi saat
compile (`minimum <= maximum`) dan diturunkan menjadi load u8, subtraction
immediate 32-bit, comparison unsigned, serta branch `rel32` ke satu handler
invalid-source bersama. Immediate 32-bit sengaja dipakai agar batas 128..255
tidak terkena sign-extension `imm8`; gate mencakup sentinel 255. Handler
melakukan complete write, tetapi tetap exit 1 jika fd 2 tidak tersedia.

Perubahan ini mendorong source `compiler.nq` melewati 65.536 byte. B0.7j
menaikkan hanya kapasitas source menjadi 131.072 byte dan menambah overflow
probe; byte 131.073 ditolak secara eksplisit, bukan dipotong diam-diam. Semantik
bahasa B0 tidak bertambah. Artifact canonical pada akhir C0.4:

```text
b0.seed            52.600 byte
c0.seed           116.545 byte
c0-successor.seed   1.046 byte
```

Urutan minimum pada akhir C0.4:

1. C0.4 textual successor tetap dikunci oleh determinism, hash,
   source-dependence, parity, invalid-input, dan error-path gate (`PASS`);
2. C0.5 memperluas grammar menjadi textual return source yang located dan
   tetap bounded, bukan langsung melompat ke parser Full NolQu-L;
3. baru uji rebuild compiler source generasi berikutnya sebelum klaim
   self-hosting apa pun.

C0.3a sampai C0.4 tetap `PASS`; status lanjutannya dicatat pada work unit C0.5
di bawah.

### Work Unit Selesai: C0.5 Located Textual Return Source

C0.5 memperluas grammar successor menjadi source return yang memiliki keyword
dan separator eksplisit:

```text
source := "return" SP digit LF EOF
digit  := "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

Successor memasang sentinel 255 di offset 41, membaca paling banyak sepuluh
byte ke offset 32, lalu memvalidasi enam byte keyword `return`, satu ASCII
space, digit, LF, dan sentinel. Seluruh validasi berjalan sebelum tiga bagian
prefix ELF ditulis. Karena itu input kosong, keyword salah, separator hilang,
non-digit, LF hilang, dan trailing byte semuanya exit 1 dengan tepat
`runtime: invalid source\n` di fd 2 serta nol byte artifact. Source
`return 2\n` dan `return 7\n` menghasilkan artifact deterministic yang
byte-for-byte sama dengan output langsung C0 dan berjalan dengan exit 2/7.

Source successor kini 1.209 byte dan melampaui bound C0 lama 1.024 byte.
Kapasitas source C0 dinaikkan secara fixed menjadi 1.536 byte; byte 1.537
ditolak di `input:1:1537`. Grammar successor juga melampaui bound lama 128
token, sehingga kapasitas token dinaikkan menjadi 192; token 193 ditolak di
lokasi aktual. Tabel paralel tetap berjarak 256 byte, sehingga bound 192
menyisakan 64 slot guard sebelum tabel berikutnya dan tidak mengubah layout
memori. Ini capacity bridge C0, bukan tambahan semantik pada B0.

Artifact canonical C0.5:

```text
b0.seed            52.600 byte
c0.seed           116.545 byte
c0-successor.seed   1.207 byte
```

Identitas canonical C0.5:

```text
c0.seed            55e799088648231d0f879cebf331a652dcc46ee5e1a3945022953d1950aad8ec
c0-successor.seed  16b32581b5337e5719235ea211b2b6253df4b317dcbe6f4e9fbc740792af9d02
```

Urutan minimum berikutnya:

1. C0.5 tetap dikunci oleh predecessor rebuild, hash, determinism, parity,
   source-dependence, enam invalid-input gate, dan error-path gate (`PASS`);
2. C0.6 memperluas nilai textual return melampaui satu digit dengan operasi
   byte-memory eksplisit dan bound tetap;
3. baru uji rebuild compiler source generasi berikutnya sebelum klaim
   self-hosting apa pun.

C0.3a sampai C0.5 tetap `PASS`; status lanjutannya dicatat pada work unit C0.6
di bawah.

### Work Unit Selesai: C0.6 Two-Digit Textual Return Source

C0.6 memperluas nilai return dari satu digit menjadi tepat dua digit:

```text
source := "return" SP digit digit LF EOF
digit  := "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

Range yang diterima adalah `00..99`. Successor memasang sentinel 255 di offset
42, membaca paling banyak sebelas byte ke offset 32, dan memvalidasi seluruh
keyword, separator, kedua digit, LF, serta EOF sebelum menulis artifact. Gate
menolak input kosong, keyword salah, separator hilang, hanya satu digit,
non-digit pada masing-masing posisi, LF hilang, trailing byte, dan tiga digit.
Semua jalur invalid menghasilkan nol byte artifact, diagnostic exact, dan
exit 1.

Konversi decimal tidak memakai parser tersembunyi. Digit puluhan dan satuan
diubah menjadi counter byte pada offset 43/44. Loop pertama menambah sepuluh ke
accumulator dengan operasi modulo-byte `-246`; loop kedua menambah satu dengan
`-255`. Kedua counter dibatasi `0..9`, sehingga accumulator maksimum 99 dan
tidak wrap. Source `return 42\n` dan `return 65\n` menghasilkan artifact yang
berbeda, deterministic, byte-for-byte sama dengan output langsung C0, dan
berjalan dengan exit 42/65.

Source successor C0.6 berukuran 1.454 byte, masih di bawah arena 1.536 byte.
Kapasitas token naik dari 192 menjadi 240; token 241 ditolak di
`input:119:3`. Successor memakai tepat seluruh 32 operation record yang sudah
ada; batas operation tidak dinaikkan. Audit C0.7 kemudian membuktikan bahwa
klaim lama tentang guard antartabel tidak benar: offset-high token 128 ke atas
dapat menimpa length-low token awal. Status C0.6 tetap sejarah transisi yang
lolos fixture saat itu, sedangkan layout-nya diperbaiki dan dikunci oleh gate
regresi C0.7.

Artifact canonical C0.6:

```text
b0.seed            52.600 byte
c0.seed           116.545 byte
c0-successor.seed   1.348 byte
```

Identitas canonical C0.6:

```text
c0.seed            9ab8c2a07e6feb502e4e8901152feaaa27753fc155b141af12b8ff91b578530c
c0-successor.seed  875d45ad99235b941782837ea15ad8fd667041a85a17304c387294a8a28433fc
```

Urutan minimum berikutnya:

1. C0.6 tetap dikunci oleh predecessor rebuild, hash, determinism, parity,
   source-dependence, sembilan invalid-input gate, exact operation capacity,
   dan error-path gate (`PASS`);
2. C0.7 memperluas fixed `00..99` menjadi seluruh textual u8 dengan parsing
   bounded dan biaya mesin yang tetap terlihat;
3. baru uji rebuild compiler source generasi berikutnya sebelum klaim
   self-hosting apa pun.

C0.3a sampai C0.6 tetap `PASS`. Status lanjutannya dicatat pada work unit C0.7
di bawah.

### Work Unit Selesai: C0.7 Full Textual U8 Return Source

C0.7 memperluas grammar successor menjadi seluruh textual u8:

```text
source     := "return" SP decimal-u8 LF EOF
decimal-u8 := digit | digit digit | digit digit digit
digit      := "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

Leading zero diterima selama spelling tetap satu sampai tiga digit: `00`
bernilai 0 dan `099` bernilai 99. Nilai `256..999`, empat digit termasuk
`0255`, digit kosong, karakter non-digit, LF hilang, dan byte setelah LF
ditolak sebelum artifact pertama ditulis. Semua jalur itu menghasilkan tepat
`runtime: invalid source\n` di fd 2, nol byte stdout, dan exit 1.

Intrinsic baru `byte_parse_u8(source_offset, destination_offset)` diturunkan
menjadi decoder x86_64 fixed 160 byte. Decoder membaca maksimum lima byte dari
byte-memory runtime, memvalidasi satu sampai tiga digit, LF, dan sentinel 255,
menghitung decimal di register, memeriksa hasil `<=255`, lalu menyimpan satu
u8. Source offset compile-time dibatasi `<=251`; setiap kegagalan lokal menuju
satu stub `rel32` yang dipatch ke handler invalid-source bersama. Tidak ada
parser host atau runtime library tersembunyi.

Successor memasang sentinel pada offset 39..43, membaca paling banyak 12 byte
ke offset 32, memvalidasi keyword `return` dan satu spasi, lalu memanggil
`byte_parse_u8(39,0)`. Source successor menyusut menjadi 1.188 byte dan memakai
22 dari 32 operation record. Gate membuktikan parity byte-for-byte terhadap C0
langsung untuk 0, 7, `00`, 42, `099`, 100, dan 255; setiap artifact berjalan
dengan exit status yang sesuai dan dua build selalu identik.

C0.7 juga menutup bug layout token laten. Enam tabel paralel 256-byte sekarang
berada pada rentang disjoint mulai byte 16.000: kind, value, offset-low,
offset-high, length-low, dan length-high. Gate regresi membangun source valid
dengan token ke-134 berada di atas offset 1.024; bentuk ini gagal sebelum fix
karena offset-high menimpa length-low token awal, dan sekarang compile serta
berjalan dengan exit 0.

Decoder membuat artifact C0 tumbuh melewati arena output B0 lama. B0.7k hanya
menaikkan `OUTPUT_CAP` dari 131.072 menjadi 196.608 byte. Gate menerima
artifact near-limit 196.598 byte lalu menolak langkah emisi 18 byte berikutnya
dengan `B0-CG-005` tanpa output parsial. Syntax dan semantik B0 tidak berubah.

Artifact canonical C0.7:

```text
b0.seed            52.600 byte
c0.seed           134.891 byte
c0-successor.seed   1.311 byte
```

Identitas canonical C0.7:

```text
b0.seed            e665b4907c3cc177461794edf58eaea848420b29b21d257fdd13befbab908b93
c0.seed            49f57f4b15f8d23ab891ee8b3a385ce61b6c10d572a63ac8342641fe503c9f78
c0-successor.seed  3014b5f0c1efc3f311bd193a80f6b4c157cd961cf58649a9ff23f51b8297a42b
```

Urutan minimum berikutnya:

1. C0.7 tetap dikunci oleh predecessor rebuild, hash, determinism, full-u8
   parity, sepuluh invalid-input gate, token-layout high-offset regression,
   error-path gate, dan B0.7k capacity boundary (`PASS`);
2. C0.8 menjalankan probe rebuild terhadap source compiler generasi berikutnya
   dan mencatat construct atau resource bound pertama yang gagal;
3. capability baru hanya ditambahkan jika probe tersebut membuktikan kebutuhan,
   lalu probe diulang sebelum klaim self-hosting apa pun.

C0.3a sampai C0.7 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai artifact serta reproducible multi-generation gate
masing-masing tersedia.

### Work Unit Selesai: C0.8 Function-Envelope Rebuild Probe

Probe awal menjalankan successor C0.7 terhadap source generasi berikutnya
`successor.nq`. Artifact menolak byte pertama karena masih mengharapkan
`return`, sedangkan source compiler dimulai dengan `fn`. C0.8 menyeberangi
batas itu dengan grammar exact yang tetap kecil dan dapat diaudit:

```text
source     := "fn" SP "main" "(" ")" "{" LF
              "return" SP decimal-u8 "}" LF EOF
decimal-u8 := digit | digit digit | digit digit digit
```

Source valid berbentuk `fn main(){\nreturn <u8>}\n`. Ini belum lexer umum:
spasi dan LF berada pada posisi exact agar biaya parser generasi ini tetap
terlihat. Nilai 0, 7, `00`, 42, `099`, 100, dan 255 menghasilkan artifact
188-byte yang byte-for-byte sama dengan output langsung C0. Delapan belas
bentuk envelope, keyword, delimiter, angka, newline, overflow, dan trailing
input invalid ditolak sebelum byte artifact pertama ditulis.

Intrinsic baru
`byte_parse_u8_then(source_offset, destination_offset, terminator)` menurunkan
decoder x86_64 fixed 190 byte. Decoder membaca maksimum enam byte, menerima
satu sampai tiga digit diikuti terminator compile-time, LF, dan sentinel 255,
memeriksa nilai `<=255`, lalu menyimpan satu byte. Source offset dibatasi
`<=250`; seluruh kegagalan menuju handler invalid-source bersama dan exit 1.
`byte_parse_u8` C0.7 tetap tersedia dan gate regresinya tetap hijau.

Pertumbuhan code target dari intrinsic ini menemukan overlap laten: scratch
payload literal lama berada di byte 5.300, sedangkan code successor C0.8 telah
melewati alamat tersebut. Akibatnya bytes nol instruction dan payload dapat
saling menimpa. Scratch literal dipindahkan ke byte `18.000..18.254`, setelah
enam tabel token yang berakhir di byte 17.535. Operation metadata tetap di
`10.000..10.255`, code target tetap di bawah byte 10.000, dan seluruh arena
sekarang disjoint sesuai bound tertulis.

Successor source berukuran 1.479 byte, tetap di bawah batas 1.536 byte, dan
memakai 31 dari 32 operation record. Artifact successor berukuran 1.580 byte.
Gate mengunci predecessor rebuild, dua build identik, parity seluruh spelling
u8, invalid-input, machine format, closed output, intrinsic lama/baru, serta
probe self-source. Prefix aktual self-source adalah
`fn main(){\nbyte_store`; parser sekarang menerima envelope sampai LF dan
berhenti pada keyword `byte_store` baris kedua dengan exit 1, diagnostic exact,
dan nol byte artifact. Karena itu blocker C0.9 diketahui secara konkret.

Artifact canonical C0.8:

```text
b0.seed             52.600 byte
c0.seed            156.692 byte
c0-successor.seed    1.580 byte
```

Identitas canonical C0.8:

```text
b0.seed            e665b4907c3cc177461794edf58eaea848420b29b21d257fdd13befbab908b93
c0.seed            d5b543b45f5ad2cc38ec3fe332e187e6e28d600954f53ca5ec09e67cba9dd537
c0-successor.seed  450fc6f26d371532a17ceb146cfba4c43bffa464db92f4788d22ebdbcd04508b
```

Urutan minimum berikutnya:

1. C0.8 tetap dikunci oleh semua gate C0.7 ditambah function-envelope,
   intrinsic suffix, arena literal disjoint, dan self-source probe (`PASS`);
2. C0.9 menambah statement dispatch bounded untuk construct pertama yang
   terbukti gagal, dimulai dari `byte_store`;
3. jangan menambah general parser, kapasitas, atau claim self-hosting sebelum
   probe berikutnya membuktikan kebutuhan dan reproduksi lintas generasi.

C0.3a sampai C0.8 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED`.

Bukan memperluas R0, bukan menghidupkan kembali LLVM sebagai jalur canonical,
dan bukan mengklaim self-hosting sebelum ada rebuild generasi lanjut.

### Work Unit Selesai: C0.9 Bounded Statement Dispatch

Probe C0.8 membuktikan `byte_store` sebagai construct pertama yang belum
diterima. C0.9 menambahkan satu intrinsic bootstrap
`byte_parse_stmts(source_offset, destination_offset)` dengan grammar body exact:

```text
body       := byte-store{0,3} return-statement NUL
byte-store := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
return-statement := "return" SP decimal-u8 "}" LF
decimal-u8 := digit | digit digit | digit digit digit
```

Tidak ada whitespace opsional, statement keempat, identifier umum, atau
expression tersembunyi. Source offset compile-time dibatasi `<=183`, sehingga
panjang maksimum grammar 72 byte tidak dapat melewati byte-memory 255.
Dispatcher x86_64 berukuran tetap 223 byte, memakai subroutine decimal bersama,
memeriksa setiap nilai `<=255`, dan mengarahkan semua kegagalan ke handler
`runtime: invalid source` yang sama. Prefix code 219 byte diverifikasi identik
dengan reference machine-byte audit sebelum displacement handler dipatch.

Statement `byte_store` dalam grammar ini tidak dapat diamati: setelahnya hanya
ada literal `return`, tanpa `byte_load`, output, atau operasi memory lain.
Successor karena itu menghapus dead store dan menghasilkan artifact return
188-byte yang sama. Gate membuktikan nol, satu, dan tiga store; leading zero;
batas 255; batas maksimal tiga statement; malformed delimiter/keyword/newline;
overflow kedua operand dan return; trailing input; diagnostic exact; serta dua
build identik. Ini adalah subset semantik bounded, bukan codegen `byte_store`
umum pada compiler generasi berikutnya.

Successor C0.9 membaca 96 byte ke byte-memory, memvalidasi function envelope,
lalu menyerahkan body ke dispatcher. Source successor berukuran 1.262 byte dan
memakai 24 dari 32 operation record. Probe terhadap source aktual menerima
tiga statement awal:

```text
fn main(){
byte_store(253,0)
byte_store(254,0)
byte_store(255,0)
```

Probe lalu menolak `input_read` pada baris kelima dengan exit 1, diagnostic
exact, dan nol byte artifact. Blocker C0.10 dengan demikian berasal dari
eksekusi ulang artifact, bukan perkiraan desain.

Artifact canonical C0.9:

```text
b0.seed             52.600 byte
c0.seed            183.983 byte
c0-successor.seed    1.452 byte
```

Identitas canonical C0.9:

```text
b0.seed            e665b4907c3cc177461794edf58eaea848420b29b21d257fdd13befbab908b93
c0.seed            ecaa8175bbbc562d223079c8368ba72a08cb71d868e0cd846ab7964004a19456
c0-successor.seed  6265d731657b436c2b90850b7c05ef93b1373c72ceeac29eb081c86061231208
```

Urutan minimum berikutnya:

1. C0.9 dikunci oleh seluruh gate C0.8 ditambah intrinsic 223-byte, grammar
   dead-store bounded, batas tiga statement, determinism, dan probe baris lima;
2. C0.10 menambah dispatch/semantik minimum untuk `input_read` yang telah
   terbukti menjadi blocker berikutnya;
3. jangan menaikkan source, token, operation, atau output capacity sebelum
   probe berikutnya menunjukkan bound konkret yang terlampaui.

C0.3a sampai C0.9 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai reproducible multi-generation equality tersedia.

### Work Unit Selesai: C0.10 Bounded Input-Read Successor

Probe C0.9 membuktikan `input_read` sebagai construct pertama berikutnya yang
belum diterima. C0.10 memperluas `byte_parse_stmts(source, destination)` tanpa
mengubahnya menjadi parser umum. Grammar runtime exact yang sekarang diterima:

```text
body       := envelope? byte-store{0,3} input-read? return-statement NUL
envelope   := "fn main(){" LF
byte-store := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
input-read := "input_read(32,96)" LF
return-statement := "return" SP decimal-u8 "}" LF
decimal-u8 := digit | digit digit | digit digit digit
```

`input_read` hanya boleh muncul satu kali, setelah seluruh `byte_store`, dan
sebelum `return`. Duplicate input, offset/count atau spelling numerik lain,
store setelah input,
statement keempat, malformed delimiter, overflow u8, dan trailing byte menuju
handler bersama `runtime: invalid source` dengan exit 1. Dispatcher x86_64
berukuran tetap 385 byte. Source offset compile-time dibatasi `<=152` dan
destination `<=253`, sehingga seluruh pembacaan dan tiga byte metadata tetap
berada dalam byte-memory 256 byte.

Metadata yang ditulis adalah nilai return di `destination`, flag no-input di
`destination+1`, dan flag input-present di `destination+2`. Successor memakai
flag itu untuk memilih tepat satu dari dua artifact yang sudah dibuktikan oleh
C0: executable return-only 188 byte atau executable `input_read(32,96)` 377
byte. Kedua output successor byte-for-byte identik dengan output langsung C0,
deterministik, syscall-only, dan memiliki behavior error yang sama. Input valid
menjalankan nilai return; fd 0 tertutup menulis diagnostic exact
`runtime: input_read failed` lalu exit 74.

Dua kapasitas C0 dinaikkan hanya setelah source successor aktual melewati batas
lama. Source input sekarang menerima maksimum 3.072 byte dan menolak byte
3.073 pada lokasi sebenarnya. Arena decoded literal memakai counter 16-bit,
menerima total tepat 1.024 byte, dan menolak byte ke-1.025; batas setiap literal
tetap 255 byte. Successor berukuran 2.449 byte dan membutuhkan 543 byte literal
untuk dua jalur artifact tersebut.

Pertumbuhan emitter C0.10 juga membuktikan dua batas predecessor B0 tidak lagi
cukup. B0.7l menaikkan tabel patch byte-access menjadi 2.560 entry dan arena
output menjadi 262.144 byte. Gate menerima tepat 2.560 patch, menolak patch
ke-2.561, menerima artifact 262.136 byte, dan menolak langkah emisi berikutnya
tanpa output parsial. B0.7l tidak menambah syntax atau semantik B0.

Saat mengintegrasikan arena literal 16-bit, parity test menemukan operand
operasi biasa secara keliru menggabungkan byte tinggi range literal. Akibatnya
`byte_store(2,0)` pada jalur input diturunkan ke alamat `0x401102`, bukan
`0x401002`. Root cause diperbaiki di batas data: loop operation memakai hanya
argumen pertama 8-bit, sedangkan penggabungan low/high 16-bit dilakukan khusus
pada pass relokasi literal. Test direct-vs-successor dan eksekusi bounded
mengunci regresi ini.

Artifact canonical C0.10:

```text
b0.seed             52.600 byte
c0.seed            201.492 byte
c0-successor.seed    1.802 byte
```

Identitas canonical C0.10:

```text
b0.seed            3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            7d553fb4e6896adf93b4f22ae6bf3a622c063e328d0ce779566f76e6cda79ae4
c0-successor.seed  18556ca2015f63fec1a62a1303a8bfb005ebe8e4979f99adffb607f32a411ade
```

Urutan minimum berikutnya:

1. C0.10 tetap dikunci oleh seluruh gate C0.9 ditambah parser 385-byte,
   metadata flags, exact input-read parity/runtime, literal 16-bit, source
   3.072-byte, dan kedua capacity boundary B0.7l (`PASS`);
2. C0.11 menangani construct pertama yang benar-benar terbukti gagal pada
   probe ulang, yaitu `byte_parse_stmts` di baris ketiga successor;
3. jangan menambah parser umum, operation kind, atau kapasitas baru sebelum
   probe berikutnya menunjukkan kebutuhan konkret.

C0.3a sampai C0.10 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai reproducible multi-generation equality tersedia.

### Work Unit Selesai: C0.11 Bounded Parse-Stmts Successor

Probe C0.10 membuktikan `byte_parse_stmts` pada baris ketiga sebagai construct
pertama berikutnya yang belum diterima. C0.11 menambah hanya grammar exact yang
dibutuhkan oleh construct itu:

```text
body        := envelope? byte-store{0,3} input-read? parse-stmts? return-statement NUL
envelope    := "fn main(){" LF
byte-store  := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
input-read  := "input_read(32,96)" LF
parse-stmts := "byte_parse_stmts(32,0)" LF
return-statement := "return" SP decimal-u8 "}" LF
```

`parse-stmts` hanya valid satu kali, tepat setelah input exact dan sebelum
return. Parser tanpa input, parser duplikat, argumen atau spelling numerik yang
berbeda, store setelah input/parser, delimiter malformed, overflow u8, dan
trailing byte semuanya menuju handler bersama `runtime: invalid source` dengan
exit 1. Dispatcher x86_64 sekarang 499 byte. Bagian 385 byte C0.10 tetap
mempertahankan control flow lamanya dan tail 114 byte menangani satu construct
baru. Source offset compile-time dibatasi `<=129` dan destination `<=252` agar
seluruh pembacaan serta empat byte metadata tetap berada dalam byte-memory 256
byte.

Metadata sekarang berisi return value, no-input flag, input-present flag, dan
parser-present flag. Successor memakai flag tersebut untuk memilih tepat satu
dari tiga jalur frozen: artifact return 188 byte, input 377 byte, atau parser
949 byte. Jalur parser successor byte-for-byte identik dengan output langsung
C0.11 pada semua gate yang sama, deterministik, menerima source valid, dan
menolak source invalid dengan diagnostic exact.

Source successor berukuran 3.905 byte dan artifact-nya 3.081 byte. C0.11
menambahkan escape string satu byte `\0` sambil mempertahankan `\x00`, sehingga
machine artifact dapat ditulis lebih ringkas tanpa mengubah byte hasil decode.
Total decoded literal dibatasi 1.536 byte, batas per literal tetap 255 byte,
dan successor memakai tepat 1.492 byte literal. Gate menerima total 1.536 dan
menolak byte ke-1.537.

Kenaikan source dari 3.072 ke 4.096 byte menemukan regresi layout, bukan sekadar
capacity shortage: source byte mulai offset 3.080 menimpa scratch compiler lama
di `3080..3999`. Scratch itu dipindahkan ke `13080..13999`, tetap di bawah arena
source B0 131.072 byte dan disjoint dari source, operation metadata, token
tables, serta literal arena. Gate menerima source tepat 4.096 byte dan menolak
byte ke-4.097 pada lokasi sebenarnya. Source C0 sendiri tetap dapat dibangun
oleh B0 tanpa menaikkan kapasitas predecessor.

Probe ulang menerima envelope, `input_read(32,96)`, dan
`byte_parse_stmts(32,0)`, lalu berhenti pada `byte_store(4,184)` di baris
keempat dengan exit 1, diagnostic exact, dan nol byte artifact. Blocker
berikutnya dengan demikian kembali berasal dari eksekusi artifact nyata.

Artifact canonical C0.11:

```text
b0.seed             52.600 byte
c0.seed            215.029 byte
c0-successor.seed    3.081 byte
```

Identitas canonical C0.11:

```text
b0.seed            3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            1106d8fa33a2d0115603b0e1557b14e2b72460f3a17ab6f7c2373e37773f7666
c0-successor.seed  f957c7ca897bb26765b72061eff2d0850a36fb0fc3278899d73ed240c8cb795e
```

Urutan minimum berikutnya:

1. C0.11 dikunci oleh seluruh gate C0.10 ditambah dispatcher 499-byte,
   metadata empat byte, `\0`, source 4.096-byte, literal 1.536-byte, layout
   scratch disjoint, parser parity/runtime, dan probe baris keempat (`PASS`);
2. work unit berikutnya menangani hanya `byte_store(4,184)` yang telah terbukti
   menjadi blocker, kemudian mengulang parity dan probe;
3. jangan menambah parser umum, operation kind, atau kapasitas predecessor
   sebelum probe atau gate konkret membuktikan kebutuhannya.

C0.3a sampai C0.11 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai reproducible multi-generation equality tersedia.

### Work Unit Selesai: C0.12 Bounded Post-Parser Store

Probe C0.11 membuktikan `byte_store(4,184)` pada baris keempat sebagai
construct pertama berikutnya yang belum diterima. C0.12 melewati tepat satu
statement pascaparser dengan grammar tambahan berikut:

```text
post-parser-store := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
```

Statement ini hanya valid setelah pasangan exact `input_read(32,96)` dan
`byte_parse_stmts(32,0)`, serta hanya satu kali sebelum return. Implementasi
tidak menambah parser kedua. Dispatcher 499 byte memakai kembali body store
generik yang sudah diaudit: keberhasilan parser masuk ke stub tujuh byte pada
NOP island lama, mengatur logical store count menjadi dua, lalu dispatch ulang.
Jika flag parser aktif, cabang existing diarahkan ke body store. Store pertama
menaikkan count menjadi tiga dan store kedua ditolak oleh bound yang sudah ada.
Ordering lama, metadata empat byte, dan seluruh jalur invalid C0.11 tetap
berlaku.

Store tersebut dead pada subset successor ini karena tidak ada pembacaan
memory setelah parser sebelum return. Successor karena itu menghapus store dan
menghasilkan artifact parser 949 byte yang sama dengan bentuk tanpa store.
Gate terpisah membuktikan bentuk direct C0 dapat dikompilasi dan dijalankan,
output successor deterministik serta byte-identik dengan jalur parser-only,
dan store pascaparser kedua gagal dengan exit 1, diagnostic exact, serta nol
byte artifact.

Lookahead store terpanjang membutuhkan 20 byte. Bound compile-time intrinsic
karena itu diperketat dari `source <= 129` menjadi `source <= 109`, sedangkan
`destination <= 252` tetap. Gate menerima pasangan batas `109/252` dan menolak
`110/253`. Dispatcher, arena source 4.096 byte, total literal 1.536 byte,
operation cap, dan kapasitas predecessor tidak berubah.

Payload parser yang ditanam di `successor.nq` diregenerasi dari C0.12 agar
successor tidak diam-diam menjalankan dispatcher C0.11. Perubahan encoding
byte membuat source successor turun dari 3.905 menjadi 3.903 byte; artifact
tetap 3.081 byte. Probe ulang menerima `byte_store(4,184)` lalu berhenti pada
`byte_store(5,60)` di baris kelima. Ini adalah blocker berikutnya yang terukur,
bukan alasan untuk mengklaim parser umum.

Artifact canonical C0.12:

```text
b0.seed             52.600 byte
c0.seed            215.029 byte
c0-successor.seed    3.081 byte
```

Identitas canonical C0.12:

```text
b0.seed            3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            c18e5afae0c05ed5c1476193c72fe8c02c282aa918ff892e1dcf2fb3e7a77dc9
c0-successor.seed  33cd17bfff567eacdadd8dbca9ad351c913714d78cb999bb18b4bb94ec11b405
```

Urutan minimum berikutnya:

1. C0.12 dikunci oleh seluruh gate C0.11 ditambah reuse store body, exact
   `109/110` dan `252/253` bounds, parity store-dead, duplicate rejection,
   payload successor C0.12, dan probe baris kelima (`PASS`);
2. work unit berikutnya menangani hanya `byte_store(5,60)` yang telah terbukti
   menjadi blocker, kemudian mengulang parity dan probe;
3. jangan menambah parser umum, operation kind, metadata, atau kapasitas
   predecessor sebelum probe atau gate konkret membuktikan kebutuhannya.

C0.3a sampai C0.12 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai reproducible multi-generation equality tersedia.

### Work Unit Selesai: C0.13 Bounded Second Post-Parser Store

Probe C0.12 membuktikan `byte_store(5,60)` pada baris kelima sebagai
construct pertama berikutnya yang belum diterima. C0.13 memperluas jumlah
pengulangan grammar `post-parser-store` yang sama dari satu menjadi tepat
maksimal dua setelah pasangan exact `input_read(32,96)` dan
`byte_parse_stmts(32,0)`.

Dispatcher tetap 499 byte dan tetap memakai body store generik. Stub sukses
parser mengatur logical store count menjadi satu, bukan dua; pemeriksaan count
yang sudah ada kemudian menerima store pascaparser pertama dan kedua, tetapi
menolak yang ketiga. Implementasi hanya mengubah satu immediate machine code
`mov bl,2` menjadi `mov bl,1`. Tidak ada operation kind, metadata byte,
parser kedua, kapasitas operation, atau capacity bridge predecessor baru.

Kedua store tetap dead pada subset successor karena tidak ada pembacaan memory
setelah parser sebelum return. Bentuk tanpa store, satu store, dan dua store
karena itu menghasilkan artifact parser 949 byte yang sama. Gate menjalankan
direct C0 serta dua build successor independen untuk setiap bentuk, lalu
membuktikan output byte-for-byte identik. Store pascaparser ketiga gagal dengan
exit 1, diagnostic exact, dan nol byte artifact.

Satu store terpanjang memerlukan 20 byte lookahead tambahan. Bound source
intrinsic diperketat dari `source <= 109` menjadi `source <= 89`, sedangkan
`destination <= 252` tetap. Gate menerima `89/252` dan menolak `90/253` pada
lokasi diagnostic yang sebenarnya. Fixture fungsi lengkap dengan dua store
memakai tepat 96 byte, sama dengan fixed input window successor.

Payload parser dalam `successor.nq` diregenerasi dari C0.13. Source successor
tetap 3.903 byte dan artifact tetap 3.081 byte. Probe ulang menerima
`byte_store(4,184)` dan `byte_store(5,60)`, lalu berhenti pada
`byte_store(9,15)` di baris keenam. Ini adalah blocker berikutnya yang terukur;
C0.13 tetap tidak mengklaim parser umum.

Artifact canonical C0.13:

```text
b0.seed             52.600 byte
c0.seed            215.029 byte
c0-successor.seed    3.081 byte
```

Identitas canonical C0.13:

```text
b0.seed            3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            20539eb5da2d715df4c801b5646a5f6be49e6a6c82dce571df4a4fdb36453b52
c0-successor.seed  a2ee11260ac1411cf85030c35b109a7c61ec136561a98ae38d55ec9f5586a025
```

Urutan minimum berikutnya:

1. C0.13 dikunci oleh seluruh gate C0.12 ditambah exact `89/90` source bound,
   bentuk dua-store berukuran tepat 96 byte, parity zero/one/two dead store,
   third-store rejection, payload successor C0.13, dan probe baris keenam
   (`PASS`);
2. work unit berikutnya menangani hanya `byte_store(9,15)` yang telah terbukti
   menjadi blocker, kemudian mengulang parity dan probe;
3. jangan menambah parser umum, operation kind, metadata, atau kapasitas
   predecessor sebelum probe atau gate konkret membuktikan kebutuhannya.

C0.3a sampai C0.13 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai reproducible multi-generation equality tersedia.

### Work Unit Selesai: C0.14 Bounded Return-Tail Split

Probe C0.13 berhenti pada `byte_store(9,15)`, tetapi pengukuran ulang terhadap
96 byte input yang benar membuktikan bahwa memperbesar counter store saja
tidak dapat mencapainya: pembacaan successor berakhir di tengah baris keenam.
Memperluas grammar menjadi 128 byte juga akan memerlukan jalur kompatibilitas
kedua hanya untuk menerima state yang sebenarnya konstan.

Empat store awal successor ternyata hanya membentuk tail executable berikut:

```text
<return-u8> 00 00 00 b8 3c 00 00 00 0f 05
```

Hanya byte pertama yang dinamis. C0.14 menghapus keempat store setup dan, pada
jalur return maupun input, mengganti `output_write(0,11)` dengan
`output_write(0,1)` diikuti literal sepuluh byte yang tetap. Jalur parser tetap
menulis artifact lengkapnya seperti sebelumnya. Tidak ada grammar baru,
metadata baru, alokasi baru, atau perubahan semantik compiler C0.

Gate membandingkan seluruh nilai return yang sudah dicakup, artifact input,
dan artifact parser terhadap output direct C0. Semuanya tetap byte-for-byte
identik. Dua build successor independen juga identik. Probe self-source tetap
gagal bersih dengan exit 1, diagnostic exact, dan nol byte artifact, tetapi
sekarang construct pertama yang belum diterima adalah `while byte_load(1)` di
baris keempat. Dengan demikian blocker store ketiga diselesaikan melalui
penghapusan state yang tidak diperlukan, bukan perluasan parser spekulatif.

Artifact canonical C0.14:

```text
b0.seed             52.600 byte
c0.seed            215.029 byte
c0-successor.seed    3.165 byte
```

Identitas canonical C0.14:

```text
b0.seed            3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            20539eb5da2d715df4c801b5646a5f6be49e6a6c82dce571df4a4fdb36453b52
c0-successor.seed  ff37bdfef5782141a1ea37467756555086383414f2f6004d37060e93beb9c7d3
```

Urutan minimum berikutnya:

1. C0.14 dikunci oleh seluruh gate C0.13 ditambah deterministic successor,
   parity return/input/parser, tail target byte-exact, hash canonical baru,
   dan probe baris keempat (`PASS`);
2. work unit berikutnya menangani hanya `while byte_load(1)` yang telah
   terbukti menjadi blocker;
3. jangan menambah loop umum, parser umum, metadata, atau kapasitas predecessor
   sebelum probe atau gate konkret membuktikan kebutuhannya.

C0.3a sampai C0.14 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai reproducible multi-generation equality tersedia.

### Work Unit Selesai: C0.15 Exact Terminating Clear Loop

Probe C0.14 berhenti pada `while byte_load(1)` di baris keempat. C0.15 tidak
menambahkan grammar loop umum. Default branch dispatcher kini menuju matcher
80 byte untuk satu source sequence lengkap:

```text
while byte_load(1) {
byte_store(1,0)
}
```

Sequence 39 byte tersebut selalu terminating: condition hanya bernilai nol
atau satu, body mengosongkan byte condition pada iterasi pertama, dan tidak
ada output sebelum final return. Successor karena itu boleh menghilangkannya
tanpa mengubah artifact target. Matcher memeriksa byte pertama, menyimpan
`RSI` dan `RDI`, membandingkan seluruh sequence dengan `repe cmpsb`, memulihkan
register pada jalur match maupun mismatch, lalu kembali ke dispatch setelah
match atau menuju handler invalid bersama setelah mismatch. Stack seimbang dan
tidak ada syscall, call, metadata baru, maupun fallthrough ke payload pattern.

Dispatcher bertambah dari 499 menjadi 579 byte. Successful-return jump di
offset 385 melewati tail baru; default dispatch di offset 83 kini menuju
matcher loop. Karena worst-case grammar bertambah 39 byte, source bound
`byte_parse_stmts` diperketat dari `<=89` menjadi `<=50`; destination tetap
`<=252`. Gate menerima `50/252`, menolak `51/253`, menjalankan loop valid
setelah parser, dan menolak condition salah, body salah, serta brace penutup
yang hilang dengan diagnostic exact dan nol artifact.

Payload parser canonical bertambah dari 949 menjadi 1.029 byte. Encoding lima
literal membuat source successor 4.079 byte, masih di bawah source cap C0
4.096 byte, tetapi total decoded literal melampaui 1.536 byte. C0.15 menaikkan
hanya total literal cap ke 2.048 byte; batas 255 byte per literal tetap. Gate
exact menerima 2.048 byte dan menolak byte 2.049.

Source `compiler.nq` bertambah menjadi 136.042 byte sehingga B0.7l menolaknya
pada batas 131.072 byte. B0.7m menaikkan hanya `INPUT_CAP` predecessor menjadi
196.608 byte. Gate exact/overflow, rebuild Stage 0, parity reference assembly,
hash, serta seluruh regression B0 membuktikan capacity bridge ini tanpa
perubahan grammar atau codegen B0.

Probe self-source sekarang menerima prefix sampai matcher loop dan gagal pada
`write` di body loop baris kelima. Ia tetap exit 1, menulis diagnostic invalid
source yang sama, dan menghasilkan nol byte artifact. Ini menetapkan `write`
sebagai blocker berikutnya yang terukur.

Artifact canonical C0.15:

```text
b0.seed             52.600 byte
c0.seed            224.279 byte
c0-successor.seed    3.371 byte
```

Identitas canonical C0.15:

```text
b0.seed            3f54d9d1c0b9a09374444a19c15aad93700739951f65126f13024071d0004bba
c0.seed            da7f1647305da092a282937244786653aa845829db79d6b3d76dd7b4c60ae50e
c0-successor.seed  1aa777595cbeab0cb7ee7b1827f35921786f7a972ee67257bfd3c08781a97f95
```

Urutan minimum berikutnya:

1. C0.15 dikunci oleh seluruh gate C0.14 ditambah exact clear-loop execution,
   malformed-loop rejection, source bound `50/51`, literal cap `2048/2049`,
   B0 input cap `196608/196609`, deterministic parity, dan hash baru (`PASS`);
2. work unit berikutnya menangani hanya `write` di body loop yang dibuktikan
   oleh probe, termasuk seluruh payload literal yang memang diperlukan;
3. jangan menambah loop umum, parser umum, metadata, atau backend eksternal
   sebelum gate konkret membuktikan kebutuhan tersebut.

C0.3a sampai C0.15 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai reproducible multi-generation equality tersedia.

### Work Unit Selesai: C0.16 Exact Return-Emitter Recognition

Probe C0.15 berhenti pada `write` di body loop return-emitter pertama. C0.16
tidak menambahkan grammar `write`, string, atau loop umum. Dispatcher mengenali
seluruh source sequence canonical baris 4--9 sebagai satu construct exact:

```text
while byte_load(1) {
write(<canonical return ELF prefix>)
byte_store(1,0)
output_write(0,1)
write(<canonical return ELF tail>)
}
```

Sequence 477 byte itu dibandingkan byte-for-byte. Matcher mempertahankan
register parser, melakukan refill source bounded sampai 512 byte, memakai
`repe cmpsb`, dan hanya memajukan source setelah full match. Mismatch satu byte,
short read, atau read failure menuju handler invalid bersama dengan exit 1,
diagnostic `runtime: invalid source`, dan nol byte artifact. Ukuran dispatcher
lokal bertambah dari 579 menjadi 1.167 byte. General literal dispatch dan loop
lain tetap invalid.

Metadata parser bertambah dari empat menjadi lima byte:

```text
return-value | no-input | input-present | parser-present | emitter-present
```

Fixture canonical menghasilkan `00 00 01 01 01`; payload dengan byte ELF
pertama yang diubah ditolak. Penambahan metadata memperketat destination bound
dari `<=252` menjadi `<=251`, dengan gate exact `251/252`. Source bound public
intrinsic tetap `<=50`, sedangkan parser-bearing artifact memperoleh private
BSS 1 KiB untuk refill. Artifact parser direct dan successor byte-identical
sebesar 1.625 byte.

Pertumbuhan RX parser membuka overlap layout nyata: artifact successor 4.655
byte sudah melewati page pertama, sedangkan RW lama berada di `0x401000`.
C0.16 memindahkan hanya parser-bearing RW load ke `0x402000` dan menyesuaikan
seluruh absolute serta RIP-relative address yang terkait. Artifact runtime
biasa tetap memakai BSS 256 byte di `0x401000`. Gate `readelf` membuktikan RX/RW
tidak overlap, tidak ada RWX load, dan GNU stack tetap non-executable.

Source successor bertambah menjadi 5.088 byte. C0 menaikkan source input secara
bounded dari 4.096 menjadi 8.192 byte serta total decoded literal dari 2.048
menjadi 3.072 byte; batas 255 byte per literal tetap. Gate exact menerima
8.192/3.072 byte dan menolak 8.193/3.073. Kenaikan source menemukan overlap
lain: bytes source di atas offset 4.096 dapat tertinggal pada field sparse ELF.
Jalur sukses sekarang membersihkan hanya tail source `[4096,count)` sebelum
emission; jalur gagal tetap tidak mengeluarkan artifact.

Source `compiler.nq` kini 176.953 byte dan artifact C0 298.359 byte, melampaui
output serta byte-access cap B0.7m. B0.7n menaikkan hanya `OUTPUT_CAP` menjadi
393.216 byte dan `BYTE_ACCESS_CAP` menjadi 3.072 entry. Gate menerima 393.212
byte output dan tepat 3.072 patch, lalu menolak langkah emisi 18 byte berikutnya
serta patch ke-3.073 tanpa artifact parsial. Stage 0 reconstruction, NASM audit
parity, determinism, hash, dan seluruh regression B0 tetap hijau; grammar dan
semantik B0 tidak berubah.

Probe self-source sekarang mengonsumsi seluruh return-emitter pertama dan
berhenti pada construct berikutnya, `while byte_load(3)` di baris 10. Probe
tetap exit 1, diagnostic exact, dan nol artifact. MCP juga memakai riwayat
blocker canonical, bukan lagi mencari kemunculan `write` pertama yang sudah
diterima.

Artifact canonical C0.16:

```text
b0.seed             52.600 byte
c0.seed            298.359 byte
c0-successor.seed    4.655 byte
parser payload       1.625 byte
```

Identitas canonical C0.16:

```text
b0.seed            582068c5f2b32a769412727e08d7ad7ff5dd6fb57d276bb6f675a6496c380b75
c0.seed            5d7162abb44427216620b265e15429de0cf1b866b529d5ec89400d816845da77
c0-successor.seed  0be664dd95b57fce05757681cd742c6426ca0f53e9cd3fc18dd721849982280a
parser payload     4d8950c402b1ca51c489e56f82a82230959416c0749dcb248812f94e91e84d7b
```

Urutan minimum berikutnya:

1. C0.16 dikunci oleh seluruh gate C0.15 ditambah exact return-emitter match,
   altered-payload rejection, metadata lima byte, destination `251/252`, source
   `8192/8193`, literal `3072/3073`, layout `0x402000`, source-tail clearing,
   B0.7n capacity gates, deterministic parity, dan hash baru (`PASS`);
2. work unit berikutnya menangani hanya `while byte_load(3)` di baris 10 yang
   dibuktikan probe;
3. jangan menambah loop umum, parser umum, Full Compiler, atau dependency host
   sebelum gate konkret membuktikan kebutuhan tersebut.

C0.3a sampai C0.16 sekarang `PASS`. Full Compiler dan self-hosting tetap
`NOT_IMPLEMENTED` sampai reproducible multi-generation equality tersedia.

---

# 0. OTORITAS DAN URUTAN SUMBER KEBENARAN

Saat melakukan pengembangan, gunakan urutan berikut sebagai sumber kebenaran:

1. **Perilaku yang telah dibuktikan oleh test yang valid.**
2. **Spesifikasi arsitektur NolQu-L yang sudah ditetapkan.**
3. **Implementasi codebase yang memang disengaja dan terdokumentasi.**
4. **Kompatibilitas source/program NolQu-L yang sudah bekerja.**
5. **Keputusan desain baru yang dibuat pada sesi ini.**

Jika terjadi konflik antara implementasi lama dan spesifikasi:

- jangan langsung mengubah salah satunya,
- identifikasi penyebab konflik,
- tentukan mana yang merupakan bug,
- mana yang merupakan desain lama,
- dan mana yang membutuhkan keputusan kompatibilitas.

Semua perubahan kompatibilitas harus dijelaskan.

---

# 1. NINE PILLARS OF NOLQU-L

Semua keputusan desain, implementasi, refactor, optimization, safety rule, syntax, CLI, runtime, dan bootstrap harus tunduk pada Nine Pillars berikut.

## Pillar 1 — Kesederhanaan

NolQu-L harus memungkinkan programmer mengekspresikan program dengan cara sesederhana mungkin tanpa mengorbankan fungsi, kontrol, performa, maupun kejelasan.

- Masalah sederhana harus dapat ditulis dengan kode sederhana.
- Hindari boilerplate, sintaks, dan aturan tambahan yang tidak memberikan manfaat nyata.
- Kompleksitas yang memang berasal dari masalah tetap boleh diekspresikan secara eksplisit.
- Jangan memindahkan kerumitan implementasi compiler menjadi beban pengguna hanya demi mempermudah compiler.

Kesederhanaan berarti mengurangi *accidental complexity*, bukan mengurangi kemampuan bahasa atau menyembunyikan konsekuensi mesin. Untuk kode internal compiler, terapkan semangat yang sama secara proporsional: pilih solusi yang paling mudah dipahami dan diverifikasi selama tetap memenuhi kontrak teknis.

## Pillar 2 — Keterbacaan

Kode NolQu-L harus mudah dibaca dan dipahami manusia. Tujuan, struktur, dan alur kode harus terlihat jelas tanpa memaksa pembaca menebak perilaku tersembunyi atau aturan yang tidak intuitif.

- Utamakan kejelasan dibanding sintaks yang terlalu pendek atau padat.
- Nama dan konstruksi bahasa harus konsisten serta menjelaskan maksudnya.
- Fitur tidak boleh membuat operasi lazim lebih sulit diikuti tanpa manfaat yang sepadan.
- Kode harus tetap mudah dipahami penulisnya sendiri maupun programmer lain di masa depan.

Keterbacaan berlaku terutama untuk **kode yang ditulis pengguna NolQu-L**. Untuk kode internal compiler, keterbacaan tetap merupakan praktik rekayasa yang penting, tetapi jangan mengaburkan tujuan utama pilar ini sebagai filosofi desain bahasa.

## Pillar 3 — Dekat dengan Mesin

NolQu-L harus tetap transparan terhadap perilaku mesin.

Jangan menyembunyikan biaya:

- allocation,
- deallocation,
- syscall,
- memory copy,
- bounds check,
- reference counting jika suatu saat digunakan,
- atomic operation,
- synchronization,
- stack allocation,
- heap allocation,
- alignment,
- ABI conversion,
- runtime safety check,
- atau operasi mesin lainnya.

Programmer harus mempunyai cara yang masuk akal untuk memprediksi:

- kapan memory dialokasikan,
- di mana memory berada,
- kapan resource dilepas,
- operasi apa yang berpotensi mahal,
- dan kapan compiler memasukkan runtime check.

## Pillar 4 — Kompleks di Dalam, Mudah di Luar

Compiler boleh melakukan analisis internal yang kompleks.

Namun source language dan user-facing interface tidak boleh dipaksa menjadi rumit hanya karena implementasinya sulit.

Sebisa mungkin:

**compiler menanggung kompleksitas sehingga programmer tidak perlu melakukannya.**

Tetapi compiler juga tidak boleh menyembunyikan biaya mesin.

## Pillar 5 — NolQu-L Safety

Memory safety dan resource safety adalah bagian dari desain bahasa.

Safety bukan plugin tambahan.

Safety harus berintegrasi dengan:

- type system,
- semantic analysis,
- ownership,
- resource lifetime,
- move semantics,
- borrow checking,
- runtime checks,
- FFI,
- ABI,
- concurrency,
- unsafe boundary,
- dan diagnostic.

## Pillar 6 — Error Handling yang Jelas

Setiap error harus memiliki:

- kode diagnostic,
- lokasi,
- penyebab,
- penjelasan,
- dan jika memungkinkan saran konkret.

Tidak boleh ada:

- silent failure,
- generic "something went wrong",
- crash tanpa konteks,
- assertion compiler pada malformed source biasa,
- atau error backend mentah yang seharusnya dapat diterjemahkan compiler.

## Pillar 7 — Test Sebelum Merge

Tidak ada perubahan yang dianggap selesai tanpa pengujian sesuai dampaknya. Test harus membuktikan perilaku baru, penolakan input yang tidak valid, dan ketiadaan regresi **yang tidak disengaja**.

Breaking change yang disetujui menurut Pillar 8 bukan otomatis regresi. Namun perubahan tersebut tetap memerlukan bukti bahwa perilaku baru sesuai spesifikasi, kerusakan sampingan tidak terjadi, dan jalur migrasi berfungsi jika tersedia. Jika regresi tidak disengaja ditemukan, hentikan perluasan pekerjaan yang terdampak sampai regresi ditangani.

## Pillar 8 — Stabilitas Tanpa Menghambat Evolusi

Perubahan harus sebisa mungkin menjaga kompatibilitas dan tidak merusak kode yang sudah bekerja. Namun **backward compatibility bukan tujuan absolut**. NolQu-L tidak boleh mempertahankan keputusan desain yang buruk hanya demi kompatibilitas.

Breaking change diperbolehkan apabila peningkatannya berarti terhadap keamanan, kesederhanaan, keterbacaan, performa, konsistensi semantik, kemampuan analisis compiler, maintainability, atau kualitas arsitektur jangka panjang.

Sebelum disetujui, perubahan perlu mencatat:

- masalah nyata pada desain lama dan bukti atau alasan teknisnya;
- alternatif yang dipertimbangkan dan alasan solusi kompatibel tidak memadai;
- manfaat yang diharapkan dan cara memverifikasinya;
- dampak terhadap source, behavior, ABI/FFI, tooling, library, serta bootstrap jika relevan;
- biaya migrasi, risiko, dan dokumentasi perubahan;
- jalur migrasi yang masuk akal apabila memungkinkan;
- rencana test, rollout, dan rollback yang proporsional.

**Deprecation dan migration:** Fitur stabil sebaiknya melewati periode deprecation jika aman dan wajar. Diagnostic, migrator, compatibility shim sementara, atau dokumentasi pengganti dapat digunakan. Namun pengecualian diperbolehkan untuk alasan keamanan, ambiguitas, dan kompleksitas yang tidak sebanding; alasan dan dampaknya harus dinyatakan eksplisit.

**Compatibility debt:** Jangan mempertahankan jalur legacy selamanya ketika biaya maintenance, pengujian, dan kerumitan compiler melebihi manfaat kompatibilitas. Compatibility shim harus memiliki tujuan, pemilik keputusan, dan kondisi evaluasi/penghapusan yang jelas apabila relevan.

**Breaking change terkendali:** Kelompokkan perubahan ke batas versi atau milestone yang jelas sejauh memungkinkan; jangan diam-diam mengubah arti kode lama. Hindari rewrite dan perubahan kosmetik yang tidak menyelesaikan masalah nyata.

Prinsip: **Pertahankan yang baik. Perbaiki yang buruk. Ganti yang menghambat masa depan.**

## Pillar 9 — Optimasi Berdasarkan Dampak

Prioritaskan optimasi yang memberi manfaat nyata bagi waktu kompilasi, performa runtime, penggunaan memori, ukuran binary, kualitas kode, atau arsitektur. Klaim performa perlu didukung pengukuran yang relevan; jika belum dapat diukur, tandai sebagai hipotesis.

Pertimbangkan biaya kompleksitas, maintainability, portabilitas, serta efek samping pada metrik lain. Optimasi mikro yang belum terbukti tidak wajib dilakukan. Jika optimasi membutuhkan breaking change, terapkan pertimbangan dan pembuktian Pillar 8; **lebih cepat** saja tidak otomatis membenarkan biaya migrasi.

---

# 2. ATURAN FUNDAMENTAL BOOTSTRAP NOLQU-L

Bootstrap NolQu-L **tidak dimulai dari compiler tingkat tinggi sebagai akar konseptualnya**.

Rantai canonical NolQu-L adalah:

```text
Machine-Level Foundation
        ↓
Stage 0
        ↓
NolQu-L Bootstrap Compiler
        ↓
NolQu-L Core Compiler
        ↓
Full NolQu-L Compiler
        ↓
Self-Hosting nqlc
        ↓
Verified nqlc
```

Setiap tahap harus dapat menjelaskan bagaimana tahap berikutnya dibangun.

Tidak boleh ada bagian bootstrap yang hanya mempunyai jawaban:

> "Compiler ini ada karena sebelumnya sudah ada compiler."

Rantai kepercayaannya harus dapat ditelusuri.

---

# 3. MACHINE-LEVEL FOUNDATION

Machine-Level Foundation adalah akar bootstrap NolQu-L.

Evaluasi secara eksplisit bentuk foundation yang digunakan codebase saat ini.

Bedakan dengan jelas:

```text
Machine Code
Assembly Source
Object File
Executable Binary
Compiler Source
Compiler Binary
Bootstrap Tool
Host Toolchain
```

Jangan menyebut semuanya sebagai "machine code".

## Machine code

Machine code adalah instruction bytes yang secara langsung dipahami target CPU.

Contoh konseptual:

```text
bytes
↓
CPU instruction decoding
↓
machine execution
```

Jika bootstrap menggunakan assembly sebagai representasi manusia untuk menghasilkan instruction bytes, dokumentasikan bahwa:

```text
Assembly Source
↓ assembler
Object / Machine Code
```

Assembly source **bukan machine code**, walaupun hubungan keduanya dekat.

Jika assembler eksternal diperlukan pada tahap awal, catat sebagai **bootstrap dependency**.

Tujuan jangka panjangnya bukan berpura-pura tidak mempunyai dependency, tetapi membuat dependency bootstrap:

- kecil,
- jelas,
- terukur,
- dapat diganti,
- dan dapat diverifikasi.

Machine-Level Foundation harus menjelaskan setidaknya:

- target ISA,
- executable/object format,
- calling convention minimum,
- register assumptions,
- stack convention,
- memory model minimum,
- entry point,
- system interaction minimum,
- dan bagaimana Stage 0 dihasilkan.

Jika target awal hanya satu arsitektur, jangan memaksakan multi-target terlalu dini.

Pilih satu target bootstrap yang jelas terlebih dahulu.

---

# 4. STAGE 0

Stage 0 harus **lebih kecil dan lebih sederhana daripada compiler yang dibangunnya**.

Stage 0 bukan Full NolQu-L.

Stage 0 tidak harus mempunyai:

- seluruh syntax,
- generics,
- borrow checker penuh,
- optimizer kompleks,
- standard library besar,
- seluruh safety mode,
- atau seluruh fitur bahasa.

Stage 0 hanya perlu mempunyai kemampuan minimum untuk menghasilkan compiler generasi berikutnya.

Kemampuan Stage 0 minimal dievaluasi terhadap:

```text
Stage 0
├── basic instruction emission
├── memory operations
├── control flow
├── symbol handling
└── minimal code generation
```

Bila implementasi membutuhkan kemampuan tambahan, tambahkan hanya bila memang diperlukan.

Untuk Stage 0, dokumentasikan:

- input yang diterima,
- output yang dihasilkan,
- format program,
- instruction representation,
- symbol resolution,
- relocation jika digunakan,
- control-flow representation,
- memory operations,
- entry point,
- error behavior,
- dependency eksternal,
- dan proses build.

Jangan menambahkan abstraksi besar ke Stage 0 hanya untuk membuat implementasi terlihat modern.

Stage 0 harus dapat diaudit.

---

# 5. NOLQU-L BOOTSTRAP COMPILER

Stage 0 kemudian digunakan untuk membangun compiler awal yang memahami **NolQu-L Core**.

Minimal NolQu-L Core harus dievaluasi terhadap kemampuan:

```text
NolQu-L Core
├── variables
├── integer types
├── functions
├── basic control flow
├── basic memory operations
└── basic code generation
```

Tambahkan fitur bootstrap lain hanya jika diperlukan untuk menulis generasi compiler berikutnya.

Setiap fitur Core harus mempunyai:

- grammar,
- semantic rule,
- type rule jika relevan,
- IR representation jika IR sudah tersedia,
- code generation,
- diagnostic,
- dan test.

Jangan membuat syntax bootstrap yang nantinya mustahil dimigrasikan ke Full NolQu-L tanpa alasan kuat.

---

# 6. NOLQU-L CORE COMPILER

Setelah bootstrap compiler cukup kuat, arsitektur compiler harus berkembang menuju pipeline yang jelas:

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
AST
  ↓
Semantic Analysis
  ↓
Type System
  ↓
NolQu-L Safety Analysis
  ↓
IR
  ↓
Optimizer
  ↓
Code Generation
  ↓
Object / Machine Code
  ↓
Link
  ↓
Executable
```

Jika implementasi saat ini berbeda, jangan otomatis mengubahnya.

Evaluasi dahulu apakah boundary yang ada:

- jelas,
- testable,
- maintainable,
- dan sesuai kebutuhan bootstrap.

Setiap tahap harus mempunyai tanggung jawab yang jelas.

---

# 7. LEXER

Lexer hanya bertanggung jawab pada lexical analysis.

Evaluasi:

- token representation,
- keyword handling,
- identifier,
- integer literal,
- string literal jika ada,
- comments,
- operator,
- punctuation,
- whitespace,
- newline handling,
- source location,
- malformed token,
- invalid character,
- integer overflow saat lexing jika relevan.

Lexer tidak boleh menjadi tempat semantic analysis.

Lexer harus selalu membuat progress.

Malformed input tidak boleh menyebabkan infinite loop.

Setiap iteration harus:

- consume input,
- menghasilkan token,
- atau menghasilkan diagnostic dan melakukan recovery/termination yang terdefinisi.

---

# 8. PARSER

Parser harus mempunyai boundary yang jelas terhadap lexer.

Evaluasi:

- grammar,
- precedence,
- associativity,
- declarations,
- expressions,
- statements,
- blocks,
- functions,
- types,
- control flow,
- recovery strategy.

Malformed syntax tidak boleh menyebabkan:

- recursion tanpa batas,
- token pointer tidak bergerak,
- panic internal,
- infinite diagnostic loop,
- atau compiler hang.

Jika parser melakukan recovery, recovery harus menjamin progress.

---

# 9. AST

AST harus merepresentasikan struktur source secara cukup jelas tanpa memasukkan detail backend secara prematur.

Evaluasi apakah AST:

- terlalu dekat dengan token stream,
- terlalu dekat dengan machine instruction,
- menyimpan redundant state,
- atau mencampurkan semantic state yang seharusnya berada pada tahap lain.

Pastikan source location tetap tersedia untuk diagnostic setelah parsing.

---

# 10. SEMANTIC ANALYSIS

Semantic analysis harus menangani hal-hal seperti:

- scope,
- declaration,
- duplicate symbol,
- unresolved symbol,
- function lookup,
- variable lookup,
- visibility jika sudah ada,
- module relation jika sudah ada,
- control-flow validity,
- valid return,
- invalid break/continue,
- assignment validity.

Semantic errors harus berhenti sebelum codegen apabila program memang tidak valid.

Backend tidak boleh dipaksa menjadi semantic validator utama.

---

# 11. TYPE SYSTEM

Evaluasi type system secara menyeluruh.

Minimal bedakan:

- type identity,
- representation,
- conversion,
- coercion,
- cast,
- assignment compatibility,
- function parameter,
- return type.

Jika fitur belum ada, jangan langsung menambahkan type system sangat kompleks.

Mulai dari kebutuhan fundamental.

Namun arsitekturnya harus memungkinkan berkembang menuju program kompleks.

Type error harus mempunyai diagnostic yang menunjukkan:

```text
expected type
actual type
location
reason
possible fix
```

---

# 12. NOLQU IR

IR adalah boundary utama antara frontend dan backend apabila architecture NolQu saat ini memang menggunakannya.

IR harus cukup:

- sederhana,
- explicit,
- analyzable,
- deterministic,
- dan mudah di-debug.

Jangan membangun IR yang terlalu abstrak sehingga hubungan dengan mesin hilang.

Tetapi jangan pula membuat frontend langsung tergantung pada instruction set CPU jika hal tersebut membuat compiler sulit dikembangkan.

Evaluasi kebutuhan:

- values,
- constants,
- basic blocks,
- branches,
- calls,
- returns,
- load,
- store,
- arithmetic,
- comparisons,
- memory operation,
- type information minimum,
- source mapping bila diperlukan.

Jika control-flow graph dibutuhkan, gunakan representasi eksplisit.

Verifikasi IR sebelum codegen.

Invalid IR yang dibuat compiler merupakan **compiler bug**, bukan user error.

---

# 13. CODE GENERATION

Backend harus mempunyai contract yang jelas dengan IR.

Evaluasi:

- instruction selection,
- register usage,
- stack layout,
- calling convention,
- alignment,
- function prologue,
- function epilogue,
- return convention,
- parameter passing,
- local variables,
- global symbols,
- relocation,
- object output,
- executable output.

Jangan menghasilkan code machine yang perilakunya bergantung pada state compiler yang tidak terdokumentasi.

Backend harus deterministic untuk input dan konfigurasi yang sama sejauh memungkinkan.

---

# 14. OBJECT FORMAT, LINKING, DAN EXECUTABLE

Jangan memperlakukan "machine code" dan "executable" sebagai hal yang sama.

Dokumentasikan pipeline nyata:

```text
NolQu Source
↓
Compiler
↓
IR
↓
Target Instructions
↓
Machine Code / Object
↓
Linker
↓
Executable
```

Jika compiler menghasilkan executable secara langsung:

jelaskan:

- header,
- sections,
- symbols,
- entry point,
- relocation behavior,
- target format.

Jika menggunakan system linker:

catat dependency secara eksplisit.

Failure dari assembler atau linker harus diterjemahkan menjadi diagnostic toolchain yang jelas apabila memungkinkan.

---

# 15. FULL NOLQU-L COMPILER

Full compiler secara bertahap harus memiliki komponen utama:

```text
Lexer
Parser
AST
Semantic Analysis
Type System
NolQu-L Safety
IR
Optimizer
Code Generator
Runtime
Standard Library
Tooling
```

Jangan menganggap compiler "full" hanya karena dapat menghasilkan executable sederhana.

Definisikan maturity criteria yang terukur.

---

# 16. SELF-HOSTING

Target self-hosting:

```text
Existing nqlc
      ↓
compile
      ↓
NolQu-L compiler source
      ↓
New nqlc
```

Compiler source NolQu-L harus dapat dikompilasi oleh compiler generasi sebelumnya.

Setelah tercapai, lakukan rebuild:

```text
Compiler A
   ↓
build compiler source
   ↓
Compiler B
   ↓
rebuild same compiler source
   ↓
Compiler C
```

Kemudian lakukan verification.

---

# 17. BOOTSTRAP VERIFICATION

Self-hosting saja **tidak cukup**.

Lakukan bootstrap verification.

Minimal bandingkan:

```text
Compiler B
vs
Compiler C
```

Jika output seharusnya reproducible:

```text
Compiler B == Compiler C
```

Jika binary identity belum dapat dicapai karena metadata non-deterministik:

- identifikasi setiap sumber nondeterminisme,
- jangan mengabaikannya,
- bedakan semantic equivalence dari bit-for-bit reproducibility.

Periksa kemungkinan sumber nondeterminisme seperti:

- timestamp,
- temporary path,
- iteration hash order,
- random seed,
- symbol ordering,
- build ID,
- filesystem ordering.

Bootstrap validation harus mempunyai hasil yang dapat direproduksi.

---

# 18. TRACEABILITY BOOTSTRAP

Setiap tahap harus mempunyai hubungan eksplisit terhadap tahap sebelumnya.

Untuk setiap stage catat:

- source,
- input compiler/tool,
- output artifact,
- command build,
- dependency,
- target,
- hash jika infrastructure mendukung,
- test,
- verification method.

Idealnya repository mempunyai dokumentasi atau manifest yang memungkinkan seseorang mengikuti:

```text
Machine Foundation
→ Stage 0
→ Bootstrap Compiler
→ Core Compiler
→ Full Compiler
→ Self-hosting
→ Verified Compiler
```

tanpa menebak langkah build.

---

# 19. NOLQU SAFETY

NolQu-L Safety merupakan bagian inti NolQu-L.

Tujuannya adalah:

- memory safety,
- resource safety,
- deterministic resource management,
- explicit unsafe boundaries,
- predictable machine behavior,
- dan diagnostic yang jelas.

Prioritas analisis:

```text
Compile-time proof
↓
Static analysis
↓
Runtime checking only when necessary
```

Runtime check tidak boleh disisipkan tanpa dapat diketahui programmer.

---

# 20. DETERMINISTIC RESOURCE MANAGEMENT

Resource tidak boleh secara default bergantung pada garbage collector sebagai mekanisme utama.

Resource dapat mencakup:

- memory allocation,
- file,
- handle,
- lock,
- socket,
- mapping,
- system resource,
- custom resource.

Semua resource yang dimiliki suatu scope harus memiliki aturan release.

Pada success path:

```text
Acquire
↓
Use
↓
Release
```

Pada error path:

```text
Acquire
↓
Error
↓
Release
```

Jika beberapa resource diperoleh:

```text
Acquire A
Acquire B
Acquire C
Error
```

cleanup harus mengikuti aturan ownership/lifetime yang predictable, umumnya:

```text
Release C
Release B
Release A
```

Semua jalur control flow harus dianalisis.

---

# 21. OWNERSHIP

Ownership menentukan siapa yang bertanggung jawab terhadap resource.

Model konseptual:

```text
Resource
↓
Owner
↓
Lifetime
↓
Release
```

Compiler tidak boleh membuat asumsi ownership yang tidak dapat dibuktikan.

Evaluasi:

- ownership creation,
- ownership transfer,
- destruction,
- return,
- parameter passing,
- field ownership,
- scope exit,
- early return,
- error path.

---

# 22. MOVE SEMANTICS

Jika ownership dipindahkan:

```text
Owner A
   ↓ move
Owner B
```

A tidak boleh tetap menggunakan resource jika ownership sudah berpindah.

Compiler harus mendeteksi use-after-move.

Diagnostic harus menunjukkan:

- lokasi move,
- lokasi penggunaan setelah move,
- resource yang terlibat,
- saran penggunaan owner baru jika diketahui.

---

# 23. BORROW CHECKING

Borrowing memungkinkan penggunaan tanpa perpindahan ownership.

Borrow checker dibangun setelah ownership dan move semantics cukup stabil.

Periksa:

- reference lifetime,
- mutable alias conflict,
- immutable/mutable overlap,
- access after resource death,
- ownership transfer selama borrow aktif.

Jangan membuat aturan borrowing lebih rumit daripada yang dibutuhkan bahasa.

Jika compiler dapat menginfer informasi tanpa annotation pengguna, prioritaskan inference selama tetap predictable.

---

# 24. LIFETIME

Resource mempunyai lifetime.

Model:

```text
Acquire
↓
Alive
↓
Use / Borrow
↓
Lifetime Ends
↓
Release
```

Reference tidak boleh hidup lebih lama daripada resource yang dirujuk jika pelanggaran dapat dibuktikan.

Jangan memaksa pengguna menulis lifetime annotation di setiap tempat bila compiler dapat menyimpulkannya dengan aman.

---

# 25. UNINITIALIZED VALUE

Compiler harus mampu menolak penggunaan nilai yang belum diinisialisasi apabila dapat dibuktikan.

Analisis semua reachable control-flow path.

Contoh:

```text
var x

if condition {
    x = 10
}

print(x)
```

Jika terdapat path di mana `x` belum diinisialisasi, compiler harus memberi diagnostic.

---

# 26. BOUNDS SAFETY

Array, slice, buffer, atau memory region yang mempunyai bounds harus mengikuti safety mode.

Jika bounds dapat dibuktikan compile-time:

- jangan masukkan runtime check yang tidak perlu.

Jika tidak dapat dibuktikan:

- Balanced/Safe dapat melakukan runtime check sesuai aturan bahasa.

Biaya runtime check harus predictable.

Unsafe dapat memberi kontrol lebih besar tetapi tidak menghilangkan diagnostic lain.

---

# 27. NULL / INVALID REFERENCE

Nilai yang mungkin tidak ada harus direpresentasikan secara eksplisit melalui type/mechanism bahasa yang ditentukan.

Jangan membuat nullability tersembunyi.

Compiler tidak boleh membiarkan kemungkinan invalid reference diabaikan secara tidak sengaja pada mode dengan safety guarantee aktif.

---

# 28. MEMORY LEAK

Compiler boleh mendeteksi leak yang dapat dibuktikan.

Jangan menjanjikan bahwa seluruh leak akan selalu ditemukan.

Jika ownership keluar menuju:

- FFI,
- raw pointer,
- external library,
- custom allocator,
- assembly,
- atau sistem yang tidak dapat diverifikasi,

compiler harus memperjelas bahwa jaminan telah melewati safety boundary.

---

# 29. SAFETY MODES

NolQu-L Safety mempunyai tiga mode:

```text
SAFE
BALANCED
UNSAFE
```

## Balanced

Default NolQu-L.

Balanced bukan "Safe yang dikurangi".

Balanced merupakan safety identity utama NolQu-L:

```text
strong safety where provable
+
high flexibility
+
high performance
+
predictable control
```

## Safe

Memaksimalkan safety verification.

Ditujukan untuk software dengan reliability/safety requirement tinggi.

## Unsafe

Memaksimalkan low-level control.

Namun:

**Unsafe does not mean unchecked.**

Syntax checking, type checking, structural validation, dan diagnostic lain tetap aktif.

Unsafe hanya mengubah batas safety guarantee.

---

# 30. UNSAFE BLOCK

Unsafe operation harus eksplisit.

Contoh konseptual:

```text
unsafe {
    -- safety:
    -- pointer berasal dari allocation valid
    -- allocation masih hidup
    -- akses eksklusif dijamin

    *ptr = 42
}
```

Unsafe block:

- harus sekecil mungkin,
- tidak boleh digunakan sebagai shortcut,
- tetap dianalisis compiler sejauh memungkinkan,
- dan harus mempunyai safety invariant jika aturan NolQu saat itu mewajibkannya.

Safety comment menjelaskan invariant.

Safety comment **bukan bukti formal** bahwa kode benar.

---

# 31. SAFE ABSTRACTION

Unsafe implementation boleh digunakan sebagai fondasi API aman.

Model:

```text
unsafe implementation
↓
verified invariant
↓
safe abstraction
↓
ordinary caller
```

Jika function mempunyai precondition unsafe yang harus dipenuhi caller, boundary harus terlihat di titik pemanggilan.

Jangan menyembunyikan contract unsafe hanya di dokumentasi jauh dari call site.

---

# 32. UNDEFINED BEHAVIOR BOUNDARY

Definisikan batas antara:

1. valid dan dijamin,
2. invalid dan ditolak compiler,
3. runtime error yang terdefinisi,
4. unsafe tetapi mempunyai contract,
5. undefined behavior.

Contoh kategori UB NolQu:

```text
NQ-UB-001 — Invalid memory access
NQ-UB-002 — Invalid pointer dereference
NQ-UB-003 — Lifetime violation
NQ-UB-004 — Invalid aliasing
NQ-UB-005 — Invalid ABI / FFI contract
```

Kode final boleh berbeda jika spesifikasi semantik membutuhkan.

Jangan memperluas undefined behavior hanya untuk memudahkan optimizer.

UB harus sesempit dan sejelas mungkin.

---

# 33. FFI DAN ABI

FFI merupakan safety boundary.

Untuk interop dengan kode luar, tentukan:

- calling convention,
- parameter representation,
- return representation,
- struct layout,
- alignment,
- integer width,
- pointer representation,
- ownership transfer,
- siapa yang membebaskan memory,
- lifetime,
- error propagation,
- panic/runtime boundary.

Type compatibility lokal tidak otomatis membuktikan FFI safe.

---

# 34. CONCURRENCY

Bedakan:

```text
Memory Safety
≠
Concurrency Correctness
```

Program dapat bebas use-after-free tetapi masih mempunyai data race.

Architecture harus memungkinkan aturan eksplisit untuk:

- shared access,
- mutable access,
- atomics,
- mutex,
- lock,
- synchronization,
- memory ordering,
- threads.

Jangan menyembunyikan memory ordering atau atomic cost.

Concurrency safety ditambahkan bertahap setelah fondasi memory/resource model cukup stabil.

---

# 35. RUNTIME

Runtime NolQu harus sekecil yang diperlukan.

Evaluasi setiap runtime dependency dengan pertanyaan:

- mengapa diperlukan?
- apakah dapat dilakukan compile-time?
- apakah dapat menggunakan system facility langsung?
- berapa biaya memory?
- berapa biaya execution?
- apakah programmer dapat mengetahui keberadaannya?

Runtime tidak boleh menjadi tempat untuk menyembunyikan semantics yang seharusnya jelas di language/compiler.

---

# 36. STANDARD LIBRARY

Standard library harus berkembang berdasarkan kebutuhan fundamental.

Prioritaskan abstraction yang:

- umum,
- predictable,
- mempunyai ownership jelas,
- mempunyai cost model jelas,
- dan tidak memaksa runtime besar.

API standard library harus mengikuti prinsip:

**mudah digunakan tanpa menyembunyikan apa yang dilakukan mesin.**

---

# 37. CLI DAN TOOLCHAIN

Source standar NolQu-L menggunakan:

```text
*.nql
```

Dua command utama:

```text
nql / nolqul
nqlc / nolqulc
```

## Menjalankan source

```text
nql hello.nql
```

## Compile

```text
nqlc hello.nql -o hello
```

Flow konseptual:

```text
NolQu-L Source (*.nql)
        ↓
       nqlc
        ↓
       AST
        ↓
   NolQu-L IR
        ↓
    Optimizer
        ↓
   NolQu-L Codegen
        ↓
   Machine Code
        ↓
Executable / Target
```

Jika implementasi aktual membutuhkan tahap tambahan, tampilkan secara eksplisit.

Command tambahan dapat meliputi:

```text
nqlc --check
nql safety
nql audit
nql test
```

tetapi jangan menambahkan command hanya karena terlihat bagus.

Implementasikan hanya jika fungsi di baliknya nyata dan selesai.

---

# 38. EXIT CODE

CLI harus mempunyai contract exit code.

Minimal:

```text
0 = success
non-zero = failure
```

Jika kategori exit code dibuat lebih detail, dokumentasikan.

Contoh failure yang wajib menghasilkan non-zero:

- source tidak ditemukan,
- malformed input,
- lexical error,
- parse error,
- semantic error,
- type error,
- safety violation,
- backend failure,
- assembler failure,
- linker failure,
- internal compiler error.

---

# 39. DIAGNOSTIC SYSTEM

Buat diagnostic sebagai subsystem, bukan print tersebar di seluruh compiler.

Diagnostic idealnya mempunyai struktur internal seperti:

```text
severity
code
file
line
column
message
cause
explanation
suggestion
notes
```

Contoh user-facing:

```text
error[NS-203]: Use of moved resource 'buffer'
 --> file.nql:42:9

The resource was moved to 'output' at line 38 and is no longer available here.

Suggestion:
Use 'output' instead.
```

Setiap compiler stage harus menggunakan sistem diagnostic yang konsisten.

Kategori diagnostic sebaiknya dapat dibedakan, misalnya:

```text
LEX-xxx
PAR-xxx
SEM-xxx
TYP-xxx
NS-xxx
IR-xxx
CG-xxx
LNK-xxx
ICE-xxx
```

Nama final boleh disesuaikan dengan codebase.

Jangan mengganti semua kode diagnostic lama apabila compatibility tidak memerlukan.

---

# 40. INTERNAL COMPILER ERROR

Bedakan user error dari compiler bug.

Malformed source adalah user error.

Compiler panic karena malformed source adalah compiler bug.

Jika invariant internal compiler rusak, hasilkan sesuatu seperti:

```text
internal compiler error[ICE-xxx]
```

dengan konteks yang cukup untuk debugging tetapi tidak membanjiri pengguna dengan state yang tidak relevan.

---

# 41. LANGKAH 0 — BASELINE TEST

**SEBELUM MENGUBAH FILE APA PUN**, jalankan seluruh test yang tersedia.

Catat command persis yang digunakan.

Jangan mengarang command.

Cari test dari:

- build configuration,
- project scripts,
- CI configuration,
- Makefile,
- test runner,
- compiler test harness,
- bootstrap test scripts.

Catat:

```text
Baseline
--------
Total:
Passed:
Failed:
Skipped:
Expected-fail:
Timeout:
Crash:
```

Jika ada test merah sebelum perubahan:

tandai sebagai:

```text
PRE-EXISTING FAILURE
```

Bukan regresi baru.

Untuk setiap pre-existing failure:

- nama test,
- command,
- actual result,
- expected result,
- kemungkinan penyebab.

Perbaiki sebelum melanjutkan jika realistis.

Jika belum dapat diperbaiki, dokumentasikan secara eksplisit dan jangan berpura-pura baseline hijau.

---

# 42. BASELINE BOOTSTRAP TEST

Jika bootstrap infrastructure sudah tersedia, baseline juga wajib menguji bootstrap chain.

Periksa stage yang benar-benar tersedia.

Contoh:

```text
Machine-Level Foundation    PASS / FAIL / NOT IMPLEMENTED
Stage 0                     PASS / FAIL / NOT IMPLEMENTED
Bootstrap Compiler          PASS / FAIL / NOT IMPLEMENTED
Core Compiler               PASS / FAIL / NOT IMPLEMENTED
Full Compiler               PASS / FAIL / NOT IMPLEMENTED
Self-host                   PASS / FAIL / NOT IMPLEMENTED
Verified rebuild            PASS / FAIL / NOT IMPLEMENTED
```

Jangan menyebut stage PASS hanya karena directory-nya ada.

Stage dianggap ada hanya jika mempunyai artifact/build/test yang nyata.

---

# 43. LANGKAH 1 — EVALUASI KESIAPAN MENYELURUH

Setelah baseline selesai, audit codebase.

Setiap jawaban harus mempunyai **bukti konkret**.

Jangan hanya menulis:

> "Sepertinya aman."

Tunjukkan:

- file,
- function,
- test,
- build,
- atau jalur code yang menjadi dasar kesimpulan.

---

# 44. STABILITAS

Jawab seluruh poin:

- Apakah seluruh baseline test hijau?
- Apakah compiler crash pada source valid?
- Apakah malformed source menyebabkan crash?
- Bagaimana compiler menangani empty file?
- Bagaimana compiler menangani file tidak ditemukan?
- Bagaimana compiler menangani unreadable file?
- Bagaimana compiler menangani truncated input?
- Bagaimana compiler menangani token tidak valid?
- Bagaimana compiler menangani deeply nested expression?
- Apakah lexer selalu progress?
- Apakah parser selalu progress?
- Apakah analysis pass selalu terminate?
- Apakah terdapat recursion tanpa batas?
- Apakah terdapat loop tanpa progress?
- Apakah terdapat kemungkinan hang?
- Apakah subprocess/tool invocation mempunyai error handling?

Test kasus yang dapat dilakukan.

---

# 45. MEMORY DAN RESOURCE

Audit:

- allocation,
- reallocation,
- deallocation,
- file open/close,
- directory handle,
- process handle,
- pipe,
- temporary file,
- mmap,
- lock,
- arena,
- compiler-owned buffers.

Untuk setiap resource, periksa:

```text
success path
error path
early return
partial initialization
```

Pastikan cleanup terjadi di semua jalur.

Jika compiler implementation language mempunyai automatic cleanup, tetap periksa ownership logic dan external resource.

Gunakan sanitizer/tool jika sudah tersedia dan sesuai environment.

Jangan mengklaim "tidak ada memory leak" hanya karena test selesai.

Gunakan wording berdasarkan bukti:

```text
No leak detected by <tool/test>
```

bukan:

```text
Compiler has no possible leaks.
```

---

# 46. ERROR HANDLING

Audit setiap layer:

```text
CLI
File loading
Lexer
Parser
Semantic
Type checker
NolQu-L Safety
IR
Optimizer
Codegen
Assembler
Linker
Runtime
```

Cari:

- ignored return value,
- empty catch,
- swallowed error,
- `unwrap`/panic/assert pada input pengguna,
- return tanpa diagnostic,
- diagnostic tanpa source location,
- backend error mentah,
- silent fallback.

Perbaiki jalur tersebut sebelum fitur baru jika signifikan.

---

# 47. ARSITEKTUR

Evaluasi apakah boundary sekarang jelas.

Jawab:

- Apakah lexer independen dari codegen?
- Apakah parser menghasilkan representasi yang jelas?
- Apakah semantic analysis terpisah dari parsing?
- Apakah type checking mempunyai tempat jelas?
- Apakah safety checker mempunyai tempat jelas?
- Apakah IR mempunyai invariant?
- Apakah optimizer hanya menerima valid IR?
- Apakah codegen tergantung pada source syntax secara langsung?
- Apakah backend target-specific terisolasi?
- Apakah diagnostic terpusat?
- Apakah filesystem/tool invocation terisolasi?
- Apakah CLI terpisah dari compiler library/core?

Jika coupling signifikan ditemukan, tentukan apakah refactor diperlukan sebelum fitur baru.

---

# 48. UTANG TEKNIS

Cari technical debt yang benar-benar dapat menghambat pengembangan.

Contoh:

- satu file compiler terlalu besar,
- parser sekaligus type checker,
- duplicated error construction,
- global mutable state,
- symbol table tidak mempunyai scope model jelas,
- backend menerima AST mentah,
- tidak ada source span,
- semua tipe direpresentasikan string,
- IR tidak tervalidasi,
- resource cleanup manual tersebar,
- bootstrap stage tidak dapat dibangun independen,
- build dependency tidak terdokumentasi.

Jangan refactor hanya karena preferensi gaya.

Refactor hanya jika meningkatkan:

- correctness,
- modularity,
- testability,
- maintainability,
- bootstrap traceability,
- atau kemampuan fitur berikutnya.

---

# 49. BOOTSTRAP READINESS

Audit secara khusus:

### Machine-Level Foundation

Apakah benar ada?

Apa bentuknya?

### Stage 0

Apakah benar Stage 0 atau hanya nama untuk compiler host-language?

### Bootstrap compiler

Apakah Stage 0 benar-benar dapat membangunnya?

### Core compiler

Fitur Core apa saja yang sudah dapat mengompilasi dirinya/komponen berikutnya?

### Full compiler

Subsystem mana yang sudah tersedia?

### Self-hosting

Apakah `nqlc` dapat mengompilasi source compiler NolQu-L?

### Verification

Apakah rebuild diverifikasi?

Laporkan dengan status:

```text
IMPLEMENTED
PARTIAL
NOT IMPLEMENTED
BROKEN
BLOCKED
```

Jangan menyamakan PARTIAL dengan IMPLEMENTED.

---

# 50. TEST INFRASTRUCTURE

Evaluasi keberadaan:

- unit tests,
- parser tests,
- lexer tests,
- compile-pass,
- compile-fail,
- runtime tests,
- safety tests,
- backend tests,
- integration tests,
- bootstrap tests,
- regression tests.

Compile-fail test harus memeriksa lebih dari sekadar exit code jika memungkinkan.

Minimal:

- diagnostic code,
- diagnostic location,
- alasan penolakan.

---

# 51. FUZZ / MALFORMED INPUT ROBUSTNESS

Jika infrastructure memungkinkan tanpa membuat scope meledak, tambahkan malformed-input testing pada parser/lexer.

Tujuan:

- tidak crash,
- tidak hang,
- tidak infinite loop,
- tidak memory corruption.

Tidak perlu membuat fuzzer besar bila codebase belum siap.

Tetapi lexer/parser harus mempunyai regression tests untuk malformed input penting yang ditemukan.

---

# 52. KEPUTUSAN: SIAP ATAU BELUM SIAP

Setelah audit, tetapkan salah satu:

```text
SIAP
```

atau:

```text
BELUM SIAP
```

Jangan memilih SIAP apabila terdapat blocker fundamental pada:

- stability,
- resource handling,
- architecture,
- bootstrap foundation,
- compiler pipeline,
- atau error handling.

---

# 53. JIKA BELUM SIAP

Jika **BELUM SIAP**, lakukan urutan berikut:

1. Perbaiki regression/pre-existing critical failure.
2. Perbaiki crash/hang.
3. Perbaiki resource lifetime/error path.
4. Perbaiki silent failure.
5. Rapikan boundary arsitektur yang menjadi blocker.
6. Perbaiki bootstrap chain jika tahap foundation tidak jelas.
7. Tambahkan regression test.
8. Jalankan seluruh baseline lagi.

Jangan menambahkan fitur besar sebelum foundation kembali stabil.

Perbaikan harus menyelesaikan penyebab, bukan hanya symptom.

---

# 54. JIKA SUDAH SIAP

Jika **SIAP**, identifikasi fitur fundamental berikutnya berdasarkan dependency.

Urutan default:

```text
Machine-Level Foundation
↓
Stage 0 completeness
↓
Core language
↓
Lexer / Parser robustness
↓
Semantic foundation
↓
Type system
↓
IR
↓
Code generation
↓
Resource management
↓
Use-after-free detection
↓
Uninitialized checking
↓
Bounds checking
↓
Ownership
↓
Move semantics
↓
Borrow checking
↓
Lifetime
↓
Safe abstraction / Unsafe API
↓
FFI / ABI boundaries
↓
Concurrency model
↓
Safety modes
↓
Optimizer
↓
Runtime / Standard Library expansion
↓
Tooling
↓
Self-hosting
↓
Verified bootstrap
```

Urutan ini boleh disesuaikan berdasarkan kondisi codebase nyata.

Tetapi jelaskan mengapa.

---

# 55. IMPLEMENTASI FITUR

Untuk setiap fitur yang dipilih:

## A. Definisikan semantics

Jelaskan secara teknis apa yang harus terjadi.

## B. Tentukan compiler stage

Misalnya:

```text
Lexer
Parser
Semantic
Type
Safety
IR
Backend
Runtime
```

## C. Implementasi lengkap

Jangan meninggalkan:

- TODO kritis,
- dummy branch,
- hardcoded success,
- placeholder backend,
- fake implementation.

## D. Diagnostic

Invalid use harus mempunyai error yang jelas.

## E. Test positif

Program valid bekerja.

## F. Test negatif

Program invalid ditolak.

## G. Regression run

Jalankan test keseluruhan.

Baru setelah hijau, lanjut ke fitur berikutnya.

---

# 56. REGRESSION PROTOCOL

Jika test yang sebelumnya hijau menjadi merah:

**HENTIKAN PENAMBAHAN FITUR.**

Lakukan:

1. reproduksi regression,
2. identifikasi perubahan penyebab,
3. tentukan apakah bug implementasi atau test yang memang harus berubah,
4. jika breaking semantic change disengaja, jelaskan,
5. perbaiki regression,
6. jalankan suite lagi.

Jangan melanjutkan fitur baru dengan alasan:

> "akan diperbaiki nanti."

---

# 57. COMPATIBILITY

Setiap perubahan syntax atau semantics harus diperiksa terhadap source lama.

Kategori:

```text
Fully Compatible
Source Compatible
Behavior Change
Breaking Change
```

Jika breaking:

berikan alasan.

Jangan mengganti syntax hanya karena syntax lain terasa lebih modern.

---

# 58. OPTIMIZATION

Optimization tidak boleh mengubah semantics.

Prioritas:

1. architecture,
2. algorithmic improvement,
3. redundant work elimination,
4. allocation reduction,
5. IR simplification,
6. backend/code quality,
7. micro-optimization terakhir.

Jika optimizer sudah ada, setiap pass harus mempunyai:

- input invariant,
- output invariant,
- test,
- correctness requirement.

Jika optimizer belum dibutuhkan, jangan membuat optimizer kompleks hanya untuk memenuhi checklist.

---

# 59. PERFORMANCE

Jika mengklaim improvement performa, ukur jika environment memungkinkan.

Catat:

```text
Before
After
Method
Input
Iterations
Variance jika relevan
```

Jangan menyebut sebuah perubahan "lebih cepat" tanpa basis.

Untuk structural optimization yang secara langsung menghilangkan operasi jelas, boleh menjelaskan reasoning, tetapi bedakan dari benchmark aktual.

---

# 60. BUILD REPRODUCIBILITY

Build compiler harus sedeterministik mungkin.

Audit:

- iteration order,
- temporary path leakage,
- timestamps,
- environment-dependent output,
- random ordering,
- uninitialized data,
- host-specific metadata.

Jika belum bit-for-bit reproducible, dokumentasikan penyebabnya.

---

# 61. TARGET DAN PORTABILITAS

Jangan memaksakan multiarchitecture sebelum target pertama stabil.

Tetapi jangan menulis frontend sedemikian rupa sehingga seluruh bahasa terkunci pada satu ISA.

Pisahkan:

```text
Language semantics
Target-independent IR
Target backend
ABI
Object format
System interface
```

sebisa mungkin.

Machine-specific behavior harus berada pada tempat yang tepat.

---

# 62. SECURITY DAN TRUST BOUNDARY COMPILER

Compiler menerima source yang mungkin malformed.

Source user tidak boleh dianggap trusted.

Audit:

- bounds pada parser,
- integer parsing,
- path handling,
- generated filenames,
- temporary files,
- subprocess arguments,
- linker arguments,
- shell invocation.

Hindari membangun shell command dari source user jika dapat menggunakan direct process invocation.

Compiler crash karena malformed source harus dianggap bug.

---

# 63. DOKUMENTASI IMPLEMENTASI

Jika perubahan mengubah arsitektur atau semantics yang penting, update dokumentasi terkait.

Dokumentasikan:

- design decision,
- invariant,
- stage boundary,
- bootstrap dependency,
- diagnostic code,
- syntax/semantic baru.

Jangan menulis dokumentasi untuk fitur yang belum benar-benar ada seolah sudah implemented.

Bedakan:

```text
Implemented
Planned
Experimental
```

---

# 64. DEFINITION OF DONE

Sebuah fitur hanya dianggap selesai jika:

- semantics jelas,
- implementasi lengkap,
- error path ada,
- test positif ada,
- test negatif ada jika relevan,
- regression suite hijau,
- tidak ada placeholder penting,
- dokumentasi diperbarui jika diperlukan,
- tidak menambah technical debt kritis.

---

# 65. DEFINITION OF DONE UNTUK BOOTSTRAP STAGE

Sebuah bootstrap stage hanya dianggap selesai apabila:

1. source/artifact-nya nyata,
2. build command tersedia,
3. dependency terdokumentasi,
4. output dapat digunakan sesuai tujuan stage,
5. test stage tersedia,
6. hubungan ke stage sebelumnya dapat dijelaskan,
7. hubungan ke stage berikutnya dapat dibuktikan.

Folder bernama `stage0` saja bukan bukti Stage 0 selesai.

---

# 66. HAL YANG DILARANG

Jangan:

- mengarang hasil test,
- mengarang benchmark,
- mengarang file yang tidak diperiksa,
- menyebut fitur implemented jika hanya skeleton,
- menutupi failure,
- menghapus test hanya agar CI hijau,
- men-disable test tanpa alasan kuat,
- mengubah expected result agar bug terlihat benar,
- memasukkan unsafe sebagai solusi mudah,
- menambahkan GC hanya untuk menghindari resource model,
- menambahkan runtime besar tanpa alasan,
- menyembunyikan machine cost,
- membuat abstraction yang tidak dapat dijelaskan,
- melakukan rewrite seluruh compiler tanpa kebutuhan nyata,
- memecahkan compatibility hanya karena refactor terasa lebih bersih.

---

# 67. LANGKAH 3 — FINAL VALIDATION

Setelah seluruh implementasi selesai, jalankan kembali:

1. unit tests,
2. integration tests,
3. compile-pass tests,
4. compile-fail tests,
5. safety tests,
6. malformed-input regression tests,
7. runtime tests,
8. backend tests,
9. bootstrap tests,
10. self-host tests jika tersedia,
11. bootstrap verification jika tersedia.

Bandingkan dengan baseline.

Tidak boleh ada test baseline hijau yang menjadi merah.

---

# 68. FINAL RESOURCE CHECK

Uji jalur:

```text
success
error
early-return
invalid source
missing input
backend failure
link failure
```

Pastikan compiler tidak meninggalkan resource yang seharusnya dilepas.

---

# 69. FINAL DIAGNOSTIC CHECK

Ambil beberapa error dari layer berbeda dan verifikasi formatnya.

Minimal:

- lexical,
- parse,
- semantic/type,
- safety,
- toolchain/backend jika dapat dipicu dengan aman.

Pastikan diagnostic mempunyai konteks cukup.

---

# 70. FINAL BOOTSTRAP STATUS

Laporkan rantai lengkap:

```text
Machine-Level Foundation : ...
Stage 0                  : ...
Bootstrap Compiler       : ...
Core Compiler            : ...
Full Compiler            : ...
Self-Hosting nqlc        : ...
Verified nqlc            : ...
```

Gunakan hanya:

```text
PASS
PARTIAL
FAIL
NOT IMPLEMENTED
BLOCKED
NOT TESTED
```

sertai bukti.

---


# 71. FORMAT OUTPUT WAJIB

Output akhir sesi harus menggunakan struktur lengkap berikut.

## 0. UPDATE CLASSIFICATION & RELEASE IMPACT

Sebelum melaporkan hasil implementasi, tuliskan:

```text
Requested Mode:
Actual Update Class:
Risk Level:
Primary Scope:
Affected Subsystems:
Public Contract Impact:
Bootstrap Impact:
Security/Trust Impact:
Compatibility Impact:
Version Impact:
Release Maturity:
RFC Required:
ADR Required:
Migration Required:
Changelog Required:
Rollback/Revert Required:
Release Blocking Issues:
```

Jika classification berubah selama sesi:

```text
Initial Class:
Final Class:
Reason for Reclassification:
```

Jika tidak ada release yang dilakukan, tuliskan:

```text
Release Performed: NO
Version Bump: NONE
```

Jangan menaikkan version hanya karena satu development session selesai.


## 1. BASELINE TEST

Tuliskan:

```text
Commands executed:
...

Total:
Passed:
Failed:
Skipped:
Timeout:
Crash:

Pre-existing failures:
...
```

Untuk setiap failure, berikan detail.

## 2. BASELINE BOOTSTRAP

```text
Machine-Level Foundation:
Stage 0:
Bootstrap Compiler:
Core Compiler:
Full Compiler:
Self-host:
Verified rebuild:
```

Berikan bukti masing-masing.

## 3. EVALUASI KESIAPAN

Kesimpulan:

```text
SIAP
```

atau:

```text
BELUM SIAP
```

Kemudian evaluasi lengkap.

### Stability

Jelaskan seluruh temuan.

### Memory & Resource

Jelaskan seluruh temuan.

### Error Handling

Jelaskan seluruh temuan.

### Architecture

Jelaskan seluruh temuan.

### Bootstrap

Jelaskan seluruh temuan.

### Compiler Pipeline

Jelaskan status:

```text
Lexer
Parser
AST
Semantic
Type
Safety
IR
Optimizer
Codegen
Runtime
```

### CLI / Toolchain

Jelaskan status.

### Testing

Jelaskan coverage dan gap.

### Compatibility

Jelaskan potensi masalah.

### Technical Debt

Daftar seluruh debt signifikan yang ditemukan.

## 4. RENCANA PERUBAHAN

Sebelum implementasi, tuliskan seluruh rencana.

Untuk setiap item:

```text
Priority:
Problem:
Root cause:
Files/modules:
Planned change:
Why now:
Risk:
Required tests:
```

Urutkan berdasarkan dependency.

## 5. IMPLEMENTASI

Untuk setiap perubahan:

```text
Change:
Files modified:
Reason:
Implementation:
Error handling:
Tests added:
Compatibility:
```

Tampilkan perubahan kode nyata.

Jangan hanya mengatakan:

> "Implemented X."

Jelaskan bagian penting implementasinya.

## 6. FITUR BARU

Jika fitur baru ditambahkan, dokumentasikan:

```text
Feature:
Syntax/API:
Semantics:
Compiler stages involved:
Machine/runtime cost:
Safety behavior:
Invalid cases:
Diagnostics:
Tests:
```

## 7. BUG YANG DITEMUKAN

Untuk setiap bug:

```text
Bug:
Severity:
Location:
Cause:
Status:
Fix:
Regression test:
```

Status:

```text
FIXED
OPEN
BLOCKED
DEFERRED-NONBLOCKING
```

Blocker tidak boleh dibiarkan DEFERRED.

## 8. HASIL TEST SETELAH IMPLEMENTASI

```text
Total:
Passed:
Failed:
Skipped:
Timeout:
Crash:
```

Bandingkan dengan baseline.

Nyatakan eksplisit:

```text
Regression detected: YES / NO
```

## 9. BOOTSTRAP VERIFICATION

Jika tersedia:

```text
Compiler A:
Compiler B:
Compiler C:

B vs C:
```

Jika sama:

jelaskan metode comparison.

Jika berbeda:

jelaskan perbedaan dan jangan klaim verified.

## 10. RESOURCE / MEMORY VALIDATION

Tuliskan apa yang benar-benar diuji.

Contoh:

```text
File descriptors:
Memory allocations:
Error cleanup:
Temporary files:
Subprocess:
```

Jangan membuat klaim lebih luas daripada test yang dilakukan.

## 11. DIAGNOSTIC VALIDATION

Berikan contoh actual diagnostic dari implementasi untuk beberapa kategori error.

Pastikan:

```text
code
location
cause
explanation
suggestion
```

tersedia bila relevan.

## 12. COMPATIBILITY REPORT

Tuliskan ringkasan:

```text
Backward compatibility:
Breaking changes:
Migration required:
Version impact:
Reason:
```

Untuk perubahan signifikan, sertakan Compatibility Matrix:

| Axis | Status | Evidence / Migration |
| --- | --- | --- |
| Source syntax | ... | ... |
| Source semantics | ... | ... |
| CLI/tooling | ... | ... |
| Standard library/API | ... | ... |
| ABI/FFI | ... | ... |
| Binary/object artifact | ... | ... |
| Runtime behavior | ... | ... |
| Bootstrap chain | ... | ... |
| Reproducibility | ... | ... |
| Diagnostic contract | ... | ... |
| Project/module format | ... | ... |

Jika tidak ada breaking change, sebutkan eksplisit.

## 13. FINAL ARCHITECTURE STATUS

Tampilkan pipeline aktual setelah perubahan:

```text
*.nql
↓
...
↓
Machine / Object Code
↓
Executable
```

Jangan menampilkan pipeline ideal jika codebase belum benar-benar mengimplementasikannya.

Bedakan:

```text
CURRENT
```

dengan:

```text
TARGET
```

jika keduanya berbeda.

## 14. FINAL BOOTSTRAP CHAIN STATUS

Tampilkan:

```text
Machine-Level Foundation
        ↓
Stage 0
        ↓
Bootstrap Compiler
        ↓
Core Compiler
        ↓
Full Compiler
        ↓
Self-Hosting nqlc
        ↓
Verified nqlc
```

Di samping setiap tahap, tuliskan status nyata.


## 14A. RELEASE / CHANGELOG STATUS

Jika sesi menghasilkan perubahan yang layak masuk release, tuliskan:

```text
Release Candidate:
Version Impact:
Maturity:
Changelog Updated:
Migration Guide:
Deprecations:
Removals:
Known Issues:
Review Gate:
CI Gate:
Artifact Hashes:
Provenance:
Signing:
SBOM:
Support Lifecycle:
Security Advisory:
Release Gate:
```

Jika belum layak release:

```text
Release Ready: NO
Blocking Reasons:
```

Changelog user-visible gunakan kategori bila relevan:

```text
Added
Changed
Deprecated
Removed
Fixed
Security
Performance
Compatibility
Bootstrap
Known Issues
Migration
```

## 15. RINGKASAN AKHIR SESI

Jangan sekadar menulis satu paragraf umum.

Jawab secara eksplisit:

### Apa yang berubah?

Semua perubahan penting.

### Apa dampaknya?

Terhadap:

- compiler,
- language,
- safety,
- bootstrap,
- performance,
- maintainability,
- compatibility.

### Apakah semua test baseline tetap hijau?

Jawab berdasarkan hasil nyata.

### Apakah terdapat regression?

Jika ya, tidak boleh dianggap selesai sampai diperbaiki.

### Apakah ada pre-existing failure?

Sebutkan status akhirnya.

### Bug di luar scope

Sebutkan dan berikan status.

### Bootstrap sekarang berada di tahap mana?

Sebutkan secara eksplisit.

### Apa yang belum selesai?

Jangan menyembunyikan gap.

### Apa prioritas sesi berikutnya?

Susun berdasarkan dependency teknis, bukan berdasarkan fitur yang paling menarik.

---

# 72. PRIORITAS JANGKA PANJANG NOLQU-L

Selalu ingat bahwa tujuan akhirnya bukan hanya membuat compiler dapat mengompilasi contoh sederhana.

Target jangka panjang adalah:

```text
Machine-Level Foundation
↓
Minimal auditable bootstrap
↓
Stable Core Language
↓
Structured Compiler Pipeline
↓
Deterministic Resource Model
↓
NolQu-L Safety
↓
Strong Type/Semantic Foundation
↓
Predictable Machine-Level Code Generation
↓
Usable Runtime + Standard Library
↓
Modules / Program Structure
↓
Large Program Capability
↓
Low-Level Capability
↓
Self-Hosting
↓
Verified Bootstrap
```

NolQu-L harus berkembang sehingga kode sederhana tetap sederhana:

```text
simple program
→ simple source
```

sementara program besar dapat berkembang secara terstruktur:

```text
large program
→ modules
→ types
→ functions
→ ownership
→ explicit resource boundaries
→ libraries
→ clear interfaces
```

tanpa mengubah NolQu-L menjadi bahasa yang terasa berat untuk penggunaan kecil.

---

# 73. FILOSOFI AKHIR

Setiap kali terdapat dua pilihan desain, tanyakan:

```text
Apakah lebih sederhana?
Apakah lebih mudah dibaca?
Apakah perilaku mesinnya dapat diprediksi?
Apakah cost-nya terlihat?
Apakah compiler dapat menanggung kompleksitas ini?
Apakah safety boundary-nya jelas?
Apakah error-nya dapat dijelaskan?
Apakah dapat diuji?
Apakah kompatibel?
Apakah membantu perjalanan menuju self-hosting?
Apakah dapat diverifikasi dari bootstrap stage sebelumnya?
```

Jika jawabannya tidak jelas, jangan terburu-buru menambah abstraction.

NolQu-L tidak harus menjadi tiruan C, C++, Rust, Zig, Go, atau bahasa lain.

Teknik dari bahasa lain boleh dipelajari.

Namun keputusan akhir harus mengikuti identitas NolQu-L sendiri.

Targetnya adalah:

> **A general-purpose systems programming language that remains simple and readable at the surface, transparent toward the machine underneath, safe where the compiler can prove safety, explicit where programmer responsibility begins, and capable of bootstrapping itself from a traceable machine-level foundation into a verified self-hosting compiler.**

Dan aturan bootstrap terpenting tetap:

> **Every compiler generation must be explainable, traceable, testable, and verifiable from the generation before it.**

Tidak boleh ada lompatan misterius dari "machine" langsung ke "full compiler".

Tidak boleh ada foundation yang hanya dipercaya karena sudah berbentuk binary.

Mulai dari mesin.

Bangun Stage 0 sekecil mungkin.

Gunakan Stage 0 untuk membangun Core.

Gunakan Core untuk membangun compiler yang lebih kuat.

Gunakan compiler tersebut untuk membangun Full NolQu-L.

Gunakan Full NolQu-L untuk membangun `nqlc` dari source NolQu-L sendiri.

Kemudian bangun lagi.

Bandingkan hasilnya.

Barulah rantai bootstrap dapat disebut benar-benar terverifikasi.


---

# ADDITIVE DESIGN CLARIFICATIONS — NAMING MIGRATION & EXPLICIT SAFETY SYNTAX

Bagian ini **hanya menambahkan dan menyesuaikan detail yang belum dikunci secara lengkap**. Bagian ini tidak menghapus, mengganti, atau menurunkan status desain yang sudah ditetapkan sebelumnya dalam dokumen ini maupun dalam `NolQu-LConcept.docx`.

Aturan utamanya:

- Nine Pillars selalu berlaku; jika perumusan lama berbeda, gunakan versi normatif terbaru pada bagian `# 1. NINE PILLARS OF NOLQU-L` dan simpan bagian ini sebagai konteks historis.
- Rantai bootstrap canonical tetap berlaku tanpa perubahan.
- Status repository yang sudah tercatat tidak boleh diubah hanya karena bagian ini ditambahkan.
- NolQu-L Safety tetap mempunyai **tiga mode: Balanced, Safe, dan Unsafe**.
- **Balanced tetap mode bawaan dan safety identity utama NolQu-L.**
- Safe tetap memaksimalkan safety verification.
- Unsafe tetap memaksimalkan low-level control tanpa berarti compiler berhenti melakukan checking.
- Interface CLI canonical di bawah ini sudah diimplementasikan. Migrasi seluruh
  corpus source/path lama tetap bertahap dan harus menjaga compatibility.
- Nama, artifact, command, fixture, atau path lama yang masih diperlukan oleh bootstrap/test tetap dipertahankan sampai migrasinya benar-benar diimplementasikan dan dibuktikan oleh test.

## NolQu Ecosystem dan NolQu-L

Gunakan pemisahan nama berikut secara konsisten:

```text
NolQu
└── ecosystem / umbrella project

NolQu-L
└── programming language
```

`NolQu-L` tetap merupakan **nama formal bahasa**. Huruf `L` tetap ditulis sebagai bagian dari nama formal tersebut walaupun berasal dari `Language`.

`NolQu` tanpa `-L` digunakan untuk menyebut ekosistem yang lebih luas apabila konteksnya memang mencakup lebih dari bahasanya sendiri, misalnya tooling, runtime, library, compiler infrastructure, safety tooling, dan komponen ekosistem lain.

Jangan mengganti penyebutan formal bahasa `NolQu-L` menjadi hanya `NolQu`.

## Canonical Naming Migration

Naming user-facing NolQu-L menggunakan bentuk yang langsung terhadap identitas `NolQu-L`:

```text
source extension : *.nq  -> *.nql
project manager  : nql   (alias nama panjang: nolqul -> nql)
compiler command : nqlc  (alias nama panjang: nolqulc -> nqlc)
```

Topologi file command canonical adalah:

```text
nql                 executable project manager
nolqul -> nql       alias nama panjang
nqlc                executable compiler
nolqulc -> nqlc     alias nama panjang
```

Tidak ada rantai alias ke implementasi bernama lama. Bentuk `nql -> nq`,
`nqlc -> nolquc`, dan `nqc -> nolquc` semuanya tidak valid.

Sehingga bentuk user-facing canonical aktif adalah:

```text
NolQu-L source : *.nql
Run            : nql / nolqul
Compiler       : nqlc / nolqulc
```

Contoh:

```text
nql hello.nql
nolqul hello.nql
nqlc hello.nql -o hello
nolqulc hello.nql -o hello
```

Flow konseptual user-facing:

```text
NolQu-L Source (*.nql)
        ↓
       nqlc
        ↓
        AST
        ↓
    NolQu-L IR
        ↓
     Optimizer
        ↓
    NolQu-L Codegen
        ↓
    Machine Code
        ↓
Executable / Target
```

### Historical Source Rule

Naming migration tidak boleh merusak bootstrap, test, artifact, atau source yang sudah bekerja.

Karena itu:

- command lama `nq`, `nqc`, `nolqu`, dan `nolquc` tidak dipasang dan tidak
  disediakan sebagai compatibility alias;
- adapter R0 boleh menerima source `.nq` untuk sementara selama migrasi corpus,
  tetapi source user-facing baru wajib memakai `.nql`;
- penyebutan lama dalam bagian history, evidence, status repository, bootstrap artifact, atau test **tidak perlu ditulis ulang secara retroaktif**;
- file seperti `compiler.nql0`, fixture bootstrap `.nql`, atau nama artifact lain yang sudah menjadi bagian kontrak bootstrap tidak boleh diganti hanya demi konsistensi kosmetik;
- interface CLI canonical dianggap aktif karena command/source baru tersedia dan
  test compatibility khusus sudah ada; migrasi corpus keseluruhan belum selesai;
- status implementasi harus selalu mengikuti bukti test repository terbaru.

Dengan demikian, bagian lama yang masih menyebut `nolqu`, `nolquc`, `nq`,
`nqc`, atau `.nq` hanya berfungsi sebagai dokumentasi status/kontrak lama.
Penyebutan historis tersebut tidak berarti command dengan nama itu tersedia.

## Explicit Safe Syntax

Safe Mode tetap merupakan salah satu dari tiga mode NolQu-L Safety dan **tidak menggantikan Balanced sebagai default**.

Tambahkan syntax eksplisit untuk memasuki Safe boundary pada scope tertentu:

```text
safe {
    ...
}
```

Semantik dasar:

- code di dalam `safe { ... }` diverifikasi menggunakan aturan Safe Mode;
- compiler memaksimalkan verification yang tersedia untuk scope tersebut;
- operasi yang tidak memenuhi safety model dapat ditolak;
- memasukkan code ke dalam `safe {}` **tidak membuat data, pointer, reference, atau invariant yang tidak terbukti menjadi otomatis aman**;
- setelah block selesai, safety mode kembali ke mode enclosing sebelumnya.

Contoh konseptual:

```text
safe {
    let buffer = allocate(1024)
    process(buffer)
}
```

## Explicit Unsafe Syntax

`unsafe { ... }` tetap mengikuti desain yang sudah ada:

```text
unsafe {
    -- safety:
    -- pointer berasal dari allocation valid
    -- allocation masih hidup
    -- akses eksklusif dijamin

    *ptr = 42
}
```

Aturan yang sudah ada tetap berlaku:

- unsafe harus eksplisit;
- block harus dibuat sekecil mungkin;
- unsafe bukan shortcut untuk menghindari safety checker;
- compiler tetap melakukan syntax checking, type checking, structural validation, dan analysis lain yang masih dapat dilakukan;
- bagian yang tidak dapat diverifikasi berpindah menjadi tanggung jawab programmer;
- safety invariant tetap diperlukan apabila contract NolQu-L Safety mewajibkannya.

## Interaction Between Safe and Unsafe Blocks

Boundary dapat dinest secara eksplisit selama semantics-nya tidak ambigu.

### Safe di dalam Unsafe

```text
unsafe {
    let ptr = get_raw_pointer()

    safe {
        process_state()
    }
}
```

`safe {}` mengaktifkan kembali Safe verification untuk scope tersebut, tetapi **tidak membersihkan atau mengesahkan state unsafe secara otomatis**.

Contoh berikut tetap harus ditolak jika validitas `ptr` tidak dapat dibuktikan oleh aturan Safe:

```text
unsafe {
    let ptr = get_raw_pointer()

    safe {
        *ptr = 42
    }
}
```

### Unsafe di dalam Safe

Safe code tetap boleh mempunyai escape hatch yang eksplisit untuk operasi yang memang tidak dapat diverifikasi:

```text
safe {
    prepare_state()

    unsafe {
        -- safety: hardware register valid untuk target ini
        *device_register = value
    }

    continue_safe_work()
}
```

Setelah `unsafe {}` selesai, enclosing scope kembali mengikuti Safe Mode.

## Function-Level Safety Syntax

Function dapat menyatakan safety boundary secara eksplisit.

### Ordinary Function

```text
fn process() {
    ...
}
```

`fn` biasa **tidak berarti Safe Mode**. Function biasa mewarisi mode yang berlaku dari konteks bahasa/file/module. Karena mode default NolQu-L adalah Balanced, ordinary function pada program default berjalan di bawah Balanced.

Secara konseptual:

```text
fn = inherit enclosing mode

default enclosing mode = Balanced
```

### Safe Function

```text
safe fn process_critical() {
    ...
}
```

`safe fn` berarti body function harus memenuhi aturan Safe Mode.

Semantik minimum:

- Safe verification berlaku pada body function;
- operasi unsafe tetap harus berada pada unsafe boundary yang eksplisit;
- `safe fn` tidak boleh digunakan untuk mengklaim bahwa input eksternal atau raw pointer otomatis valid;
- contract parameter/return tetap harus dapat dibuktikan sesuai type, ownership, lifetime, dan safety rules yang berlaku.

### Unsafe Function

```text
unsafe fn write_to(ptr, value) {
    -- safety:
    -- ptr harus valid dan writable
    -- allocation harus masih hidup

    *ptr = value
}
```

`unsafe fn` digunakan ketika caller mempunyai safety precondition yang tidak dapat dibuktikan penuh oleh compiler.

Boundary harus terlihat pada call site. Secara konseptual:

```text
unsafe {
    write_to(ptr, 42)
}
```

Aturan:

- function tetap di-parse, di-type-check, dan dianalisis sejauh mungkin;
- `unsafe fn` tidak berarti seluruh body bebas aturan;
- caller mengambil tanggung jawab untuk memenuhi safety precondition yang dinyatakan;
- safety precondition harus terdokumentasi dekat dengan function/API;
- ordinary caller tidak boleh memanggil unsafe function tanpa boundary yang diwajibkan language specification.

## Relationship With Existing Three Safety Modes

Syntax baru ini **bukan mode safety keempat** dan tidak menghapus mode mana pun.

Model tetap:

```text
BALANCED
├── default NolQu-L
├── strong safety where provable
├── high flexibility
├── high performance
└── predictable control

SAFE
├── maximum available safety verification
└── explicit via Safe Mode / safe boundary where applicable

UNSAFE
├── maximum low-level control
├── reduced safety guarantees
└── programmer responsibility becomes explicit
```

Ringkasnya:

```text
ordinary code / ordinary fn -> inherits mode; default = Balanced
safe { ... }                -> Safe for that block
unsafe { ... }              -> Unsafe for that block
safe fn ...                 -> Safe function body
unsafe fn ...               -> unsafe-precondition function boundary
```

Balanced tetap berada di tengah model NolQu-L Safety dan tetap menjadi default. `safe` dan `unsafe` hanya menambahkan boundary syntax yang eksplisit agar programmer dapat memilih scope dengan intent yang jelas.

## Grammar Integration Direction

Ketika parser Full NolQu-L sudah sampai pada tahap yang relevan, grammar dapat diperluas secara konseptual menjadi:

```text
function_decl := safety_modifier? "fn" ident "(" parameters? ")" block
safety_modifier := "safe" | "unsafe"

statement := ... | safety_block
safety_block := ("safe" | "unsafe") block
```

Ini merupakan arah grammar untuk Full NolQu-L, **bukan requirement bahwa B0/Core-0 saat ini harus langsung mendukung syntax tersebut**.

Jangan memperluas Stage 0 atau B0 hanya demi menerima syntax ini apabila generasi bootstrap berikutnya belum membutuhkannya.

## Required Test Direction

Ketika naming migration dan explicit safety syntax mulai diimplementasikan, tambahkan test tanpa menghapus regression test lama.

Minimum naming tests:

```text
nql-run-source
nqlc-compile-source
nql-extension-accepted
legacy-cli-alias-compatible
legacy-source-extension-compatible-if-retained
new-and-legacy-command-equivalence
```

Minimum safety syntax tests:

```text
balanced-remains-default
ordinary-fn-inherits-balanced-default
safe-block-enforces-safe-rules
unsafe-block-retains-compiler-diagnostics
safe-inside-unsafe-reenables-safe-verification
unsafe-inside-safe-is-explicit
safe-fn-enforces-safe-body
unsafe-fn-requires-unsafe-call-boundary
unsafe-fn-precondition-documented
nested-boundary-restores-enclosing-mode
```

Test names final boleh berbeda mengikuti convention repository. Yang wajib adalah behavior tersebut benar-benar dibuktikan sebelum syntax atau naming baru dianggap selesai.

## Non-Regression Rule

Bagian tambahan ini tidak boleh digunakan sebagai alasan untuk:

- menghapus Balanced;
- menjadikan Safe sebagai default;
- mengubah arti existing unsafe block;
- mengganti bootstrap artifact yang sudah PASS tanpa kebutuhan teknis;
- mengklaim migration CLI/source sudah selesai tanpa implementation dan test;
- mengganti nama formal bahasa menjadi `NolQu`;
- atau menulis ulang history/evidence lama hanya agar menggunakan naming baru.

Tujuan penambahan ini adalah memperjelas evolusi naming dan memberikan explicit Safe/Unsafe boundary syntax **sambil menjaga seluruh fondasi NolQu Major Development yang sudah ditetapkan**.

---

# IMPLEMENTATION UPDATE 2026-08-30 — CANONICAL CLI AND MCP CONTROL PLANE

Bagian ini mengubah target naming di atas menjadi interface repository yang
aktif dan teruji. Perubahan ini **tidak** mengubah status Full Compiler atau
self-hosting menjadi selesai.

## Canonical Interface Aktif

```text
Source canonical        : *.nql
Project manager / run   : nql; nolqul -> nql
Compiler CLI            : nqlc; nolqulc -> nqlc
Project manifest        : nql.toml
Project state/cache     : .nql/

Legacy source adapter   : *.nq (sementara, bukan nama command)
Removed commands        : nq, nqc, nolqu, nolquc
```

`nql` dan `nqlc` adalah file executable canonical, bukan symlink ke command
lama. Alias hanya berjalan dari nama panjang menuju nama pendek:
`nolqul -> nql` dan `nolqulc -> nqlc`. Instalasi menghapus sisa command
`nq`, `nqc`, `nolqu`, dan `nolquc`. Hal ini tidak mengklaim bahwa Reference
Compiler R0 telah berubah menjadi Full Compiler canonical.

`nql init` membuat `nql.toml`, `src/main.nql`, `.nql/`, dan entry `.nql/` pada
`.gitignore`. Build, check, run, test, clean, incremental hash cache, install,
dan uninstall menggunakan layout canonical. Source lama hanya dapat diproses
pada boundary adapter R0 yang masih menerima `.nq`; project canonical tidak
memiliki fallback manifest atau command lama.

Tool migrasi sekarang memakai file `.nql` sebagai source fisik. Alias source
lama hanya menunjuk menuju nama canonical, tidak sebaliknya:

```text
tools/nql_ir_dump_parser.nql                 source canonical
tools/nq_ir_dump_parser.nq       -> nql_ir_dump_parser.nql
tools/nql_ir_json_to_llvm.nql                source canonical
tools/nq_ir_json_to_llvm.nq      -> nql_ir_json_to_llvm.nql
```

## MCP NolQu-L

`tools/nolqu_mcp.py` menggunakan hanya `nql` dan `nqlc` untuk command
project/compiler; tidak ada fallback atau tool alias `nq_*`. Control plane MCP
menyediakan:

- capability `READ_ONLY`, `WRITE`, `BUILD`, `DESTRUCTIVE`, `REMOTE`, dan
  `UNSAFE_SHELL` beserta confirmation/environment boundary;
- structured command result, timeout, dan global stdout/stderr limiter;
- atomic edit dengan `fsync`, rename, cleanup, dan `expected_sha256`;
- unique temporary directory untuk benchmark dan migration verification;
- canonical bootstrap status/build/hash tools yang memisahkan R0 dari rantai
  Machine Foundation -> Stage 0 -> B0 -> C0;
- C0 probe, probe history, ELF/artifact inspection, dan generation comparison;
- stable/experimental/legacy metadata pada manifest tool;
- architecture resources `nolqu://...` dan workflow prompts resmi;
- local JSONL audit di `.nolqu-mcp/audit.jsonl`;
- `mcp_self_test` untuk root, path escape, command, timeout, atomic cleanup,
  audit, serta deteksi `nql`/`nqlc`.

`build_full_compiler`, `self_host_generation`, dan `verify_self_hosting` tetap
mengembalikan `NOT_IMPLEMENTED` bila artifact generasi yang disyaratkan belum
ada. MCP tidak boleh mempromosikan R0 menjadi tahap canonical.

## Migration Verification Status

Verifier migration sekarang membandingkan exit code, stdout bytes, stderr
bytes, output artifact, SHA-256, dan deterministic compiler rebuild. Artifact
x86_64 dijalankan melalui `qemu-x86_64` pada host non-x86_64.

Default generated-IR fixture untuk `nql_ir_dump_parser` dan
`nql_ir_json_to_llvm` sekarang menunjukkan:

```text
exit code parity     : PASS
stderr parity        : PASS
output file parity   : PASS
stdout parity        : PASS
deterministic binary : PASS
```

Perbaikan determinisme dilakukan dengan menghilangkan path temporary acak dari
metadata object NASM dan mengaktifkan mode reproducible ketika
`SOURCE_DATE_EPOCH` disediakan. Source NolQu-L juga menghasilkan success line
yang byte-identical dengan oracle Python ketika menulis artifact.

Python oracle dan source compatibility **belum layak dihapus** hanya dari satu
default fixture. Penghapusan baru boleh dilakukan setelah seluruh corpus test
yang ada berjalan melalui nama `.nql`, mencakup input invalid, dan test suite
tidak lagi merujuk implementasi Python sebagai runtime path.

## Verification Gate

Naming migration hanya boleh dianggap tetap hijau apabila seluruh gate berikut
lulus bersama:

```text
tests/mcp/test_nolqu_mcp.py
tests/compiler/toolchain_cli.sh
tests/compiler/run_tests.sh
make bootstrap-test
make release-check
```

Test corpus historis tidak boleh dihapus hanya karena command canonical sudah
aktif; yang dilarang adalah menghidupkan kembali command lama sebagai alias.

## Verification Result 2026-09-01

Seluruh gate di atas sudah dijalankan ulang setelah canonical CLI, MCP, dan
perbaikan compiler terakhir. Hasilnya:

```text
tests/compiler/toolchain_cli.sh :  46 PASS, 0 FAIL
tests/compiler/run_tests.sh     : 843 PASS, 0 FAIL
make bootstrap-test             : 218 PASS, 0 FAIL
make release-check              :   9 PASS, 0 FAIL
tests/mcp/test_nolqu_mcp.py      :  19 PASS, 0 FAIL
```

Angka tersebut adalah hitungan per gate dan tidak dijumlahkan sebagai jumlah
test unik karena beberapa gate menjalankan coverage yang beririsan. Tidak ada
pre-existing failure yang tersisa pada gate canonical ini.

MCP yang di-import dari source saat ini mendaftarkan 116 tools, 8 resources,
dan 5 prompts. Jumlah tersebut bukan target kualitas tersendiri; status tool,
capability boundary, structured result, verification, dan canonical bootstrap
awareness tetap menjadi contract utamanya.

## Closed Regression: Dynamic String Slot Drift

Full regression run menemukan kegagalan pada input JSON IR besar: nilai akhir
`i64 179` tidak ter-emisi. Penyebabnya bukan parser JSON, melainkan allocator
slot string pada Reference Compiler R0. Counter `str()` dan gabungan
`slice`/string concatenation dipakai sekaligus sebagai total layout BSS dan
cursor codegen. Operasi string yang muncul setelah `read_file` atau `arg_str`
menggeser layout akhir, sehingga generated code menunjuk slot dengan kelas
buffer yang salah. Input 31 KiB kemudian dapat ditulis ke buffer concatenation
4 KiB dan merusak slot argument/output di sebelahnya.

Allocator sekarang memakai invariant berikut:

```text
parser          -> hitung total its_cnt dan str_cat_cnt
codegen         -> gunakan cursor its_cur dan str_cat_cur
BSS layout      -> hanya bergantung pada total yang sudah final
read_file slot  -> setelah seluruh slot string dinamis
arg_str slot    -> setelah seluruh read_file slot
```

`str_cat_cnt` mencakup `IR_STR_CONCAT` dan `IR_STR_SLICE`, sedangkan cursor
codegen di-reset bersama cursor input/file/argument pada awal `cg_run`.
Reproducer 360 item IR dengan input 31.607 byte sekarang menghasilkan LLVM IR
lengkap yang memuat `i64 179`, menjaga output path tetap utuh, dan kemudian
melewati seluruh 845 test compiler.

Perbaikan ini menutup memory corruption yang terukur pada generated program.
Ini tidak mengubah status bootstrap: Machine Foundation, Stage 0, B0, dan C0
tetap PASS; Full Compiler canonical, self-host generation, dan verified
self-hosting tetap `NOT_IMPLEMENTED` sampai artifact serta parity generasinya
benar-benar tersedia.

## Work Unit Selesai: C0.17 Canonical Parser-Emitter Recognition

Probe C0.16 berhenti pada `while byte_load(3)` di baris 10 successor. C0.17
menangani tepat satu construct tersebut tanpa mempromosikan grammar `while`,
`write`, atau string umum. Matcher baru mempertahankan matcher return-emitter
C0.16, lalu memproses bentuk canonical berikut:

```text
while byte_load(3) {
write("<canonical parser ELF bytes>")
...
byte_store(3,0)
byte_store(2,0)
}
```

Payload parser tidak ditanam sebagai salinan rekursif di matcher. Runtime
membaca `p_filesz` RX dari ELF parser yang sedang berjalan di `0x400000`,
mendecode setiap literal source, dan membandingkan byte hasil decode langsung
dengan artifact tersebut. Canonical decoder menerima printable byte yang aman,
`\0`, `\n`, `\r`, `\t`, `\\`, `\"`, serta lowercase `\xHH`. Setiap chunk
selain chunk terakhir wajib tepat 255 byte. Header, newline, penutup literal,
tail clear, EOF, panjang artifact, dan setiap byte payload semuanya divalidasi
sebelum metadata sukses ditulis.

Metadata parser sekarang enam byte:

```text
return | no-input | input | parser | return-emitter | parser-emitter
```

Karena itu destination maksimum berubah dari 251 menjadi 250. Fixture batas
250 diterima dan 251 ditolak. Parser-bearing artifact memperoleh private BSS
8 KiB di `0x402000`; ordinary runtime artifact tetap memakai 256 byte di
`0x401000`. Refill tidak dapat melewati akhir mapping `0x404000`, file
descriptor input mencapai EOF sebelum sukses, dan mismatch pertama selalu
menuju diagnostic `runtime: invalid source` tanpa stdout artifact.

Gate parser-emitter membuktikan tiga jalur terpisah:

1. artifact parser direct menerima source yang memuat byte dirinya sendiri;
2. fixture metadata parser-emitter mengembalikan flag keenam;
3. mutasi ELF magic pertama dari `0x7f` menjadi `0x7e` keluar 1 dengan
   diagnostic byte-exact dan tanpa artifact.

Source C0.17 berukuran 214.941 byte. B0.7n mengukur kegagalan input arena dan
tabel patch byte-access; output artifact sebenarnya tetap di bawah bound lama.
B0.7o menaikkan hanya `INPUT_CAP` 196.608 -> 262.144 dan
`BYTE_ACCESS_CAP` 3.072 -> 4.096. `OUTPUT_CAP` tetap 393.216 byte. Gate exact
dan overflow mengunci input 262.144/262.145 serta patch 4.096/4.097 tanpa
perubahan grammar atau semantik codegen B0.

Artifact canonical C0.17:

```text
b0.seed             52.600 byte  6740118e4a386e0b56b42a7dc1bdd593f4fe74cf6c04788beca91ede6bd7351f
c0.seed            367.327 byte  e4b62412d08d6ec7681c3ccb7719d0d88d193f4d1925606acb0b60cd2bf9a3d0
c0-successor.seed    5.973 byte  c6c2da6e699ddeb5e18eec428e89f7c16b0dcbc679ac1d269e5747ecdca67f04
parser direct        2.238 byte  921daf9d67935138f6904f5f274678fd9a710775ea3dee0c53f2070a1b9eb5eb
```

Successor source sekarang 6.824 byte. Direct C0 dan successor menghasilkan
parser 2.238 byte yang identik. Materializer B0, C0, dan successor membangun
ulang artifact canonical secara byte-for-byte dan memverifikasi manifest hash.
Gate B0 serta C0 lengkap tetap hijau setelah promosi artifact.

Probe self-source generasi berikutnya sekarang melewati return-emitter dan
parser-emitter, lalu berhenti pada construct ketiga `while byte_load(2)` di
baris 23 dengan exit 1, stdout kosong, dan diagnostic exact. Itu adalah blocker
terukur C0.18. Full Compiler, self-host generation, dan verified self-hosting
tetap `NOT_IMPLEMENTED`; C0.17 tidak mengubah status ketiga milestone tersebut.

## Work Unit Selesai: C0.18 Canonical Input-Emitter Recognition

Probe C0.17 berhenti pada `while byte_load(2)` di baris 23 successor. C0.18
menangani tepat loop input-emitter canonical itu sebagai satu construct
bounded. Matcher tidak membuka grammar `while`, `write`, atau output umum.
Setelah matcher return-emitter dan parser-emitter lama sukses, ia memvalidasi
urutan lengkap berikut:

```text
while byte_load(2) {
write("<canonical input ELF bytes>")
byte_store(2,0)
output_write(0,1)
write("<constant ELF tail>")
}
```

Semua keyword, punctuation, newline, literal chunk, payload ELF, clear store,
output call, tail, dan penutup dibandingkan secara byte-exact. Metadata
`byte_parse_stmts` sekarang tujuh byte:

```text
return | no-input | input | parser | return-emitter | parser-emitter | input-emitter
```

Flag ketujuh baru ditulis setelah matcher lengkap sukses. Destination maksimum
berubah dari 250 menjadi 249; fixture 249 diterima dan 250 ditolak. Mutasi
payload pertama tetap menuju `runtime: invalid source`, exit 1, tanpa artifact
parsial. Parser-bearing artifact memakai private BSS 16 KiB di `0x402000`,
sedangkan ordinary runtime artifact tetap memakai 256 byte di `0x401000`.

Source input C0 sekarang menerima tepat 9.984 byte dan menolak byte ke-9.985.
Arena decoded literal menerima tepat 4.096 byte dan menolak byte ke-4.097.
Dispatcher parser berukuran 2.742 byte. Parser direct yang dihasilkannya
berukuran 3.216 byte dan menerima seluruh source successor canonical 8.295
byte dua kali dengan exit 0, stdout kosong, stderr kosong, serta hasil
deterministik.

Pertumbuhan source C0 menjadi 281.110 byte dan artifact C0 menjadi 488.170
byte melampaui tiga kapasitas B0.7o. B0.7p menaikkan hanya kapasitas bounded
yang terukur:

```text
INPUT_CAP       262.144 -> 327.680 byte
OUTPUT_CAP      393.216 -> 524.288 byte
BYTE_ACCESS_CAP   4.096 ->   5.120 entry
```

Gate menerima tepat 327.680 byte input dan 5.120 patch, menolak byte ke-327.681
serta patch ke-5.121 tanpa artifact, menerima output tepat 524.288 byte, lalu
menolak langkah emisi 18 byte berikutnya dengan `B0-CG-005`. Grammar dan
semantik codegen B0 tidak berubah.

Artifact canonical C0.18:

```text
b0.seed             52.600 byte  6f8a829c1aba2159d00d0e5b2cddfe6f58cd6db83aac3587f5c79928225351d9
c0.seed            488.170 byte  cf6f278ad1ea24c973b72717e8bba6dc5b2241e1c566a0cefb2a8b90d33ba91d
c0-successor.seed    8.113 byte  902c2e184509abb112d5377baf957558aad04b98110864e9ba1e0bce7f7ee709
parser direct        3.216 byte  836db9b7e711de4c33f36c8d295efe2eb7d3b945e511f0c1b74b267339804339
```

Source successor canonical memiliki 34 baris, 8.295 byte, dan SHA-256
`9c928c6b481e8897f2af381f5956790de123d976a12d875e7b73063a880b98e3`.
Materializer B0, C0, dan successor membangun ulang artifact canonical secara
byte-for-byte dan memverifikasi manifest hash.

Penerimaan penuh oleh parser direct adalah bukti **parse completeness untuk
grammar successor bounded**, bukan self-hosting. `c0-successor.seed` masih
menghasilkan target artifact subset, belum mengemisi compiler pengganti.
Karena tidak ada lagi source line yang ditolak parser direct, probe MCP kini
melaporkan `PARSED`, `parse_complete: true`, dan blocker
`full compiler emission` tanpa nomor baris fiktif. Full Compiler,
self-host generation, dan verified self-hosting tetap `NOT_IMPLEMENTED`.

## Work Unit Selesai: Canonical Command Ownership NolQu-L

Naming command tidak lagi memakai alias dari nama baru menuju executable lama.
Repository dan installer sekarang memiliki satu arah kepemilikan yang tegas:

```text
nql                 executable project manager
nolqul -> nql       alias nama panjang
nqlc                executable compiler driver
nolqulc -> nqlc     alias nama panjang
```

Command `nq`, `nqc`, `nolqu`, dan `nolquc` tidak tersedia di root maupun hasil
instalasi. Installer juga menghapus file stale dengan nama tersebut ketika
upgrade atau uninstall. Dengan demikian, bentuk lama berikut ditolak sebagai
arsitektur:

```text
nql  -> nq
nqlc -> nolquc
nqc  -> nolquc
```

MCP mengikuti boundary yang sama. Constant dan tool alias `NQ`/`nq_*` telah
dihapus; operasi project/compiler hanya mengeksekusi `nql` dan `nqlc`.
`tool_manifest` membuktikan bahwa command-tool lama tidak terdaftar. Setelah
pembersihan ini MCP memuat 116 tools, 8 resources, dan 5 prompts.

Nama internal R0 yang masih membawa identitas compiler lama juga sudah
dipindahkan ke pemilik canonical NolQu-L:

```text
src/nqlc.asm                 source driver R0
tools/nql_r0_adapter.sh      adapter pipeline R0
build/nqlc-r0                artifact compiler R0
```

Path `src/nolquc.asm`, `tools/nq_legacy.sh`, dan `build/nolquc` bukan lagi
dependency aktif. Installer membersihkan sisa path tersebut saat upgrade,
sedangkan test layout memastikan dependency baru tidak kembali mengarah ke
nama lama.

Arah alias source tool migrasi juga dibalik agar file canonical benar-benar
memiliki extension `.nql`:

```text
tools/nql_ir_dump_parser.nql                 source fisik
tools/nq_ir_dump_parser.nq       -> nql_ir_dump_parser.nql
tools/nql_ir_json_to_llvm.nql                source fisik
tools/nq_ir_json_to_llvm.nq      -> nql_ir_json_to_llvm.nql
```

Alias `.nq` tersebut hanya boundary sementara untuk corpus R0. Ia bukan command
publik dan tidak mengubah aturan bahwa source baru memakai `.nql`. Source
bootstrap yang nama serta byte-nya sudah dikunci manifest tetap tidak diganti
secara kosmetik.

Gate setelah perubahan ownership:

```text
tests/compiler/toolchain_cli.sh :  46 PASS, 0 FAIL
tests/compiler/run_tests.sh     : 843 PASS, 0 FAIL
make bootstrap-test             : 218 PASS, 0 FAIL
make release-check              :   9 PASS, 0 FAIL
tests/mcp/test_nolqu_mcp.py      :  19 PASS, 0 FAIL
```

Seluruh artifact dan hash C0.18 tetap identik karena perubahan ini hanya
menyentuh ownership CLI, penamaan internal driver R0, control plane MCP, source
tooling non-bootstrap, test, dan dokumentasi. Source serta artifact bootstrap
canonical tidak diubah. Blocker compiler berikutnya tetap **full compiler
emission**; tidak ada klaim self-hosting baru dari work unit naming ini.

## Work Unit Selesai: C0.19 Bounded Self-Image Generation

C0.18 sudah menerima seluruh source successor bounded, tetapi hanya berhenti
dengan parse sukses. C0.19 menambahkan tepat satu jalur emisi mesin untuk
membuktikan generasi compiler berikutnya tanpa berpura-pura bahwa Full
Compiler sudah tersedia.

Fixture marker canonical menulis `N` dan `L` pada byte-memory offset 7 dan 8,
kemudian menjalankan `input_read(32,96)` dan `byte_parse_stmts(32,0)`. Setelah
ketujuh byte metadata parser lengkap, routine mesin 229 byte:

1. memblokir `SIGPIPE`,
2. membaca ukuran RX dirinya dari ELF `p_filesz` di `0x400060`,
3. menulis image mulai `0x400000` dengan complete-write loop,
4. mengulang short write,
5. dan keluar 74 dengan `runtime: output_write failed` pada kegagalan.

Source tanpa marker atau metadata lengkap tetap memakai perilaku parser
bounded lama. General `write`, loop bebas, linker, dan compiler grammar tidak
dibuka oleh perubahan ini.

Gate canonical membangun generation B dari fixture tersebut menggunakan
`c0.seed`. Generation B menerima source successor 8.919 byte dan menghasilkan
generation C yang identik. Generation C menerima source sama dan menghasilkan
generation D yang juga identik. Ketiganya 3.459 byte dengan SHA-256:

```text
5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

Ini sengaja disebut **bounded self-image generation**, bukan self-hosting.
Generation B berasal dari fixture marker kecil, bukan hasil kompilasi source
compiler general yang sama. Successor source juga merupakan konstruksi exact
yang dikenali dispatcher, belum bahasa compiler penuh.

Pertumbuhan ini menemukan regresi layout nyata. `c0-successor.seed` membesar
menjadi 8.631 byte sehingga RX melewati alamat private BSS lama `0x402000`.
Kernel kemudian memetakan RW di atas tail executable dan literal output rusak.
Parser-bearing artifact sekarang menempatkan BSS 16 KiB di `0x403000`, sampai
`0x407000`. Ordinary runtime artifact tetap di `0x401000`. Test membaca program
header ELF dan menolak setiap layout dengan `RX end > RW start`.

Dua batas lain dinaikkan hanya setelah successor baru membuktikannya:

```text
token lexer       240 -> 248
operation record   32 -> 40
```

Enam tabel token tetap berjarak 256 byte. Empat puluh operation record memakai
arena disjoint `10000..10319` untuk kind, tiga argumen, patch output/error, dan
patch literal. Gate menerima record ke-40 dan menolak ke-41; token overflow
ditolak tepat pada `input:123:3` tanpa artifact parsial.

Identitas canonical C0.19:

```text
b0.seed             52.600 byte  6f8a829c1aba2159d00d0e5b2cddfe6f58cd6db83aac3587f5c79928225351d9
c0.seed            516.795 byte  3b8959468cfdfb3ea7a11b498241f0d0e9b63f090d3102b48b53e8ecf9b2f0b7
c0-successor.seed    8.631 byte  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
self-image direct    3.459 byte  5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

Source `compiler.nq` berukuran 296.992 byte dengan SHA-256
`12806bae3275791a148f7c2c3da8c504bdc27eda9d3440d3b1adba31c097b5ab`.
Source successor berjumlah 35 baris, 8.919 byte, dan SHA-256
`00ff07d5868c12fa0315469eed9966d6c8c835d6c54c1d56dfc0e12dde8536b2`.
Materializer B0 -> C0 dan C0 -> successor menghasilkan ulang kedua seed secara
byte-for-byte dan memverifikasi hash sebelum rename atomic.

MCP sekarang mengenali `C0.19`, menjalankan generation B -> C -> D di temporary
directory unik, dan hanya melaporkan
`BOUNDED_GENERATION_VERIFIED` jika exit code, stderr, byte artifact, dan hash
semuanya cocok. `build_full_compiler`, formal self-host generation, dan
verified self-hosting tetap `NOT_IMPLEMENTED`.

Gate yang selesai untuk work unit ini:

```text
tests/bootstrap/core_compiler_c0.sh  PASS
make bootstrap-test                  PASS
tests/mcp/test_nolqu_mcp.py          20 PASS, 0 FAIL
```

Blocker berikutnya bukan lagi parsing source atau menyalin image bounded.
Pekerjaan berikutnya adalah **general Full Compiler implementation** yang
menghasilkan compiler dari source compiler canonical yang sama. Hanya setelah
itu generasi self-host dan verifikasi reproducible boleh dipromosikan.

## Work Unit Selesai: C0.20 Indirect Byte Load And Source Scan

C0.19 dapat membaca byte-memory hanya dari offset yang dibekukan di source.
Itu cukup untuk matcher exact, tetapi belum cukup untuk lexer Full Compiler
yang harus berjalan mengikuti posisi source runtime. C0.20 menambahkan satu
primitive kecil tanpa memperluas B0:

```text
byte_load_at(pointer_slot, destination)
```

Kedua operand adalah offset u8 compile-time. Artifact yang dihasilkan
menjalankan semantik berikut:

```text
memory[destination] = memory[memory[pointer_slot]]
```

Karena pointer disimpan sebagai satu byte, effective address selalu berada
dalam byte-memory runtime `0..255`. Lowering x86_64-nya tetap transparan dan
fixed-size 20 byte: satu RIP-relative load untuk pointer, satu load melalui
alamat BSS runtime, lalu satu RIP-relative store untuk hasil. Jalur ordinary
tetap memakai BSS `0x401000`; perhitungan yang sama juga menghormati base
`0x403000` pada artifact parser-bearing. Tidak ada heap, libc, LLVM, Python,
assembler, linker, atau runtime host baru.

Pengembangan dilakukan dengan gate merah terlebih dahulu. C0.19 menolak
fixture baru secara located pada:

```text
input:4:5: error[C0-001]: invalid C0 program
```

Setelah lexer, parser-state, operation record, dan codegen kind 12 ditambah,
gate membuktikan tiga hal:

1. indirect load mencapai offset terakhir 255 dan menghasilkan exit 90;
2. program scan membaca source ke offset 32, menaikkan pointer saat runtime,
   berhenti pada sentinel nol BSS, dan menulis ulang input byte-for-byte;
3. destination 256 ditolak pada `input:2:21`, exit 1, stderr exact, dan stdout
   tetap kosong.

Program scan diuji dengan input `fn main(){ LF return 42 } LF`; hasil stdout
identik termasuk newline terakhir. Loop selesai tanpa crash atau hang. Semua
I/O menggunakan fd proses yang diwariskan dan primitive tidak membuka resource
baru, sehingga tidak ada descriptor tambahan yang perlu dilepas.

Artifact lama yang tidak memakai `byte_load_at` tetap identik. Secara khusus,
`c0-successor.seed` dan bounded generations C0.19 tidak berubah:

```text
b0.seed             52.600 byte  6f8a829c1aba2159d00d0e5b2cddfe6f58cd6db83aac3587f5c79928225351d9
c0.seed            522.058 byte  aa17cd154619ccf4ba8a20ef2984fa948ebca347e1bd774c45507b875c63593a
c0-successor.seed    8.631 byte  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
self-image direct    3.459 byte  5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

Source `bootstrap/compiler/c0/compiler.nq` sekarang 300.264 byte dengan
SHA-256
`84177febcf7e946e0b3230cdb1ae9bc2966ff59ecc6127981e626594e67838d5`.
B0.7p menghasilkan `c0.seed` yang sama dalam dua build deterministik. Ukuran
522.058 byte masih berada 2.230 byte di bawah `OUTPUT_CAP` 524.288, sehingga
tidak ada capacity bridge B0 tanpa bukti kebutuhan.

MCP sekarang mengenali C0.20 dan tidak sekadar membaca nomor milestone. Probe
menjalankan direct indirect-load, source-scan byte-exact, lalu bounded
generation B -> C -> D. Status suksesnya adalah
`INDIRECT_LOAD_AND_BOUNDED_GENERATION_VERIFIED`; Full Compiler, formal
self-hosting, dan verified `nqlc` tetap `NOT_IMPLEMENTED`.

Gate work unit:

```text
tests/bootstrap/core_compiler_c0.sh  PASS
tests/mcp/test_nolqu_mcp.py          PASS
```

Blocker berikutnya sekarang lebih sempit dan terukur: lexer source-driven
memerlukan **indirect byte store** untuk mengisi token table dan patch table
berdasarkan index runtime. Work unit berikutnya harus menambahkan primitive
tersebut dengan bound u8, deterministic codegen, located rejection, dan gate
read-after-write nyata sebelum lexer Full Compiler mulai diimplementasikan.

## Work Unit Selesai: B0.7q Capacity Bridge dan C0.21 Indirect Byte Store

C0.20 sudah dapat membaca source melalui pointer runtime, tetapi belum dapat
mengisi token table atau patch table pada index yang baru diketahui saat
program berjalan. Work unit C0.21 menambahkan pasangan mutasinya:

```text
byte_store_at(pointer_slot, source_slot)
```

Kedua operand tetap offset u8 compile-time. Semantik runtime-nya eksplisit:

```text
memory[memory[pointer_slot]] = memory[source_slot]
```

Pointer satu byte menjaga effective address di dalam byte-memory `0..255`.
Lowering x86_64 berukuran tetap 20 byte: source byte dimuat secara
RIP-relative, pointer byte dimuat ke register index, lalu source byte disimpan
melalui base BSS runtime. Perhitungan base mengikuti artifact biasa di
`0x401000` maupun artifact parser-bearing di `0x403000`. Primitive ini tidak
menambah heap, runtime host, atau dependency toolchain eksternal.

TDD dimulai dari C0.20. Fixture baru ditolak secara located sebelum
implementasi:

```text
input:4:5: error[C0-001]: invalid C0 program
```

Setelah keyword, parser state, operation kind 13, dan codegen ditambahkan,
gate membuktikan:

1. pointer runtime dapat menyimpan ke offset terakhir 255 dan program exit 91;
2. input `NQL!` dibaca pada offset 32, disalin ke offset 160 melalui pointer
   dinamis, lalu ditulis kembali byte-for-byte ke stdout;
3. source slot 256 ditolak pada `input:2:22`, exit 1, stderr exact, stdout
   kosong, dan tidak ada artifact parsial;
4. seluruh artifact lama yang tidak memakai primitive baru tetap identik,
   termasuk `c0-successor.seed` dan bounded generations B, C, dan D.

Pertumbuhan source memunculkan blocker predecessor yang terukur. B0.7p
menolak build C0.21 dengan:

```text
input.nql:2:5: error[B0-CG-005]: generated executable would exceed B0 output limit
```

Build pengukuran berkapasitas lebih besar menunjukkan output yang dibutuhkan
adalah 527.503 byte. Source 303.722 byte masih di bawah `INPUT_CAP` 327.680 dan
jumlah patch tetap di bawah `BYTE_ACCESS_CAP` 5.120. Karena itu B0.7q hanya
menaikkan `OUTPUT_CAP` dari 524.288 menjadi 589.824 byte. Gate batas menerima
artifact terbesar yang dapat direpresentasikan fixture langkah 18 byte,
589.808 byte, lalu menolak langkah berikutnya pada 589.826 byte dengan
`B0-CG-005` tanpa output parsial. Grammar dan semantik B0 tidak berubah.

Identitas canonical setelah promosi:

```text
b0 compiler.nql0  106.103 byte  772fe2335e468888f6a2585300c0245160912b0e03451aa67f91ba4d4581ed0d
b0.seed             52.600 byte  4eea6da6f805d1bf07bb878bcde52e0b1d129899af25d839582d74fa4e030ad6
c0 compiler.nq     303.722 byte  430c44c95270801936edce7112dd180aa63373abcd818e9ff405c0b4b1b1d96c
c0.seed            527.503 byte  b6405b1ffd7f3581c07e831dfed54f009eaff92f18cde6a417ed1f1f19a91668
c0-successor.seed    8.631 byte  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
self-image direct    3.459 byte  5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

Probe MCP C0.21 sekarang memverifikasi indirect load, source scan, indirect
store, source-table copy, dan bounded generation parity. Status suksesnya
`INDIRECT_STORE_AND_BOUNDED_GENERATION_VERIFIED`; probe tidak mengubah status
Full Compiler atau self-hosting.

Gate work unit:

```text
tests/bootstrap/bootstrap_compiler_b0.sh  PASS
tests/bootstrap/core_compiler_c0.sh       PASS
tests/mcp/test_nolqu_mcp.py               PASS
```

Blocker berikutnya adalah **source-driven tokenization** nyata. Work unit
berikut harus memakai `byte_load_at` dan `byte_store_at` untuk menghasilkan
token kind, offset, dan length dari source runtime dengan progress serta bound
yang teruji. Full Compiler, self-hosting `nqlc`, dan verified `nqlc` tetap
`NOT_IMPLEMENTED` sampai compiler general dibangun dari source canonical yang
sama dan melewati perbandingan multi-generasi.

## Work Unit Selesai: C0.22 Bounded Source Byte Token Table

C0.21 membuktikan primitive indirect read/write, tetapi bukti itu masih berupa
scan dan copy byte. C0.22 menambahkan program bootstrap canonical yang benar-
benar membangun record token dari source runtime:

```text
bootstrap/compiler/c0/source_byte_tokenizer.nql
```

Program ini sengaja tidak diimplementasikan sebagai intrinsic compiler. Source
NolQu-L tersebut hanya memakai `input_read`, `byte_assert_range`,
`byte_load_at`, `byte_store_at`, byte assignment, satu loop bounded, dan
`output_write` yang sudah dibuktikan pada milestone sebelumnya. Dengan begitu
kemampuan baru berasal dari komposisi bahasa C0, bukan blob mesin baru.

Format output tetap dan dapat diaudit:

```text
byte 0       jumlah token, 0..16
bytes 1..48  enam belas record [kind, offset, length]
```

Untuk layer pertama, `kind` adalah byte source nonzero asli, `offset` adalah
posisi zero-based, dan `length` selalu satu. Record yang tidak terpakai tetap
nol. Whitespace serta punctuation sengaja dipertahankan; C0.22 tidak mengklaim
klasifikasi keyword, identifier, integer, string, atau penggabungan karakter.

Layout runtime tidak overlap:

```text
0..5      scratch pointer/current byte/count
64..80    source dan satu byte overflow guard
127       token count output
128..175  16 x 3-byte token records
```

Program meminta 17 byte dari fd 0 tetapi hanya menerima maksimal 16 byte
source. Byte ke-17 berada di slot guard 80 dan wajib nol. Input lebih panjang
mencapai diagnostic exact `runtime: invalid source`, exit 1, dan stdout kosong.
Input kosong, parsial, dan tepat 16 byte selalu berhenti; pointer source tidak
dapat wrap sebelum loop selesai. Semua I/O memakai descriptor proses yang
diwariskan dan tidak ada resource baru yang perlu dilepas.

TDD dimulai dengan gate source yang belum ada:

```text
FAIL c0-source-byte-tokenizer-source
```

Setelah program ditambahkan, gate membuktikan output sample `fn 42+\n`
byte-for-byte, seluruh 16 record pada input batas, zero padding pada input
parsial, output kosong-terstruktur 49 byte, overflow diagnostic, determinisme,
ELF64 x86_64 static tanpa interpreter, dan stack non-executable.

Identitas canonical C0.22:

```text
compiler.nq              303.722 byte  0a00c222f8d34a66f5c67994f0a13066a92898e0dd742e9d5349a3d811edf179
c0.seed                  527.503 byte  b6405b1ffd7f3581c07e831dfed54f009eaff92f18cde6a417ed1f1f19a91668
source_byte_tokenizer.nql    688 byte  ee19754193edf4064763eadb967cb71aa1e145ef75a9ae2018abd77305b62a4c
tokenizer artifact           900 byte  85107865350e99c4181092960d4fb7e611f1011d4a4d66b173c678fd92ffd4ab
```

`compiler.nq` hanya berubah pada header milestone C0.22. B0.7q menghasilkan
ulang `c0.seed` yang tetap byte-identik, sehingga tidak ada capacity bridge atau
perubahan semantik compiler tanpa bukti kebutuhan. Source tokenizer sendiri
masuk ke bootstrap suite melalui `c0_source_byte_tokenizer.sh`.

Probe MCP C0.22 mengompilasi source tokenizer, memverifikasi record sample dan
overflow, lalu tetap menjalankan indirect load/store serta bounded generation
B -> C -> D. Status suksesnya:

```text
SOURCE_BYTE_TOKENS_AND_BOUNDED_GENERATION_VERIFIED
```

Gate work unit:

```text
tests/bootstrap/c0_source_byte_tokenizer.sh  PASS
make bootstrap-test                            PASS
tests/mcp/test_nolqu_mcp.py                   23 PASS, 0 FAIL
```

Blocker berikutnya adalah **lexical token classification and coalescing**.
Byte records harus digabung menjadi identifier dan decimal integer, whitespace
harus dilewati secara bounded, punctuation harus mendapat kind stabil, dan
setiap kegagalan harus tetap located serta tidak menghasilkan output parsial.
Source-driven parser, Full Compiler, self-hosting `nqlc`, dan verified `nqlc`
tetap `NOT_IMPLEMENTED`.

## Work Unit Selesai: C0.23 Bounded ASCII Lexical Classification

C0.22 menghasilkan record source satu-per-byte, tetapi `kind` masih memuat
byte mentah. C0.23 menambahkan satu primitive runtime yang kecil dan eksplisit:

```text
byte_classify_ascii(source_slot, destination)
```

Kedua operand adalah offset u8 compile-time. Primitive membaca satu byte dari
`memory[source_slot]`, memetakan byte tersebut melalui tabel ASCII tetap, dan
baru menulis kind ke `memory[destination]` setelah input terbukti valid. Kind
yang sekarang stabil adalah:

```text
1       whitespace: SP, TAB, LF, CR
4       identifier byte: A..Z, a..z, _
5       decimal digit: 0..9
10..20  ( ) { } ; + * - / = ,
```

Byte ASCII lain, DEL, dan byte `>=128` mencapai handler bersama
`runtime: invalid source`, exit 1. Jalur gagal tidak memutasi destination dan
program tokenizer tidak menghasilkan stdout parsial. Lowering x86_64 tetap
bounded 170 byte: direct load, pemeriksaan non-ASCII, lookup pada tabel 128
byte di segment RX, pemeriksaan kind nol, direct store, dan satu patch `rel32`
ke handler invalid-source. Tidak ada heap, descriptor baru, libc, assembler,
linker, Python, atau LLVM yang masuk ke rantai canonical.

`source_byte_tokenizer.nql` sekarang memanggil primitive tersebut sebelum
menulis setiap record. Bentuk output masih 49 byte dan tetap mudah diaudit:

```text
byte 0       jumlah record, 0..16
bytes 1..48  enam belas record [classified_kind, offset, 1]
```

Milestone ini sengaja belum menggabungkan identifier atau integer dan belum
menghapus whitespace. Pemisahan itu menjaga klaim sesuai bukti: C0.23 selesai
untuk klasifikasi, sedangkan coalescing tetap work unit berikutnya.

TDD dimulai dengan source tokenizer yang memakai primitive baru terhadap seed
C0.22. Gate gagal located sebelum implementasi:

```text
input:13:9: error[C0-001]: invalid C0 program
FAIL c0-source-byte-tokenizer-build
```

Setelah keyword kind 31, parser state 79..83, operation kind 14, metadata,
codegen, dan patch handler ditambahkan, gate membuktikan seluruh kelas huruf,
underscore, digit, empat whitespace, sebelas punctuation, input kosong,
batas 16 byte, overflow byte ke-17, byte tidak dikenal, non-ASCII, dan operand
compile-time 256. Operand invalid dilaporkan tepat di `input:2:28`; runtime
invalid selalu exit 1 dengan stderr exact dan stdout kosong.

Pertumbuhan tetap berada dalam B0.7q sehingga tidak ada capacity bridge baru:

```text
compiler.nq              313.990 byte  1b06384ef7a529f97d02f9f91d1792068c8596c9f88ebd5be78b4bb53a72ddd7
c0.seed                  545.270 byte  263d818d5f6c79f6bb2eeb259e3df5e46b004077f8437041c103a1b4e7f48fd8
source_byte_tokenizer.nql    743 byte  e8204b27f1149330cb7624e6a29532f36427e12f7171ccb2e269996b0b6b3eb8
tokenizer artifact         1.077 byte  d658dc3cfe5eb944aa5912f528892a5b1fde271be33f8be23c8d74ca1d0833cf
c0-successor.seed           8.631 byte  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
```

Source 313.990 byte masih di bawah `INPUT_CAP` 327.680 dan artifact 545.270
byte masih di bawah `OUTPUT_CAP` 589.824. Successor dan bounded generations
lama tetap byte-identik. Probe MCP C0.23 menambahkan validasi classified token
sample serta penolakan byte tidak dikenal, kemudian tetap memverifikasi
indirect load/store dan generasi B -> C -> D. Status suksesnya:

```text
SOURCE_ASCII_CLASSIFICATION_AND_BOUNDED_GENERATION_VERIFIED
```

Gate work unit:

```text
tests/bootstrap/c0_source_byte_tokenizer.sh  PASS
tests/bootstrap/core_compiler_c0.sh          PASS
tests/mcp/test_nolqu_mcp.py                   24 PASS, 0 FAIL
```

Blocker berikutnya adalah **lexical token coalescing and whitespace elision**.
Source canonical harus menggabungkan run identifier dan decimal integer,
melewati whitespace tanpa record, mempertahankan punctuation satu-byte,
menjaga progress/batas 16 byte, dan gagal tanpa output parsial. Source-driven
parser, Full Compiler, self-hosting `nqlc`, dan verified `nqlc` tetap
`NOT_IMPLEMENTED`.

## Work Unit Selesai: B0.7r Capacity Bridge dan C0.24 Lexical Token Coalescing

C0.24 menyelesaikan work unit lexical C0.23 dengan primitive runtime bounded:

```text
byte_token_push(kind_slot, offset_slot, table_base)
```

Ketiga operand adalah offset u8 compile-time. `kind_slot` menunjuk hasil
klasifikasi, `offset_slot` menunjuk posisi source zero-based, dan `table_base`
menunjuk count byte pertama dari tabel berikut:

```text
byte 0       jumlah token, 0..16
bytes 1..48  enam belas record [kind, offset, length]
```

Primitive menerapkan aturan lexical kecil yang eksplisit:

- kind 1 (whitespace) tidak menghasilkan record;
- kind 4 (identifier) bergabung dengan identifier sebelumnya jika kontinu;
- kind 5 (decimal digit) bergabung dengan identifier atau integer sebelumnya
  jika kontinu;
- kind 10..20 (punctuation Core-0) selalu menghasilkan record satu byte;
- record hanya digabung jika `previous_offset + previous_length` sama dengan
  offset source saat ini;
- token ke-17, length yang wrap, kind invalid, atau tabel yang tidak muat
  mencapai `runtime: invalid source`, exit 1, tanpa stdout parsial.

Karena tabel selalu memerlukan 49 byte dalam memory 256 byte, `table_base`
dibatasi sampai 207. Lowering x86_64 berukuran tetap 162 byte dan tidak memakai
heap, file descriptor baru, libc, assembler, linker, Python, atau LLVM. Source
`source_byte_tokenizer.nql` tetap membatasi input ke 16 byte, tetapi jumlah
token kini juga diuji secara independen: 16 punctuation diterima dan
punctuation ke-17 ditolak.

TDD pertama kali berhenti tepat pada primitive yang belum dikenal:

```text
input:11:9: error[C0-001]: invalid C0 program
FAIL c0-source-byte-tokenizer-build
```

Implementasi awal kemudian membuka bug addressing nyata: indeks record
sebelumnya memakai `3 * (count - 1)` langsung dari `table_base`, sehingga byte
header count terbaca sebagai kind. Rumus diperbaiki menjadi `3 * count - 2`,
yakni offset kind record sebelumnya setelah melewati header satu byte. Encoding
pengganti dijaga tetap lima byte agar seluruh branch relatif berikutnya tidak
bergeser. Gate batas `12a a12` membuktikan integer berhenti sebelum identifier,
sedangkan digit setelah identifier tetap tergabung sebagai identifier.

Pertumbuhan compiler melewati cap patch B0.7q. Pengukuran predecessor
menunjukkan 5.165 patch gagal dan 5.166 patch berhasil. B0.7r karena itu
menaikkan hanya `BYTE_ACCESS_CAP` dari 5.120 ke 5.376, menyisakan margin bounded
tanpa mengubah `INPUT_CAP` 327.680 byte atau `OUTPUT_CAP` 589.824 byte. Gate
exact menerima 5.376 patch dan menolak patch ke-5.377 tanpa artifact parsial.

Identitas canonical setelah promosi:

```text
b0 compiler.nql0       106.108 byte  4c115dfa566f1368d2a35371163709af4d5802ab6c2bfa488f685a982493ef8c
b0.seed                  52.600 byte  7b71089df23551ea55444f132834046cc619a93cf45ad78f285d64d615ce495c
c0 compiler.nq          327.359 byte  d464e590875adbf66ce2973106504e0c7403a0ce1806bf4b80d189129f39f00b
c0.seed                 568.889 byte  c2b6d8138867123861eac0a34eaebfda2d44633d097f44329ac6a612edd30745
source_byte_tokenizer.nql   427 byte  39e90287b6a592b257c977dba8413c1ac965547d41c5025b9290b92fcd0ab5f5
tokenizer artifact        1.083 byte  132372400176567973f1f288e3ebbf8fd872abc6e65fbc08b1612c88ca03908f
c0-successor.seed          8.631 byte  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
self-image direct          3.459 byte  5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

Probe MCP C0.24 memverifikasi indirect load/store, ASCII classification,
whitespace elision, coalescing identifier/integer, punctuation, batas token,
dan bounded generation parity. Status suksesnya:

```text
SOURCE_TOKEN_COALESCING_AND_BOUNDED_GENERATION_VERIFIED
```

Gate work unit:

```text
tests/bootstrap/bootstrap_compiler_b0.sh      PASS
tests/bootstrap/c0_source_byte_tokenizer.sh   PASS
tests/bootstrap/core_compiler_c0.sh            PASS
tests/mcp/test_nolqu_mcp.py                    25 PASS, 0 FAIL
```

Blocker berikutnya adalah **source-driven parser over coalesced tokens**.
Parser berikut harus membaca record kind/offset/length ini secara bounded,
mempertahankan lokasi source, menjamin progress, dan gagal tanpa artifact
parsial. Full Compiler canonical, self-hosting `nqlc`, dan verified `nqlc`
tetap `NOT_IMPLEMENTED`; bounded self-image C0.19 tidak mengubah status itu.

## Work Unit Selesai: C0.25 General Bounded Expression Parser

Klasifikasi aktual work unit ini:

```text
Requested Mode        : Major Development / continuation
Actual Update Class   : Major Development
Risk Level            : medium-high
Primary Scope         : canonical C0 parser foundation
Affected Subsystems   : C0 token storage, source parser, bootstrap tests, MCP,
                        canonical hashes, architecture documentation
Public Contract Impact: none; Full Compiler dan CLI publik belum dipromosikan
Bootstrap Impact      : canonical C0 identity berubah, topology tetap
Compatibility Impact  : internal pre-release bootstrap contract
Version Impact        : milestone C0.24 -> C0.25; public release tidak berubah
RFC / ADR Required    : no; mengikuti bootstrap progression yang sudah disetujui
Release Blocking      : yes; Full Compiler dan self-hosting belum ada
```

C0.25 tidak menambah primitive parser mesin. Sebaliknya, program canonical baru
`bootstrap/compiler/c0/source_token_parser.nql` dibangun oleh `c0.seed` dan
memakai hanya operasi byte-memory, indirect load, assertion, loop, dan output
yang sudah tersedia. Inputnya adalah tabel coalesced C0.24 berukuran tetap 49
byte. Grammar executable pertama adalah:

```text
expression      := primary (binary-operator primary)*
primary         := identifier | decimal-integer
binary-operator := "+" | "*" | "-" | "/"
```

Parser menerima satu sampai lima belas token bermakna dalam bound lexer 16
token. Setiap iterasi wajib mengonsumsi tepat satu operator dan satu primary.
Setelah operator, sisa token diperiksa sebelum counter dikurangi lagi; input
dengan jumlah token genap karena itu berhenti dengan error, bukan wrap ke 255
atau loop tanpa akhir. Kind, offset, dan length setiap record yang benar-benar
dikonsumsi juga divalidasi. Empty stream, operator awal/akhir, dua operator,
dua primary, punctuation yang belum didukung, count invalid, offset invalid,
dan length nol semuanya exit 1 dengan stderr exact:

```text
runtime: invalid source
```

Tidak ada stdout parsial pada jalur gagal. Jalur sukses menghasilkan 53 byte:

```text
0..48  tabel token asli, byte-for-byte
49     jumlah root node: 1
50     kind root: 1 (flat infix expression)
51     indeks token pertama: 0
52     jumlah token expression
```

Output ini sengaja disebut **flat CST root**, bukan AST precedence. Semua lokasi
lexical dipertahankan, tetapi grouping, associativity tree, keyword resolution,
statement, function, module, semantic analysis, dan emission Full Compiler
belum diklaim.

Source parser yang lebih besar mengungkap batas struktural lama pada token
source ke-249. Perbaikannya bukan primitive baru: enam tabel token internal C0
diperlebar dari stride 256 menjadi stride 512 dan bound checked dinaikkan dari
248 ke 512 token:

```text
kind        16000..16511
value       16512..17023
start low   17024..17535
start high  17536..18047
length low  18048..18559
length high 18560..19071
```

Arena decoded literal 4.096 byte dipindah ke `20000..24095` agar tetap
disjoint. Source bound 9.984 byte dan operation cap 40 tidak berubah. Gate
boundary membangun program valid tepat 512 token dan menolak token ke-513 di
`input:1:524` tanpa artifact. Tidak diperlukan bridge B0 baru karena source,
artifact, dan patch count C0 tetap berada di batas B0.7r.

Identitas canonical C0.25:

```text
b0.seed                    52.600 byte  7b71089df23551ea55444f132834046cc619a93cf45ad78f285d64d615ce495c
c0 compiler.nq            327.359 byte  1b75e7eb24ac27e5ff401efe5a67544b2deb7def2c4438e12f35ff28e99e813b
c0.seed                   568.889 byte  312fc0cab67b4c366cc7f5f17546619926654bdb326afcbe7bfb1c310a70266b
source_token_parser.nql     1.356 byte  f8f44089cc28d61847105f4cb267fcf92e23d2e430a8878137d278f8f85ffa8f
parser artifact             1.360 byte  f03e85e4966b2439f3fbeccd22bc1b57c0dd7feaa1638bb76ce7ebc6bc4fc357
tokenizer artifact           1.083 byte  132372400176567973f1f288e3ebbf8fd872abc6e65fbc08b1612c88ca03908f
c0-successor.seed            8.631 byte  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
```

MCP `run_c0_probe` sekarang mengenali C0.25 dan memverifikasi kapasitas 512,
penolakan token 513, build parser deterministik, expression valid, input
trailing-operator invalid, serta parity bounded generation yang sudah ada.
Status suksesnya:

```text
SOURCE_EXPRESSION_PARSER_AND_BOUNDED_GENERATION_VERIFIED
```

Gate work unit:

```text
tests/bootstrap/c0_source_token_parser.sh    PASS
tests/bootstrap/c0_source_byte_tokenizer.sh  PASS
tests/bootstrap/core_compiler_c0.sh          PASS
tests/mcp/test_nolqu_mcp.py                   26 PASS, 0 FAIL
```

Blocker berikutnya adalah **source-driven statement grammar and precedence
tree construction**. C0.26 harus menentukan format node bounded yang stabil,
menghasilkan tree dengan precedence `*`/`/` di atas `+`/`-`, menyelesaikan
keyword dari lexeme source, dan menerima envelope function serta statement
minimum dengan progress dan error atomik. Setelah kontrak itu teruji, emission
Full Compiler `nqlc` dapat dimulai. Full Compiler, self-hosting `nqlc`, dan
verified `nqlc` tetap `NOT_IMPLEMENTED`.

---

## Work Unit Selesai: C0.26 Source Frontend And Precedence AST

```text
Requested Mode        : lanjutkan parser source-driven menuju Full Compiler
Actual Update Class   : Minor Development
Risk Level            : medium
Primary Scope         : source lexer, parser, AST berindeks
Affected Subsystems   : C0 frontend, bootstrap artifact/gate, MCP, dokumentasi
Public Contract Impact: tidak mengubah CLI nql/nqlc atau ABI program
Bootstrap Impact      : komponen C0 tambahan dibangun langsung oleh B0
Compatibility Impact  : emitter dan proof C0.25 dipertahankan byte-identik
Version Impact        : milestone komponen C0.26; VERSION/CHANNEL tidak berubah
RFC / ADR Required    : keputusan dan kontrak internal di C0/FRONTEND.md
Release Blocking      : semua gate baseline dan frontend wajib hijau
Reason                : pisahkan source-to-AST dari emitter bounded lama;
                        jangan menambah intrinsic parser khusus lagi
```

Baseline sebelum perubahan sesi ini: `make test` exit 0, **1.068 PASS, 0 FAIL,
0 SKIP**. Suite MCP terpisah: **26 test, semuanya PASS**. Tidak ada baseline
failure. Warning dependency Pydantic tentang `lifespan` sudah ada sebelum
perubahan; bukan error compiler dan bukan regresi sesi ini.

### Implementasi

`bootstrap/compiler/c0/frontend.nql` kini melakukan keseluruhan pekerjaan
source-to-AST, bukan mengolah fixture atau menambah primitive bounded baru:

- baca fd 0 hingga EOF, termasuk short reads, dengan overflow byte eksplisit;
- lexer source-driven, full-lexeme keyword resolution, identifier ASCII,
  decimal, whitespace LF/CRLF, serta komentar `#` dan `//`;
- parser `fn main()` berisi banyak `let`, assignment, dan final `return`;
- tree nyata untuk `+ - * /`, precedence dan left associativity, serta grouping
  bertingkat tanpa rekursi pada machine stack;
- node berindeks dengan span lexeme, left/right operand dan link statement;
- diagnostic `input:line:col: error[C0P-NNN]` dengan penyebab dan saran;
- invalid input exit 1 tanpa stdout parsial; syscall failure exit 74;
- NQAF/1 deterministik, memuat source asli dan hanya node yang digunakan.

Batas storage: 8.192 source byte, 512 token, 512 node. Test mencapai batas
source/token serta mencakup 252 tingkat grouping, 24 binding, dan semua
kombinasi pasangan operator. Batas 512 node adalah guard defensif; grammar
saat ini hanya dapat menghasilkan paling banyak 507 node pada 512 token,
sehingga jalur node-overflow belum dapat diuji melalui source valid. Storage
ada di arena byte 65.536 byte milik runtime B0, dengan region terpisah untuk
source/token/node/stack. Tidak ada heap atau descriptor baru yang dibuka.
Referensi memory map dan grammar lengkap: `bootstrap/compiler/c0/FRONTEND.md`.

Keputusan provenance penting: frontend ini **dibangun B0**, sebagaimana C0
emitter juga dibangun B0. Bahasa runtime yang dihasilkan C0.25 masih terlalu
sempit untuk menulis frontend ini secara terbaca; memperluasnya lewat banyak
intrinsic parser khusus tidak dilanjutkan. Tidak ada Python, R0, NASM, LLVM,
atau linker host yang mengompilasi frontend canonical. Python hanya menjadi
oracle test; qemu hanya adapter eksekusi x86_64 pada host AArch64.

Ini bukan klaim C0 sudah mengompilasi frontend-nya sendiri. Artifact
`c0.seed` tetap versi emitter C0.25; komponen tambahan adalah C0.26 frontend.
Full Compiler, self-hosting `nqlc`, dan verified `nqlc` tetap `NOT_IMPLEMENTED`.

```text
frontend.nql SHA-256
05a28e2dfc3432d2774aa86955dddb225c8b427bf2ce7eb1b776b3d9fc43adc6

c0-frontend.seed: 58.039 byte, SHA-256
2eb0ec1b447b14e623fd873ef486137c334216cdd201313fefe771c56c71d325

c0.seed (tidak berubah)
312fc0cab67b4c366cc7f5f17546619926654bdb326afcbe7bfb1c310a70266b
```

`materialize-frontend.sh` membangun lewat B0, memeriksa hash, lalu mengganti
output secara atomik. Output lama tetap utuh pada compile/hash failure.
Temporary unik, cleanup, dua build concurrent, dan penolakan output yang
menimpa source/predecessor/hash/builder diuji.

MCP menambah `build_c0_frontend` dan `run_c0_frontend_probe`, keduanya capability
`BUILD` dan status `experimental`. Catalog artifact memasukkan `c0_frontend`,
dengan `built_by=B0`. `run_c0_probe` menjalankan bukti emitter/generation lama
dan frontend, lalu melaporkan `SOURCE_AST_AND_BOUNDED_GENERATION_VERIFIED` hanya
jika keduanya lulus. `c0_version=C0.25` dan `frontend_version=C0.26` dibedakan,
bukan menyamarkan pergantian artifact compiler.

### Bukti Dan Batas

```text
bash tests/bootstrap/c0_frontend.sh                  12 tests PASS
tests/mcp/test_nolqu_mcp.py                          30 tests PASS
fresh-process MCP run_c0_probe                      PASS
make test sesudah integrasi                         1.069 PASS, 0 FAIL, 0 SKIP
make release-check                                 9 PASS
git diff --check                                   PASS
```

Semua command di atas exit 0. Gate frontend terbaru juga dijalankan terpisah
setelah penambahan mutation/truncation coverage. MCP ELF inspector pada path
artifact baru memverifikasi tanpa interpreter dan tanpa shared library;
hash canonical diverifikasi oleh materializer/gate. Proses MCP yang sudah
berjalan perlu dimuat ulang untuk mendaftarkan tool baru; probe lengkap sudah
diverifikasi dari proses baru, bukan menganggap daemon lama otomatis reload.

Review independen read-only pada frontend, kontrak AST, materializer, dan
oracle test tidak menemukan cacat. Review tersebut juga melaporkan 310
perbandingan grammar/AST/token-count tambahan yang cocok; probe tambahan
ini bukan bagian suite permanen dan tidak dimasukkan ke jumlah test di atas.
Coverage yang masih terbatas: write failure setelah stdout parsial, interupsi
signal pada materializer, dan kegagalan rename belum memiliki fault-injection
test khusus. Hal ini bukan bukti adanya bug, tetapi juga tidak diklaim sudah
terverifikasi oleh uji closed-stdout atau compile/hash failure.

Bug implementasi baru yang ditemukan test: semicolon setelah `let` tidak
dikonsumsi saat commit statement. Sudah diperbaiki dan matrix parser kembali
hijau. `/dev/full` tidak dapat diakses pada host ini; test write failure memakai
closed stdout tanpa skip, dan tetap memeriksa status 74 serta diagnostic.
Uji negatif probe gabungan juga menemukan `parse_complete`/exit code masih
mewarisi keberhasilan emitter ketika frontend gagal. Pelaporan gabungan sudah
diperbaiki; bukti emitter tersimpan terpisah dan kegagalan frontend tidak dapat
memajukan blocker atau menghasilkan status sukses.

Temuan lama di luar frontend: helper C0.25 `source_token_parser.nql` menerima
input tabel yang terpotong karena runtime zero-padding. Repro empat byte
`01 04 00 03` menghasilkan output 53 byte. Helper itu dipertahankan sebagai
proof historical dengan kontrak input lengkap dari tokenizer, **bukan**
validator stream arbitrer. Tidak dipakai oleh frontend C0.26. Perbaikannya
pada jalur aktif adalah baca source sampai EOF dan validasi lengkap di
frontend baru; framing helper historical sendiri masih terbatas dan tidak
diklaim selesai. Tidak ada file lama yang dihapus atau compiler penuh yang
dipromosikan.

Blocker berikutnya: **semantic/name/type resolution dan codegen dari AST**,
diikuti function calls dan structured control flow. Pembagian frontend ini
memberikan batas tahap yang dapat diuji, bukan mengganti backend dengan LLVM
atau memasukkan R0 ke canonical chain.

---

## Work Unit Selesai: C0.27 AST Backend And Checked Scalar ELF

```text
Requested Mode        : lanjutkan pengembangan canonical dari AST C0.26
Actual Update Class   : Minor Development
Risk Level            : high (validasi AST dan emitter machine code baru)
Primary Scope         : local resolution, scalar i64 semantics, ELF codegen
Affected Subsystems   : C0 backend, wrapper/gate bootstrap, MCP
Public Contract Impact: komponen experimental; bukan pengganti CLI nqlc
Bootstrap Impact      : backend.nql dibangun langsung oleh B0
Compatibility Impact  : source/artifact C0.25 dan C0.26 tidak berubah
Version Impact        : C0.27 komponen backend; VERSION/CHANNEL tidak berubah
RFC / ADR Required    : kontrak dan keputusan di C0/BACKEND.md
Release Blocking      : runtime, malformed AST, hash, regression dan review
```

Baseline sebelum perubahan: `make test` exit 0, **1.069 PASS, 0 FAIL, 0 SKIP**;
suite MCP terpisah **30 test PASS**. Tidak ada pre-existing failure. Warning
Pydantic `lifespan` tetap merupakan warning dependency yang sudah ada.

### Implementasi Dan Dampak

`bootstrap/compiler/c0/backend.nql` menerima NQAF/1 sampai EOF, memeriksa
framing, kapasitas, node/lexeme, ownership dan urutan statement, lalu
menyelesaikan nama secara exact dalam satu flat scope. `let` mutable baru
terlihat setelah initializer; duplicate, unknown, forward/self reference
ditolak. Decimal dibatasi signed i64. `+ - * /` dieksekusi oleh machine code
hasil kompilasi, bukan dievaluasi oleh script host.

Hasilnya ELF64 x86_64 Linux, RX load segment dan stack RW non-executable,
tanpa interpreter/libc/shared library. Setiap nilai memakai slot 8 byte pada
frame tetap 4096 byte. Overflow aritmetika, pembagian nol dan `INT64_MIN/-1`
menghasilkan diagnostic lokasi operator dengan exit 70; error IR/semantic
exit 1 tanpa stdout, error I/O exit 74. Arena compiler 65536 byte, tanpa heap
atau descriptor baru. Ini bukti untuk komponen ini, bukan klaim audit memory
seluruh repository atau pembuktian formal bebas bug.

`materialize-backend.sh` membangun melalui B0 dan memeriksa pin sebelum
publikasi atomik. `compile-source.sh input.nql output` menghubungkan frontend
ke backend melalui temporary unik; syntax failure menghentikan pipeline
sebelum backend. Output lama dan input dilindungi pada jalur gagal.

MCP menambah `build_c0_backend` dan `run_c0_backend_probe` sebagai experimental
`BUILD`, serta artifact `c0_backend`. Probe gabungan memisahkan versi emitter,
frontend dan backend; hanya memajukan blocker bila ketiganya lulus. Status
Full Compiler dan self-hosting tetap `NOT_IMPLEMENTED`. Definisi tool baru
memerlukan reload proses MCP; daemon yang sudah berjalan tidak hot-reload.

```text
backend.nql SHA-256
4534673b31a56d1f45ea83e584180271d6661095dcce4c4030db9aaf77e481ea

c0-backend.seed: 80.665 byte, SHA-256
b51e42c8d36dd4fa069dd9c198e8026da51c68a4bb21269f2d00058b939aa54a
```

Tidak ada Python, assembler, linker, R0 atau LLVM dalam build canonical.
Python hanya oracle test, shell mengatur file/proses, QEMU hanya adapter
eksekusi x86_64 pada host AArch64. Artifact baru bukan compiler yang membangun
dirinya sendiri; B0 tetap predecessor kedua komponen.

### Perbaikan Dari Review

Review independen menemukan bahwa referensi child yang selalu mundur belum
cukup: record expression dapat dipindah melewati assignment sehingga membaca
nilai lama; binding yang dipindah juga dapat melewati duplicate-name check.
Tiga regresi permanen dibuat dan dibuktikan gagal pada artifact awal.

Validator sekarang menuntut subtree contiguous dalam postorder kiri-ke-kanan
dan setiap statement mulai persis setelah statement sebelumnya. Tabel awal
subtree dipakai ulang sebagai tabel slot setelah validasi, tanpa tambahan
arena. AST hasil frontend lama tetap diterima; reordered AST ditolak dengan
`C0B-002`, termasuk pemindahan dua subtree yang membalik urutan runtime fault.

Review ulang independen tidak menemukan masalah pada perbaikan: subtree
berurutan, batas statement, masked reads, dan pemakaian ulang tabel slot
diperiksa. Probe tambahan menguji binding dengan ID di atas 255 dan 20 child
di luar batas; ini bukti tambahan, bukan penambahan jumlah test permanen.

### Verifikasi

Gate backend final: **15 test PASS**, mencakup precedence/operator pairs,
mutable local, 126 deklarasi pada batas token, kapasitas source/grouping,
i64/overflow/division, ELF layout, truncation/mutation/permutation AST,
short reads, partial-output EPIPE, closed descriptors, dan wrapper atomik.
Fault injection materializer membuktikan concurrent build, hash/compile
failure, output alias, rename failure, SIGTERM saat publikasi dan cleanup.
Inspector MCP memverifikasi artifact final tanpa interpreter/shared library;
hash canonical diverifikasi secara terpisah oleh materializer dan gate.

Probe MCP gabungan artifact final lulus dengan status
`SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED` (exit 0), memisahkan
`c0_version=C0.25`, `frontend_version=C0.26`, dan `backend_version=C0.27`.

```text
make test (artifact final)                    1.070 PASS, 0 FAIL, 0 SKIP
bash tests/bootstrap/c0_backend.sh            15 tests PASS
tests/mcp/test_nolqu_mcp.py                   33 tests PASS
make release-check                           9 PASS
git diff --check                             PASS
```

Semua command exit 0. Gate backend termasuk dalam `make test`; angka test
unit tidak dijumlahkan ulang ke jumlah baris PASS suite. Seluruh 1.069 kasus
PASS baseline masih ditemukan dalam hasil final, tanpa kasus yang hilang.
Bug ordering dari review sudah diperbaiki; tidak ada regresi baseline tersisa.

Blocker berikutnya: **function calls, structured control flow, dan coverage
source compiler**. NQAF saat ini hanya satu function/flat scope/scalar i64;
general type inference, strings, parameter, modules dan self-compilation
belum diimplementasikan. Helper token C0.25 dengan framing terbatas tetap
proof historical dan tidak digunakan pipeline aktif. Tidak ada file legacy
yang dihapus, tidak ada perubahan ABI publik, dan tidak ada promosi `nqlc`.

---

## Work Unit Selesai: C0.28 Structured Control Flow And Lexical Scope

Requested mode: melanjutkan pengembangan dari blocker C0.27. Actual class:
Major Development, high risk pada lexer/parser, AST, scope resolution dan
branch codegen. Kontrak/ADR serta checklist implementasi berada di
`bootstrap/compiler/c0/CONTROL_FLOW.md`. Tidak ada perubahan VERSION/CHANNEL,
ABI publik, dependency canonical, atau promosi Full Compiler.
Klasifikasi dinaikkan dari perkiraan awal Minor karena perubahan grammar,
format NQAF/2 dan lexical scope membutuhkan koordinasi frontend/backend.
Matriks kompatibilitas, resource bounds, migrasi dan rollback terbatas pada
pasangan komponen ini dicatat dalam ADR; bukan perubahan versi major publik.

### Baseline Dan Urutan

Sebelum edit, log baseline `make test` mencatat **1.070 PASS, 0 FAIL, 0 SKIP**;
suite MCP **33 test PASS**. Tidak ada pre-existing failure. Warning dependency
Pydantic `lifespan` tetap ada. Pemeriksaan dilakukan pada workspace yang sudah
berisi perubahan; file yang tidak terkait tidak di-revert.

Urutan: test baru yang gagal pada seed lama; parser/precedence dan delimiter;
validasi topology/nesting; lexical scope; direct branch codegen; parity scalar,
pin/rebuild atomik; gate bootstrap/MCP dan regresi penuh. Tidak ada tambahan
intrinsic parser khusus pada C0.25, LLVM, assembler, atau linker host.

### Implementasi

`frontend.nql` sekarang mengonsumsi source `if expr { ... } else { ... }` dan
`while expr { ... }` secara struktural, termasuk nesting campuran sampai 64
body. Lexer mengenali `< <= > >= == !=` sebagai token utuh; precedence
aritmetika lebih tinggi daripada relational, kemudian equality. Semua operator
left-associative. Kondisi i64 memakai zero=false, nonzero=true; hasil compare
adalah 0/1. Tidak ada shortcut eval atau constant-folding host.

NQAF/2 mempertahankan record 16 byte dan source asli. Expression tetap tree
postorder contiguous; statement stream menambah guard/delimiter bertipe,
bukan alamat jump mentah. Backend menolak nesting silang, else ganda, child
di luar batas, operand lintas statement, delimiter malformed dan versi format
yang tidak sesuai. Parser dan backend memeriksa batas nesting secara mandiri.

`backend.nql` menyelesaikan nama melalui symbol stack scope. Local terlihat
setelah initializer, inner scope boleh shadow outer local, duplicate pada
scope yang sama ditolak. Keluar blok atau memasuki else memulihkan binding
enclosing. Body loop menginisialisasi local ulang pada setiap iterasi; assignment
dapat mengubah local enclosing. Cabang yang tidak dijalankan tetap diperiksa
secara semantik.

Codegen langsung memakai signed `cmp/setcc`, guard `jz rel32`, forward fixup
untuk else/end, dan backward `jmp rel32` ke awal seluruh expression kondisi
while. Return di dalam blok langsung keluar dari main. Cabang yang dilewati
tidak menjalankan arithmetic fault. Checked arithmetic/diagnostic lokasi
operator tetap berlaku pada iterasi yang benar-benar dieksekusi.

Resource tetap bounded: 8.192 byte source, 512 token/node, arena compiler
65.536 byte, frame executable 4.096 byte, tanpa heap atau descriptor baru.
Stack kontrol berindeks direuse untuk validasi, scope dan fixup; literal table
direuse untuk code-start hanya setelah immediate selesai diemit. Loop compiler
berprogres atau gagal; loop program pengguna tetap dapat sengaja tidak selesai.

### Compatibility Dan Bukti Komponen

20 source scalar yang mencakup semua pasangan operator aritmetika tetap
byte-identik pada **AST dan ELF** terhadap seed C0.26/C0.27 sebelum upgrade.
Keyword `if`, `else`, `while` sekarang reserved; pemakaiannya sebagai nama
local lama adalah satu perubahan kompatibilitas experimental yang disengaja.
Nama dengan prefix keyword, misalnya `while_count`, tetap didukung.

Gate frontend mempertahankan 12 test lama dan menambah pemeriksaan AST/syntax
control flow. Gate backend mempertahankan 15 test lama dan menjalankan suite
`test_c0_control_flow.py`: nesting, perbandingan signed, scope/shadowing, return,
unselected faults, lokasi runtime fault, AST mutation, batas 64/65 yang
independen, binding ID di atas 255, parity scalar, determinisme, dan publikasi
wrapper atomik. Error header NQAF/2 tanpa extension sempat berubah kode;
test lama mendeteksinya dan kode `C0B-001` telah dipulihkan.

MCP melaporkan frontend/backend C0.28 terpisah dari emitter C0.25. Flag
`control_flow_verified` dan `lexical_scope_verified` hanya true ketika gate
backend lulus. Probe gabungan tetap menolak promosi jika satu tahap gagal.
Daemon MCP lama perlu reload untuk memakai definisi terbaru; verifikasi sesi
ini mengimpor modul baru dalam proses terpisah tanpa menghentikan daemon user.

```text
frontend.nql SHA-256
e9046061c0bb3559590b302e8c2364b8be4535d470c133921ece9f73a7bdd9be
c0-frontend.seed: 68.160 byte
8db70d3d3deca966cdba25bee8676ca7091a7c0d44b04936bc131bf55f43c811

backend.nql SHA-256
cf7c49a9d452be83739a36e50169aecd48e569e6afb40eccc988ea584b0c507f
c0-backend.seed: 93.974 byte
a28cac84c547f5ee3f000cfabb5d79340d227f12dea7b25893c7664d820e0c65
```

B0/C0.25 dan bounded successor tidak berubah. Frontend/backend C0.26/C0.27
diupgrade pada path komponen yang sama; pin baru berasal dari dua rebuild B0,
bukan hasil modifikasi ELF manual.

### Verifikasi Akhir

```text
make test                                  1.071 PASS, 0 FAIL, 0 SKIP
test_c0_frontend.py                         12 tests PASS
test_c0_backend.py                          15 tests PASS
test_c0_control_flow.py                     13 tests PASS
tests/mcp/test_nolqu_mcp.py                  33 tests PASS
make release-check                          9 PASS
git diff --check                           PASS
```

Semua command selesai dengan exit 0. Test komponen sudah termasuk dalam gate
`make test`, bukan tambahan untuk dijumlahkan ulang ke jumlah baris PASS.
Perbandingan nama test mempertahankan seluruh 1.070 baris PASS baseline;
tambahan satu baris gate adalah `c0-control-flow`. Tidak ada regresi tersisa.

Probe MCP fresh-process lulus dengan
`SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED`, exit 0,
`c0_version=C0.25`, `frontend_version=C0.28`, `backend_version=C0.28`.
`control_flow_verified=true`, `lexical_scope_verified=true`;
Full Compiler/self-hosting tetap false. Probe menjalankan gate frontend dan
backend, bukan sekadar membaca metadata versi atau hash.

Review independen read-only tidak menemukan masalah pada empat file utama
(frontend, backend, ADR dan test control flow). Probe reviewer memeriksa
nesting/scope/branch targets, AST maksimum, dan alamat malformed tanpa crash
atau output error parsial. Ini bukti pengujian terbatas, bukan verifikasi formal
seluruh compiler. Tidak ditemukan bug di luar scope yang perlu ditunda.
Tidak ada perubahan legacy LLVM bootstrap, commit, merge, atau penghapusan
file lama dalam work unit ini.

Berikutnya: pemanggilan function, parameter, runtime byte/stream operations
dan coverage source compiler. Masih satu `fn main()` dan i64; belum ada
break/continue, else-if shorthand, all-path return analysis, module, type
inference umum, atau self-compilation. Main tetap membutuhkan return akhir.
Ini batas subset yang terdokumentasi, bukan klaim Full Compiler.

---

## Work Unit C0.29: Function Dan Native Calls

### Baseline Dan Keputusan

Work unit ini melanjutkan C0.28, bukan mengulang implementasinya. Baseline
sebelum perubahan adalah **1.071 PASS** (`/tmp/nql-c029-baseline.log`) dan
**33 test MCP PASS**. Tidak ada failure baseline yang diketahui. Interupsi
sesi menyisakan source kandidat; seed canonical belum dipromosikan saat
pekerjaan dilanjutkan pada 2026-09-09.

Klasifikasi: **Major Development**, risiko tinggi pada lexer/parser, kontrak
AST, scope function, ABI stack dan codegen. Tidak ada perubahan versi release
publik, trust root, B0 atau emitter C0.25. Keputusan dan rencana terukur ada di
`bootstrap/compiler/c0/FUNCTIONS.md`. Beban implementasi berada di frontend
dan backend NolQu-L yang dibangun B0, tanpa compiler/assembler/linker host.

Subset yang dituju: function i64 bernama, 0..6 parameter mutable, calls
forward/nested/recursive, satu `main()` tanpa parameter dalam urutan definisi
apa pun, scope terpisah per function, dan evaluasi argumen kiri-ke-kanan.
NQAF/3 menambah marker function/parameter/end serta node call/argument-prefix.
NQAF/1 dan NQAF/2 tetap dipertahankan untuk program lama tanpa calls.

### Bukti Awal Implementasi

Test-first `test_forward_calls` gagal pada seed C0.28 di koma `sum(20,22)`
dengan C0P-001, exit 1, tanpa output parsial. Frontend kandidat kemudian
lulus test syntax dan kontrak AST function, termasuk call bersarang.
Seluruh 13 test control flow lulus dengan frontend kandidat dan backend lama.
Corpus control flow C0.28 menghasilkan AST dan ELF byte-identik.

Empat kasus penolakan frontend lama dipindahkan secara eksplisit ke pengujian
semantik backend: function tanpa main, main berparameter, callee tidak dikenal,
dan duplicate main. Syntax-nya sekarang valid, tetapi executable-nya tetap
harus ditolak. Ini perluasan grammar yang disengaja, bukan penghapusan test
invalid. Pemeriksaan materializer masih menolak hash kandidat sampai pin
baru terbukti dan dipromosikan bersama backend.

MCP Astra Project Forge dipakai untuk checkpoint/evidence proyek;
MCP NolQu tetap menyediakan operasi khusus bootstrap. Keduanya bukan bagian
dari build compiler canonical. Integrasi MCP menambah flag function/parameter
yang fail-closed dan lulus 33 unit test. Status akhir work unit ditentukan
oleh gate runtime, rebuild deterministic, regression dan probe, bukan metadata.

### Penyelesaian Implementasi Dan Review

Frontend dan backend C0.29 sekarang terintegrasi: function i64 bernama dengan
0..6 parameter mutable, scope terpisah, forward/nested/self/mutual-recursive
calls, evaluasi argumen kiri-ke-kanan dan native stack frame. Return memulihkan
frame serta budget kedalaman. Maksimum 64 function aktif termasuk main;
kelebihan kedalaman menghasilkan C0R-003 di lokasi source, exit 70. Kegagalan
menulis diagnostic menghasilkan exit 74. Tidak ada heap atau FD baru.

Review menemukan satu bug kandidat frontend: panjang nama callee u16 disimpan
dalam scratch satu byte. Nama 257 byte dapat salah memanggil function satu byte
dan menghasilkan 1 alih-alih 42. Test RED membuktikan masalah sebelum perbaikan;
scratch sekarang menyimpan kedua byte. Test panjang 255/256/257 pada arity 0/1/6,
exact-name lookup, lokasi diagnostic dan kegagalan write kini lulus. Seluruh
17 test function lulus; review ulang frontend dan review backend tidak menyisakan
temuan konkret. Probe reviewer juga memeriksa malformed AST, batas node tinggi,
enam register argumen, caller-live values dan predecessor byte parity.

Saat melanjutkan sesi, baseline ulang sempat berhenti di pin frontend lama
(225 PASS sebelum berhenti). Ini **pre-existing incomplete integration**:
source sudah C0.29 tetapi seed masih C0.28, bukan regresi baru dari perubahan
lanjutan. Suite R0 yang belum tercapai dijalankan terpisah dan lulus 843 PASS.
Pin tidak dilemahkan; kedua kandidat dibangun dua kali dengan B0, dibandingkan
byte-for-byte, lalu dimaterialisasi bersama setelah test kandidat lulus.

| Artifact canonical | Bytes | SHA-256 |
| --- | --- | --- |
| `c0-frontend.seed` | 81576 | `2e231661ca4da4a8a80da22cefad2b602cb09fb67d4af717bfe34262aa286875` |
| `c0-backend.seed` | 125197 | `ac091d9fd9bc695dbbdf8c9254f05ee1e8012d383839679de241949e8281bbcf` |

Machine Foundation, Stage 0, B0, emitter C0.25 dan bounded-successor tidak
berubah. MCP `verify_bootstrap_hashes` memverifikasi semua tujuh artifact;
inspeksi backend membuktikan ELF x86_64 static, tanpa interpreter/dependency
host dan dengan non-executable stack. Corpus empat source C0.28 tetap memiliki
AST dan ELF byte-identik. Build canonical tidak menggunakan LLVM atau linker
host. Tool Python untuk test/MCP bukan compiler canonical.

Pengujian berjalan melalui QEMU x86_64 pada host ARM64/proot. Fixture broken
pipe tidak konsisten pada lingkungan ini dan `/dev/full` tidak dapat diakses;
test kegagalan diagnostic memakai FD tertutup/read-only yang deterministik,
tanpa skip. Ini batas lingkungan pengujian, bukan klaim audit resource seluruh
project. Review tidak menyisakan temuan correctness C0.29; legacy bootstrap
tidak diubah dan tidak ada file lama dihapus.

### Verifikasi Akhir C0.29

Work unit ditutup pada **2026-09-10** dengan source dan seed yang sama seperti
hasil review. Rerun penuh menyelesaikan gate berikut:

```text
make test                                 1.072 PASS, 0 FAIL, 0 SKIP
test_c0_functions.py                          17 tests PASS (termasuk make test)
tests/mcp/test_nolqu_mcp.py                    33 tests PASS
make release-check                            9 PASS
verify_bootstrap_hashes                        7 artifact PASS
git diff --check                              PASS
```

Semua gate command di atas selesai exit 0. Perbandingan multiset nama PASS
mempertahankan seluruh 1.071 baris baseline, dengan satu gate tambahan
`c0-functions`. Test komponen tidak dijumlahkan dua kali ke angka agregat.
Tidak ada regresi tersisa dalam suite tersebut. Warning startup Pydantic
tentang annotation `lifespan` sudah ada pada baseline MCP dan masih muncul;
33 test tetap lulus, tanpa perubahan dependency untuk menyembunyikan warning.

Log lengkap ada di `/tmp/nql-c029-completion-test.log`; hasil terstruktur di
`/tmp/nql-c029-completion-result.json` mencatat `ok=true`, `exit_code=0`,
`timed_out=false`, durasi 1.242.016 ms, dan tidak ada output terpotong. Log run
sebelum interupsi juga sudah mencapai 1.072 PASS, tetapi exit code sesi itu
tidak lagi tersedia; rerun ini memastikan bukti completion tidak bergantung
pada perkiraan dari log. Log MCP/release masing-masing memakai suffix
`completion-mcp.log` dan `completion-release.log` pada prefix yang sama.

Probe fresh-process di `/tmp/nql-c029-final-probe.json` lulus dengan
`SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED`, exit 0,
`c0_version=C0.25`, dan frontend/backend `C0.29`.
`function_calls_verified=true` serta `parameter_scope_verified=true`;
Full Compiler/self-hosting tetap false. MCP canonical status juga membaca
kedua pin C0.29 dengan benar. Checklist `FUNCTIONS.md` kini selesai.

### Blocker Berikutnya Yang Terukur

Pada 2026-09-10, frontend canonical diuji langsung dengan seluruh source kedua
komponen. `frontend.nql` berukuran 50.458 byte dan ditolak dengan C0P-002 di
`input:167:32`; `backend.nql` berukuran 79.883 byte dan ditolak di
`input:157:17`. Keduanya exit 1 tanpa AST karena batas source masih 8.192 byte.
Perintah reproduksi dan kontrak lanjut dicatat di `FUNCTIONS.md`. Kenaikan
kapasitas saja belum cukup: runtime byte/stream operations, call statement,
serta kapasitas token/node masih diperlukan untuk source compiler.
Source backend juga melampaui rentang offset u16 (65.535 byte) pada NQAF/1..3.
Perlu kontrak span lebih lebar yang versioned atau compilation unit bounded,
serta layout arena baru; bukan sekadar menaikkan konstanta batas input.

README dan roadmap yang masih menunjuk C0.15 atau meminta pembangunan B0
dimulai ulang sudah diselaraskan. Status yang benar tetap: komponen C0.29
PASS, Full Compiler dan self-hosting **NOT_IMPLEMENTED**. Tidak ada perubahan
`VERSION`, `CHANNEL`, atau semantik publik R0.

---

# Work Unit C0.30: Runtime Byte Dan Stream

Status: **VERIFIED pada 2026-10-12**. Pekerjaan yang terinterupsi pada September
dituntaskan melalui audit state disk dan verifikasi ulang. C0.29 sudah selesai;
tidak dibangun ulang sebagai milestone baru. Source dan pin C0.30 yang sudah
ada dipertahankan; sesi Oktober memperbaiki integrasi, test dan dokumentasinya.
Kontrak, alternatif, ABI, batas, serta urutan test-first tercatat di
`bootstrap/compiler/c0/RUNTIME_IO.md`.

Baseline sebelum perubahan source: `make test` melalui fresh-process MCP
`_run_result(timeout=3600)`, **1.072 PASS, 0 FAIL, 0 SKIP**, exit 0.
Hasil terstruktur `/tmp/nql-c030-baseline-result.json` menyimpan exit code dan
durasi 1.338.375 ms; log lengkap `/tmp/nql-c030-baseline.log`.
Unittest MCP: **33 PASS**, exit 0. Warning Pydantic `lifespan` tetap merupakan
warning yang sudah ada, bukan kegagalan baru.

Scope work unit ini:

1. Call statement berbasis source, termasuk call berurutan dan di dalam block;
   NQAF/4 kind 44 memiliki call expression-nya sendiri, bukan arbitrary expression
   statement yang diam-diam dibuang.
2. Runtime `byte_load`, `byte_store`, `input_read`, `output_write`, `error_write`
   dengan arena eksplisit 65.536 byte, pemeriksaan range, syscall Linux langsung,
   serta diagnostic lokasi dan exit code. User function tetap dapat memakai
   nama tersebut tanpa kehilangan perilaku C0.29.
3. Rebuild deterministik kedua komponen dengan B0, parity predecessor, review,
   bootstrap/MCP gates dan regression suite sebelum promosi pin.

RED sudah terbukti pada seed C0.29: call statement ditolak C0P-008, byte-load
expression ditolak C0B-008. Checkpoint September sempat mencatat pin masih C0.29;
audit disk Oktober menemukan kedua komponen dan pin sudah C0.30. Gate materializer
asli kini lulus tanpa mengurangi pemeriksaan hash. Rebuild ganda oleh B0,
byte parity kandidat/pin dan fingerprint corpus predecessor semuanya lulus.

Runtime memakai arena stack zero-initialized 65.536 byte yang terpisah dari frame
function. Range/index diperiksa sebelum akses; empty range tidak melakukan syscall.
`input_read` mengembalikan short count/EOF, sedangkan `output_write` dan
`error_write` menyelesaikan seluruh range. Fault range C0R-004 exit 70;
fault read/write C0R-005/006 exit 74 dengan lokasi callee. Diagnostic yang gagal
ditulis exit 74 tanpa rekursi. Tidak ada heap, FD baru, libc atau linker host.

### Baseline Dan Verifikasi Akhir Oktober

| Gate | Sebelum edit Oktober | Setelah edit |
| --- | --- | --- |
| `make -k test` | 1.073 PASS, 0 FAIL/SKIP, exit 0 | 1.073 PASS, 0 FAIL/SKIP, exit 0 |
| MCP (`.venv-mcp/bin/python -m unittest discover -s tests/mcp -v`) | 33 PASS | 37 PASS, exit 0 |
| `make release-check` | 8 PASS, 1 pre-existing FAIL | 9 PASS, exit 0 |
| Combined C0 probe | runtime/call statements terverifikasi | source dan pin tetap identik |

Multiset nama PASS baseline dan rerun akhir identik. Tambahan gate terhadap
baseline September adalah `c0-runtime-io`; kasus unittest di dalamnya tidak
dihitung dua kali. Log: `/tmp/nql-c030-resume-baseline-20261012.log`,
`/tmp/nql-c030-final-tests-20261012.log` dan `/tmp/nql-c030-final-mcp-20261012.log`.

Pre-existing failure release-check dan resource MCP berasal dari rujukan ke
`NOLQU_MAJOR_DEVELOPMENT.md` yang sudah tidak ada. Rujukan sekarang memakai
dokumen revisi ini; obsolete fallback tidak dihidupkan kembali. Pencarian resource
juga diperbaiki agar mengambil heading lengkap, bukan kutipan heading pada
pendahuluan. Tiga test baru membuktikan RED sebelum fix, lalu GREEN. Test protokol
tambahan membuktikan initialize, resource/prompt/tool discovery dari working
directory lain memakai proses MCP baru. Server MCP lama perlu reconnect karena
tidak hot-reload. Warning Pydantic `lifespan` masih ada; interpreter sistem tanpa
paket `mcp` bukan environment test yang dikonfigurasi.

Review frontend sebelumnya tidak menemukan bug implementasi, tetapi oracle test
link terlalu lemah. Test kini memeriksa rantai statement fisik persis, batas child
dan single ownership; mutasi `next=65535` terbukti tertangkap. Review backend
independen tersimpan sebelum sesi review terkena usage limit dan tidak menemukan
defect actionable pada AST, native helper, ABI atau runtime. Report dan detail
bukti tercatat di `RUNTIME_IO.md`. Reviewer MCP terpisah tidak menghasilkan report;
fix MCP diverifikasi lewat self-review dan test, bukan diklaim independent review.

Hash seed frontend:
`8b745978c63387126ba18b6a75524551b6352b296440cadc504a4468f3ce76ad`.
Hash seed backend:
`46a08a95224f7171b7fd9b948fecaf1e7b6e819c4a8b4b8471b980361d708405`.
Ketujuh bootstrap artifact cocok dengan pin. Probe tetap membedakan emitter
C0.25 dari frontend/backend C0.30; bounded-generation parity bukan Full Compiler.

### Blocker Berikutnya

Source frontend 51.214 byte dan backend 106.949 byte sama-sama ditolak C0P-002
oleh batas input 8.192 byte, exit 1 tanpa AST; lokasi masing-masing 166:8 dan
151:51. Source backend juga melampaui rentang span u16. Berikutnya adalah kontrak
kapasitas compiler-source: span lebih lebar atau compilation unit bounded,
kapasitas token/node dan layout arena secara koheren. Jangan sekadar menaikkan
konstanta input, mengulang C0.30, atau kembali menambah helper khusus pada C0.25.

Belum ada klaim Full Compiler atau self-hosting. Batas source 8.192 byte,
token/node 512 dan span u16 tetap; source compiler yang lebih besar memerlukan
pekerjaan kapasitas/versioned format terpisah setelah runtime ini terverifikasi.
`VERSION`, `CHANNEL`, Machine/Stage0/B0 dan emitter C0.25 tidak diubah.

---

# Work Unit C0.31: Kontrak Kapasitas Compiler-Source

Status: **IMPLEMENTATION IN PROGRESS; belum terverifikasi sebagai C0.31 selesai**.
Desain disetujui pada 2026-10-13; kelanjutan pada 2026-10-14 menyetujui eksekusi
rencana dengan subagent-driven development. Kontrak:
[C0.31 Compiler-Source Capacity](docs/superpowers/specs/2026-10-13-c031-compiler-capacity-design.md).
Ini tidak mengulang atau menaikkan status C0.30 yang sudah terverifikasi.

[Rencana implementasi C0.31](docs/superpowers/plans/2026-10-13-c031-compiler-capacity.md)
sudah disusun: bridge B0, frontend lebar, backend/slot native, runtime profile,
pipeline atomik, verifikasi generasi komponen, lalu integrasi pin dan MCP.
Setiap task mempunyai langkah RED/GREEN dan review terpisah. Task 1 selesai
kedua review pada 2026-10-16; Task 2 selesai pada 2026-10-21 dan Task 3 sedang
diverifikasi di worktree
`/home/Axelly/.codex/worktrees/4878/NolquASM`, yang memuat
salinan source dirty/untracked sebenarnya. Checkout utama tidak diubah.
Belum ada pin kandidat yang dipromosikan.

Baseline baru `make -k test release-check` memiliki log lengkap dengan
**1.082 PASS, 0 FAIL, 0 SKIP**: 1.073 gate utama dan 9 release gate.
Multiset nama PASS gate utama identik dengan hasil akhir C0.30. Receipt exit
shell gabungan hilang saat interupsi; jangan mengklaim exit 0 teramati untuk
command tersebut. Rerun terpisah `make release-check` lulus 9 gate, exit 0.
Suite MCP memakai interpreter yang dikonfigurasi: **37 test PASS, exit 0**.
Log: `/tmp/nql-c031-baseline-20261012.log` dan
`/tmp/nql-c031-mcp-baseline-20261012.log`. Semua pin bootstrap tetap cocok.

Inventaris melalui lexer B0 yang dipin, bukan parser host: frontend 51.214 byte
dan 12.019 token; backend 106.949 byte dan 25.014 token. Kedua command lexer
exit 0 tanpa stderr. Ini bukti kebutuhan kapasitas, bukan bukti source tersebut
sudah bisa dikompilasi C0. Batas source 8.192 byte masih menjadi blocker aktual.

Usulan menyatukan batas source/token/node, NQAF/5 dengan span/ID u32, arena
compiler-profile eksplisit, pemetaan slot per function, offset codegen dan
diagnostic lokasi. AST besar tidak otomatis memperbesar arena program pengguna.
Perubahan B0 dibatasi pada bridge profile yang dibuktikan perlu; jalur default
dan parity predecessor tetap wajib. Tidak memakai LLVM atau compiler host
sebagai tahap semantik tersembunyi.

Baseline eksekusi baru sebelum edit pada 2026-10-14 telah selesai: `make -k test`
**1.073 PASS, 0 FAIL, 0 SKIP, exit 0**; MCP **37 test, exit 0**; release
**9 PASS, exit 0**. Receipt terstruktur dan log terpisah berada di
`/tmp/nql-c031-execution-20261014.SWSw0P/baseline-receipts.json`.
Ini menggantikan kebutuhan mengulang baseline hanya karena sesi terinterupsi,
bukan pengganti pengujian regresi setelah implementasi.

Snapshot predecessor immutable sudah dapat direkonstruksi melalui Stage0/B0
dan diverifikasi terhadap SHA-256. Helper pengujian lulus 10 test setelah RED;
harness debugger lulus 17 test, termasuk syscall short-write nyata, EOF/packet
rusak, timeout serta cleanup proses/socket. Ini bukti infrastruktur pengujian,
bukan bukti bahwa profil compiler B0 atau C0.31 sudah selesai.

Kandidat bridge B0 kini lulus 15 test profil, termasuk parity byte/status/stream
54 fixture default dan kompilasi kedua source C0.30 beku. Dua build Stage0
identik; reference NASM independen juga cocok seluruh byte. Review menemukan
checksum debugger yang menerima tanda/spasi; reproduksi RED, perbaikan, dan
review ulang sudah lulus. Regresi penuh kandidat selesai: 1.073 gate utama,
37 test MCP dan 9 release gate, semuanya exit 0; nama PASS baseline identik.
Receipt: `validation-task1-green-receipts.json` dalam direktori bukti di atas.
Review spec dan kualitas compiler disetujui. Temuan validasi body packet debugger
ditutup melalui RED/GREEN dan review ulang independen: 30 test debugger lulus,
15 test profil diulang dan lulus tanpa mengubah kandidat B0. Ini menutup Task 1.

Task 2 dimulai dengan dua assertion RED terhadap C0.30: source 8.193 byte masih
ditolak C0P-002; envelope NQSC ditolak C0P-001. Oracle NQAF/5 sudah memeriksa
65.536 record dan ID u32 tanpa rekursi; ini bukti format wire, bukan klaim parser
sudah mampu menghasilkan 65.536 node. Pelebaran frontend dan transport belum
dinyatakan selesai. Kode diagnostic envelope menggunakan C0P-013, karena
C0P-010 sudah berarti trailing source pada C0.30.

Kandidat B0 terverifikasi tetap sama; seed/pin resmi, `VERSION`, `CHANNEL` dan
status Full Compiler/self-hosting belum berubah. Ledger kelanjutan:
`.superpowers/sdd/2026-10-13-c031-compiler-capacity/progress.md`. Detail
kompatibilitas, ownership resource, layout tanpa overlap, alternatif dan
acceptance gates tetap mengikuti spesifikasi.

## Checkpoint Frontend C0.31, 2026-10-21

Kandidat frontend lebar kini berhasil memparse **kedua source compiler aktual**,
bukan hanya fixture kecil. Epilog frontend/backend diubah dari conditional
return menjadi `return ok == 0`, sesuai grammar C0 yang mensyaratkan return
akhir pada tingkat fungsi. Eksekusi B0 membuktikan status tetap sama untuk nol,
nilai negatif dan beberapa nilai nonzero, dalam profil default maupun compiler.
Perubahan backend pada checkpoint ini hanya epilog tersebut.

| Source aktual | Byte source | Token | Node AST | Byte NQAF/5 |
| --- | ---: | ---: | ---: | ---: |
| `frontend.nql` | 63.904 | 14.212 | 12.607 | 467.360 |
| `backend.nql` | 106.927 | 25.007 | 22.480 | 826.319 |

Keempat eksekusi, raw source dan NQSC untuk masing-masing source, exit 0 tanpa
stderr; source dan graph ownership diverifikasi. Dialect tetap 4, runtime profile
tetap metadata terpisah 0/1. Ini bukti parsing source, belum bukti kompilasi
source tersebut menjadi executable melalui backend C0.

Suite kapasitas frontend **18 test PASS**, suite frontend **14 test PASS**,
dan probe epilog **32 build/eksekusi PASS**, semua exit 0. Dua build frontend
melalui B0 `--compiler-profile` identik; dua build backend dengan epilog setara
juga identik. Review spesifikasi dan review kualitas kode telah **APPROVED**
setelah memeriksa receipt regresi lengkap dan identitas source/artifact.

SHA-256 kandidat frontend:
`183b7ba50a64b672578c7bf8a25819c699a6937d4f0d3b6a3c59637714c3ff02`.
Pengujian NQAF/5 pada tepat 65.536 record adalah bukti oracle wire/storage;
grammar mencapai batas token sebelum menghasilkan sebanyak itu. Jangan
melabelinya bukti eksekusi allocator frontend pada 65.536 node.

Regresi penuh kandidat selesai pada salinan terpisah dengan pin provisional
yang koheren: **1.073 PASS, 0 FAIL, 0 SKIP**, nama gate identik dengan baseline;
MCP **37 test**, release **9 gate**, support **10 test**, debugger **30 test**,
profil B0 **15 test**, kapasitas frontend **18 test**, semuanya exit 0 tanpa
timeout. Keempat belas identitas seed/manifest resmi tetap sama. Empat test
MCP authority/protocol tambahan juga lulus, termasuk server dari cwd berbeda.
Task 2 selesai; Task 3 belum dimulai.
Frontend/format/transport dijelaskan di `bootstrap/compiler/c0/FRONTEND.md`;
receipt dan review tercatat dalam ledger C0.31 di atas. Seed/pin resmi dan status
Full Compiler/self-hosting tetap belum dipromosikan. Tahap berikutnya adalah
validator NQAF/5, slot native per fungsi dan lokasi lebar pada backend.

## Checkpoint Backend C0.31, 2026-10-21

Status Task 3: **COMPLETE, 2026-10-22; kandidat belum dipromosikan**.
Kandidat backend menerima NQAF/5, memvalidasi graph/anchor, memakai indeks
deklarasi fungsi dan awal baris, serta memisahkan node ID dari slot frame
per fungsi. Binding permanen tetap hidup sampai fungsi berakhir; temporer
dan argumen nested call memakai slot hidup yang tidak saling menimpa.
Batas frame tetap 512 i64/4.096 byte dan kedalaman call tetap 64 termasuk main.
Nama user pada node 513..517 tidak lagi berbagi identitas dengan intrinsic.

Source backend 150.457 byte / 36.011 token / 30.883 node berhasil diparse oleh
frontend kandidat. Dua build kanonik B0 compiler-profile identik, SHA-256:
`60fd60eade18fc683d1d86d66402fb63eb6740f481169330ae78c8acef8f0f8a`.
Suite kapasitas backend **28 test PASS**, exit 0, termasuk ABI nyata, graph
65.536 node, slot 512/513, rel32 mundur lebar, nama/literal panjang, lokasi
enam digit, malformed IR, proteksi batas tabel dan parity byte legacy.
Suite backend/control-flow/
function/runtime **59 test PASS**, exit 0. Ini bukan bukti self-compilation.

Regresi penuh pengganti selesai: **1.074 PASS, 0 FAIL/SKIP**, exit 0.
Multiset nama PASS mempertahankan tepat seluruh 1.073 gate baseline ditambah
satu `c0-capacity-backend`. MCP **37 test**, release **9 gate**, support **10**,
debugger **30**, B0 profile **15**, capacity frontend **18** dan capacity backend
**28** semuanya lulus dengan exit 0 dan tanpa timeout. Test nested tidak
ditambahkan lagi ke hitungan gate utama. Seluruh 14 file seed/hash resmi tetap
identik. Receipt: `/tmp/nql-c031-execution-20261014.SWSw0P/validation-task3-sentinel-20261021-receipts.json`,
SHA-256 `2f52721af270dc0e2ea4ff9c4b5161071c8522beede16318455e4640f265df90`.
Review spesifikasi dan kualitas penutupan terpisah keduanya **APPROVED**;
report `task-3-spec-review-closure.md` dan `task-3-quality-review-closure.md`
tersimpan pada workspace ledger C0.31. Task 4 kini menjadi tahap berikutnya.

Profil program default tetap arena 64 KiB, meskipun source lebar. Task 3
menolak profil compiler C0 eksplisit dengan C0B-009 setelah validasi graph dan
anchor, bukan diam-diam menggantinya dengan profil default; runtime mapped
merupakan Task 4. Bug kandidat pertama pada flag return, mask pencarian callee,
batas literal dan relokasi diagnostic sudah diperbaiki terhadap test RED.
Hasil dan identitas lengkap ada di ledger/report Task 3. Pin resmi tetap
C0.30; tidak ada promosi Full Compiler/self-hosting atau perubahan CLI/version.

## Checkpoint Runtime C0.31, 2026-10-22

Status Task 4: **COMPLETE, 2026-10-22; kandidat belum dipromosikan**.
Kandidat backend menerima profil compiler 1 eksplisit dari NQSC/NQAF/5 dan
membuat mapping anonymous/private 16.777.216 byte RW/NX hanya jika intrinsic
benar-benar teresolusi. Source lebar dengan profil 0 tetap memakai arena
64 KiB; fungsi user yang menutupi nama intrinsic tidak memicu mapping.

State privat 32 byte di atas frame menyimpan base, ownership, status keluar dan
stderr rusak. Jalur sukses, arithmetic/depth/range, stream dan kegagalan
diagnostic melewati cleanup. Mapping yang diperoleh dicoba dilepas tepat sekali;
kegagalan mmap/munmap memakai C0R-007, lokasi input:1:1, exit 74 dan pesan statis
di ELF. Kegagalan stderr tidak didiagnosis secara rekursif. Fatal signal tetap
mengandalkan reclamation OS, bukan jaminan cleanup userspace yang belum diuji.

Dua build kanonik B0 identik: **261.405 byte**, SHA-256
`4c46cba8d33c85e0af30d067f5b1a30ae1608e3bd87d2ef2f175377307c6ca72`.
Source backend **165.619 byte**, SHA-256
`2606be9e76c61b4126b55e78963d1f35526d8146d3c4caeaa4b39af7e6ebe0fe`.
Suite profil final **20 test PASS**, kapasitas backend **28 PASS**, dan seluruh
backend/control-flow/function/runtime **63 PASS**, masing-masing exit 0.
Oracle byte membandingkan nilai di dalam guest sebelum pemotongan exit status;
breakpoint syscall menolak release ganda bahkan sebelum diagnostic pertama.
Fault injection dibedakan dari kegagalan kernel alami. Detail receipt dan
identitas berada pada ledger/report Task 4. Full Compiler, self-hosting,
kompilasi komponen antargenerasi, pin resmi serta CLI/version belum dipromosikan.

Regresi penuh provisional selesai: **1.074 PASS, 0 FAIL/SKIP**, exit 0.
Multiset nama PASS tepat mempertahankan 1.073 gate baseline ditambah satu
`c0-capacity-backend`, identik dengan Task 3. MCP **37 test**, release **9 gate**,
support **10**, debugger **30**, B0 profile **15**, capacity frontend **18**,
capacity backend **28** dan C0 profile **20** semuanya lulus, exit 0 tanpa timeout.
Seluruh 14 identitas seed/hash resmi dan manifest tidak berubah. Receipt:
`/tmp/nql-c031-execution-20261014.SWSw0P/validation-task4-20261022-receipts.json`,
SHA-256 `3d937051d5a848a3421d3c6d28391038fd5264c9299bbd30d6be0575f3953893`.
Audit controller mengikat hash source/test, kandidat dan seluruh log; kedua
review penutup terpisah **APPROVED**, tanpa temuan terbuka. Report
`task-4-spec-review-closure.md` dan `task-4-quality-review.md` ada pada ledger
C0.31. Tahap berikutnya adalah wrapper source yang mendukung profil eksplisit,
cleanup sebelum rename dan penghentian subprocess milik invocation saat sinyal.
Ini belum merupakan bukti kompilasi komponen antargenerasi atau self-hosting.

## Checkpoint Pipeline C0.31, 2026-10-22

Status Task 5: **COMPLETE, 2026-10-22; kandidat belum dipromosikan**.
Wrapper source menerima flag awal `--compiler-profile` atau bentuk raw lama.
Profil eksplisit menambahkan header NQSC 16 byte lalu menyalin source tanpa
mengubah isinya. Seed dan pin dibaca relatif terhadap script, bukan cwd atau
environment khusus test. Status producer/frontend/backend diperiksa, termasuk
kegagalan teardown setelah output lengkap; file yang tidak kosong bukan bukti
kompilasi sukses.

AST, source berbingkai dan workspace harus berhasil dibersihkan sebelum rename.
Kegagalan sebelum commit mempertahankan byte dan mode output lama. Rename
menjadi titik commit; sinyal sesudahnya tidak menghapus atau memulihkan output.
Wrapper dan kedua materializer menghentikan process group milik command dan
menunggu direct child sebelum cleanup. Reaping orphan oleh OS bukan klaim wait
userspace terhadap non-child. Kegagalan filesystem permanen dilaporkan dengan
lokasi residu, bukan janji penghapusan yang tidak mungkin dipenuhi.

Suite pipeline **27 test PASS** serta **3 test lama** wrapper/materializer
lulus, semua exit 0 tanpa timeout. Regresi penuh provisional selesai dengan
**1.074 gate utama**, 37 test MCP dan 9 release gate. Seluruh sepuluh perintah
validasi exit 0 tanpa timeout: main, MCP, release, support, debugger, profil B0,
kapasitas frontend, kapasitas backend, profil C0 dan pipeline. Seluruh 1.073
nama PASS baseline tetap lengkap; multiset 1.074 gate identik dengan Task 3/4.
Tidak ada penjumlahan ulang test yang tertanam dalam gate utama.

Kedua review penutup terpisah **APPROVED**, tanpa temuan terbuka. Audit controller
dan kedua reviewer memeriksa 20 log, exit status serta hash kandidat yang sama.
Seluruh **204 file test lama** identik dengan snapshot Task 4; source compiler,
14 file seed/hash resmi dan manifest tidak berubah. Receipt
`validation-task5-20261022-receipts.json` dan audit
`task5-full-controller-audit.json` ada di
`/tmp/nql-c031-execution-20261014.SWSw0P`; identitas lengkap dan report review
ada pada ledger C0.31. Bukti targeted tetap di subdirektori `task5.262EVI`.
Task 6 menguji generasi komponen dari source lengkap. C0.31 secara keseluruhan,
Full Compiler dan self-hosting belum ditandai selesai atau dipromosikan.

## Checkpoint Generasi Komponen C0.31, 2026-10-22

Status Task 6: **SELESAI; penutupan terverifikasi pada 2026-10-23**.
Kedua source compiler lengkap dibangun dua kali oleh B0 menjadi A; pasangan A
membangun pasangan B, lalu B membangun C dari byte source yang sama. Frontend
B/C identik byte-for-byte, begitu juga backend B/C. A tidak diwajibkan identik
dengan B karena codegen B0 dan C0 berbeda. Semua generasi menjalankan corpus
legacy, lebar, malformed dan runtime; B dan C masing-masing juga menjalankan
18 test lama tanpa perubahan. Ini bukti generasi komponen, bukan Full Compiler
atau self-hosting penuh.

Corpus awal menemukan 26 kegagalan pada backend B/C: akumulasi literal MAX yang
valid memicu overflow internal, dan literal terlalu besar menghasilkan runtime
70 alih-alih C0B-005/1. Perbaikan terbatas mengguard operand sebelum aritmetika
eager, termasuk digit ditolak/inaktif. Sintaks, 16 local B0, template runtime,
kapasitas dan ABI tidak berubah. Kandidat backend baru `7c9f6b17...` dibangun
dua kali identik; kandidat historis `4c46...` dan seluruh pin resmi dipertahankan.

Run standalone terakhir lulus **6 test**, **215/215 check**, enam pembandingan
identik dan 18 test tambahan per B/C; exit 0 tanpa timeout. Gate gabungan baru
mengulang kapasitas frontend/backend/profil **18/28/20 test**, lalu generasi
**6 test** dengan B/C yang baru, seluruhnya PASS. Marker hanya dicetak setelah
subprocess sukses. Regresi terkait **63 test** serta pipeline **27** dan satu
test materializer frontend juga lulus. Tidak ada penjumlahan ulang subtest atau
test yang tertanam dalam gate sebagai gate utama.

Receipt `component-generations-final-green.json` dan `capacity-gate-final-green.json`
ada di `/tmp/nql-c031-execution-20261014.SWSw0P/task6.bqAEOO`; detail source,
ukuran, hash artefak, biaya arena dan batasnya ada pada
[CAPACITY.md](bootstrap/compiler/c0/CAPACITY.md). Audit controller membuktikan
seluruh **205 file test lama** dan **14 file seed/hash resmi** tidak berubah.
Regresi penuh provisional selesai dengan **1.074 gate utama**, **37 test MCP**,
**9 release gate**, support/debugger/profil B0 **10/30/15 test**, kapasitas
frontend/backend/profil C0/pipeline/generasi **18/28/20/27/6 test**, serta
verifikasi **7 pasangan seed/hash**. Seluruh 12 perintah exit 0 tanpa timeout.
Multiset nama PASS persis sama dengan Task 5: semua 1.073 gate baseline tetap
ada, dengan satu tambahan kapasitas backend yang sudah ada pada Task 3.
Jumlah nested test tidak dijumlahkan ulang sebagai gate utama.

Receipt `validation-task6-20261023-receipts.json` SHA-256
`0a0cbad28cddc5e27dc2ca98788f8b83d56e88315cb89d3403ce1489359b4556`
dan audit `task6-full-controller-audit.json` SHA-256
`bdd228da0876674d16393861878bee3d0d703c8873c66f7be1bd1b68f6df9147`
ada pada root evidence di atas. Kedua review penutup independen
**APPROVED**, tanpa temuan terbuka. Task 6 selesai; Task 7 berikutnya mengikat
hasil aktual ke MCP dan runner, menjalankan probe kanonik gabungan, lalu
meninjau seluruh perubahan sebelum promosi seed yang koheren. C0.31 secara
keseluruhan, pin resmi, Full Compiler dan self-hosting belum dipromosikan.

---

# GOVERNANCE REFERENCE BASIS

Bagian governance di prompt ini dibuat agar self-contained, tetapi prinsipnya selaras
dengan praktik software/language engineering yang mapan:

- **Semantic Versioning 2.0.0**: major untuk incompatible public-API change, minor untuk
  backward-compatible functionality/deprecation, patch untuk backward-compatible bugfix,
  dan released version tidak diubah diam-diam.
- **Rust RFC process**: perubahan language/system yang substantif membutuhkan design
  process lebih formal, sedangkan refactor/bugfix yang tidak mengubah meaning tidak selalu
  membutuhkan RFC.
- **Architecture Decision Records (ADR)**: keputusan arsitektur penting dicatat bersama
  context, decision, alternatives, dan consequences.
- **Release channels** seperti development/alpha/beta/release-candidate/stable digunakan
  untuk memisahkan maturity dari nomor versi.
- **Protected-branch / required-check practice**: high-risk merge dapat dibatasi oleh
  required review, required status checks, conversation resolution, push restrictions,
  dan protection terhadap force-push/deletion jika hosting platform mendukungnya.
- **LLVM release process**: semakin dekat release ke final, perubahan pada release line
  semakin konservatif; regression dan backport diperlakukan sebagai release-management
  decision, bukan kesempatan menambah feature baru.
- **Rust compiler fuzzing practice**: fuzzing digunakan sebagai complementary compiler
  validation untuk menemukan crash/ICE dan bug yang sulit dijangkau test biasa.
- **SLSA provenance model**: provenance adalah informasi verifiable mengenai dari mana,
  kapan, dan bagaimana artifact dihasilkan; gunakan sebagai reference bila NolQu-L
  suatu saat mempunyai provenance/attestation infrastructure nyata.

Referensi ini **bukan sumber kebenaran NolQu-L**.

Urutan otoritas NolQu-L tetap mengikuti bagian:

```text
OTORITAS DAN URUTAN SUMBER KEBENARAN
```

di dokumen ini.

NolQu-L tidak wajib meniru SemVer, Rust, atau project lain apabila keputusan arsitektur
NolQu-L yang terdokumentasi membutuhkan policy berbeda. Jika policy berbeda, jelaskan
alasan, compatibility impact, dan migration-nya.

Governance reference tidak boleh dipakai untuk mengarang infrastructure yang belum ada.
Jika repository belum mempunyai branch protection, signing, SBOM, provenance, target tier,
release manager, atau downstream suite, statusnya harus ditulis `NOT IMPLEMENTED`,
`NOT FORMALLY DEFINED`, atau `NOT YET ESTABLISHED` sesuai konteks—bukan dipalsukan agar
checklist terlihat lengkap.

## Checkpoint Instalasi C0.31 (2026-10-23)

Status: **COMPLETE — TERPASANG KOHEREN DAN TERVERIFIKASI** untuk kapasitas C0.31.
Review whole-change akhir telah menyetujui penutupan tanpa temuan terbuka.
Bukan rilis publik. Snapshot serta checkpoint sebelumnya tetap historis.

Sasaran teknis: menjadikan kapasitas source compiler yang sudah diimplementasikan
sebagai jalur kanonik yang dapat dipakai tanpa override kandidat. Batas tetap
262144 byte source, 65536 token/node, NQAF/5 u32, frame 4096 byte/512 slot,
profil default 64 KiB dan profil compiler eksplisit mapped 16 MiB RW/NX.
Kedua source lengkap tetap 63904 dan 165737 byte; tidak dipotong atau ditulis
ulang oleh host. Jalur tetap Machine -> Stage0 -> B0 -> C0.

Delapan pemeriksaan pra-instalasi lulus exit 0 tanpa timeout atau skip:
discovery protokol MCP dari cwd lain (120 skema tool/8 resource/5 prompt),
46 test MCP, 1076 gate utama, 16 test profil B0, 27 test pipeline, 9 release
gate, tujuh pasangan hash bootstrap dan probe kanonik gabungan nyata.
Semua 1073 nama PASS baseline dan 37 selector MCP lama dipertahankan.
Probe memvalidasi 215 check/554 stage, enam perbandingan identik dan 18 metode
oracle per B/C; kasus negatif tetap memakai exit nonzero yang diharapkan.
Frontend B/C identik pada 6349683 byte, backend B/C identik pada 6445930 byte.
Hash, identitas source/artifact dan receipt rinci tersedia di CAPACITY.md.

Review menemukan dua masalah nyata sebelum promosi: fixture MCP melewati jalur
error yang dimaksud, dan runtime B0 mencoba diagnostik kedua bila stderr lalu
munmap gagal. Fixture kini menguji helper aktif beserta positive control yang
jelas unit-only. Perbaikan R15 privat B0 lulus empat kasus guest RED/GREEN,
semua 16 test profil dan parity 54 fixture default. Tidak ada perubahan grammar,
kapasitas baru, ABI C0, atau klaim performa. Review SPEC, QUALITY dan whole-change
menyetujui set yang diverifikasi sebelum materialisasi kanonik.

B0/frontend/backend beserta tiga hash dipasang melalui materializer kanonik;
empat pasangan seed/pin lain dan manifest tetap. Rollback sumber/script/metadata/
pin lengkap telah diarsip dan fresh-extract diperiksa, tidak pernah dijalankan
sebagai rollback. Versi tetap 1.0.2a1/dev dan perubahan hanya di worktree terpisah,
tanpa commit, merge atau push. `nqlc` publik masih R0/NASM; Full Compiler,
self-hosting, Verified, ISA baru dan Safety penuh tetap belum diimplementasikan.

Delapan perintah yang sama telah diulang dalam mode promoted, setelah byte
resmi diperiksa sama dengan kandidat yang direview, tanpa staging override.
Seluruh exit 0, tanpa timeout/skip, dengan input/pin guards tetap benar dan
1076 nama gate persis sama dengan pra-instalasi. Probe MCP baru kembali
memverifikasi 215 check/554 stage serta oracle dan identitas B/C yang sama.
Receipt pascainstalasi SHA-256
`98350a556a1ace5953970aa91f69bbd82800f6830ae72ca7f3b07ca26de5868a`;
audit `87864ad112abd1c522e24d6e5769601c64d8c1cbafcf1ac913e6a1a2b2ddc42b`.
Rincian lengkap ada di CAPACITY.md. Ini hasil aktual, bukan asumsi dari fase
pra-instalasi. Enam test resource/otoritas/metadata MCP serta sembilan release
gate juga lulus setelah pembaruan dokumentasi. Review akhir memeriksa hasil
pascainstalasi, byte resmi, penggunaan wrapper langsung, rollback dan dokumen;
SHA-256 report `d95f1eccbd3b9ca655c500830bba631bde71ec41df539e24018d3af49924d79b`.
Seluruh tujuh task selesai dalam scope kapasitas ini. Sasaran compiler terpisah
berikutnya adalah transisi Full Compiler/CLI publik kanonik beserta gate
kompatibilitasnya; kemampuan itu belum dinyatakan terimplementasi.
