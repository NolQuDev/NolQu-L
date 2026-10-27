# Android host smoke bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Execute sequentially; retain evidence and do not commit/push/release.

**Goal:** Provide an independently copied, bounded Android host smoke bundle
without making a false native-Termux claim.
**Architecture:** New optional standard-library host tool; reuse the unchanged
bounded runner and pinned compiler components. No compiler integration changes.
**Tech Stack:** Python/unittest, existing QEMU Linux-user adapter.
**Spec:** [Android host design](../specs/2026-10-27-android-host-design.md).

## Global Constraints

- Preserve all61 existing proof inputs and all canonical sources/seeds/pins.
- Preserve VERSION1.0.2a1 and CHANNELdev. No commit/merge/push/release.
- Copy independent bytes only; private new directories; fixed manifest allowlist.
- One guest call at a time; one attempt;15s/call,300s aggregate,8MiB/stream,3MiB input.
- Native requires explicit observed TracerPid0 and Termux Python on Android.
- Do not change Android permissions or service configuration.
- Retain C032-SIGNAL-01 OPEN and native execution NOT TESTED until actual evidence.

## Review Focus

- Wrong or changed pin must fail before launching; AB02/AB04.
- Symlinks/FIFOs and partial preparation must not produce a usable bundle; AB03.
- Existing output/evidence must survive all failures; AB05.
- Missing proc metadata must not manufacture a native result; AB06/AB07.
- Real guest output, error location and source-dependent artifact must be checked;
  retain raw bounded invocations and run AB08.

## Task1: copied bundle and context classification

Files: create tools/nql_android_smoke.py and
tests/security/test_android_host.py.
Interfaces: prepare_bundle(root, destination)->manifest;
verify_bundle(bundle)->manifest; host_context(proc_root=Path('/proc'))->dict;
run_bundle(bundle, output, require_native_termux=False)->report.

- [ ] Write AB01–AB07, observe the initial missing-tool RED.
- [ ] Implement only the fixed copy/hash/context/output contracts.
- [ ] Run the control suite and preserve RED/GREEN logs.

## Task2: sequential real compiler smoke and handoff

Interfaces: consume the verified bundle; use its unchanged BoundedRunner to run
the documented finite cases and write result.json with checks and limitations.
Files: tool/tests above; new docs/compiler/ANDROID_HOST_TESTING.md and
docs/project/ANDROID_HOST_SESSION_REPORT.md; Unreleased changelog entry.

- [ ] Write AB08 against real pinned components, observe missing-run RED.
- [ ] Implement sequential calls, exact outputs/status/diagnostic oracles and
  deterministic AST/ELF comparisons; failure persists a non-success report.
- [ ] Run new controls, existing runner/evidence controls and real bundle smoke
  sequentially. Prepare an independent bundle in Termux private storage.
- [ ] Fresh review if available; check syntax, whitespace and61 unchanged proof
  inputs. Write actual results/native limitation and runnable Termux command.

Pre-flight: Task2 consumes the fixed manifest and context from Task1. The runner
is copied unchanged and verified before import; no shared existing code is edited.

## Native continuation correction — 2026-10-27

Task1 and the original Task2 implementation/tests already exist; their ledger is
retained from the migration archive. Continue the outstanding review, without
repeating completed implementation or historical traced runs.

Native baseline failed before guest launch because evidence blob publication
required unavailable `os.link`. The existing proof-input preservation constraint
therefore needs this explicit exception: repair the host-only evidence helper
and its controls, retain the original failed baseline and old hashes, and record
the intended host-file identity changes. Compiler source/seed/pin identities stay
fixed. This is a local portability repair, not a bootstrap stage change.

- [x] Reproduce the host publication failure (NE18 RED); replace hard links with
  closed-temp rename under a directory lock, preserving existing-blob validation.
- [x] Isolate native host-oracle assumptions without skipping tests; all18
  evidence controls pass, retaining all17 original method names.
- [x] Reproduce unchecked pyc bypass (AB10 RED), execute verified source bytes,
  then pass the complete10-test control suite.
- [x] Reproduce stale report staging (AB11 RED), use unique staging/owned cleanup,
  then pass the complete11-test suite.
- [x] Reproduce the8MiB adapter rejection (AB12 RED), stream the regular snapshot,
  then pass the complete12-test suite.
- [ ] Run all relevant final native gates sequentially, retaining failures and
  exact raw streams. Do not convert a later pass into failure attribution.
- [ ] Finish independent review, documentation and final scope/limitation report.
