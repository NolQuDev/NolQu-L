# Native invocation evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Preserve exact per-invocation diagnostic evidence through disposable test cleanup.
**Architecture:** Add an opt-in observer to the existing run_native helper while preserving the absent-option subprocess.run path and owned-child lifecycle. Keep sidecars separate from strict generation receipts and external process tracing.
**Tech Stack:** Existing host Python standard library, unittest, shell gate; existing QEMU adapter. No canonical build/runtime dependency added.
**Spec:** [NATIVE_TEST_EVIDENCE.md](../../compiler/NATIVE_TEST_EVIDENCE.md); design and review snapshots retained in the task evidence directory /tmp/nql-c032-reliability-20261026-ems1vhfz.

## Global Constraints

- Preserve VERSION1.0.2a1/CHANNELdev, compiler source/seed/pins/ABI/topology and existing timeouts.
- No product edits before the unchanged serial main/MCP/runner/assurance/release baseline finishes or a failure is understood/documented.
- No retries, global subprocess patch, new session/group cleanup or BoundedRunner substitution.
- Exact byte archive where owned; external stdin payload and inaccessible proc metadata explicitly unobserved.
- Preserve original C032-SIGNAL-01 as OPEN unless matching actual cause evidence exists.
- No commit/merge/push/release for this task; user-owned dirty state preserved.

## Review Focus

- Closing0/1/2 or passing read-only/write-only FDs must still produce the original result; NE04.
- Signal status, timeout and cancellation must remain distinct and reap only owned child; NE03/NE08.
- Archive failure/tampering must never manufacture success or launch after invalid preparation; NE07/NE09.
- Temp cleanup, bytes argv and concurrent calls must leave exact uniquely attributable records; NE01/NE05/NE17.
- Optional observation changes proof input identity; fresh proof, MCP, assurance and end-to-end main must bind it.

---

### Task1: host observation and integration

Files: modify tests/bootstrap/c031_support.py::run_native; create tests/bootstrap/test_run_native_evidence.py; modify tests/bootstrap/run_tests.sh; document docs/compiler/NATIVE_TEST_EVIDENCE.md.
Interfaces: preserve run_native(binary,data=b'',*,args=(),timeout=15,**kwargs)->CompletedProcess; add optional environment NQL_NATIVE_EVIDENCE_DIR; expose NativeEvidenceError with record/result/original_error for distinct harness failures. Private helpers handle blob publication/atomic records/proc observations.

- [x] Draft host controls outside W and run NE01 against original helper; assert failure because no retained invocation exists after caller cleanup. Save actual RED.
- [x] After baseline, record final classification and exact input snapshot; copy control into W, retain RED, implement just specified optional branch.
- [x] Run focused real-process controls: normal0/1/7 bytes, check exception, argv/cwd, external stdin, uncaptured streams, closed/wrong-direction FDs, signal/timeout partial bytes, spawn/proc/archive failures, executable replacement flag, cancellation/sibling and parallel uniqueness.
- [x] Integrate one explicit python control invocation and PASS marker in run_tests.sh; no pinned gate/test definition changes.
- [x] Independent fresh-context review of helper/control/docs and exact existing kwargs, address concrete findings using RED/GREEN.

### Task2: current-input evidence and completion

Files: sidecar receipts outside W; update current report/changelog/status/docs after measured results.

- [x] Freeze helper/control/gate bytes and bind final source map; serialize one observed full main, MCP124, fresh combined generation proof (no duplicate standalone proof), assurance594 and release9. Runner11 baseline remains applicable if its code unchanged.
- [x] Audit invocation records for incomplete/outcome classes, raw blobs/hashes, and exact known old-backend nested-call tuple retention; do not infer signal sender from a negative returncode.
- [x] Verify fresh full-source B=C identities unchanged, sources/pins unchanged; compare baseline PASS multiset.
- [x] Update threat/invariant/test matrix and full0–15+14A session report, exact failed experiments, known limitations and measured next blocker; independent evidence review and diff check.

Completion evidence2026-10-26: normal baseline1079, observed main1080 preserving
all labels, MCP124, fresh actual combined proof722/275, assurance594 and release9
completed with unchanged execution inputs. Host controls17 and actual adapter
comparisons14+2 passed. Native archive audit:3771 terminal records,1364 valid blobs,
zero incomplete/signal/mutation observations and four exact old-backend nested-call
matches. Independent code review5 READY covered the integrated bytes. An additional
report-script review attempt returned a service usage-limit error before completion;
that supplementary review is NOT RUN. Documentation/evidence were self-reviewed;
no human approval, merge, release or historical signal resolution is inferred.
See docs/project/C032_RELIABILITY_REPORT.md and the retained SDD evidence ledger.
