# NolQu-L Label Policy

This document defines the small label set intended for the GitHub repository.

The goal is to keep issue and pull request triage readable without turning
labels into a second taxonomy that is harder to maintain than the repo itself.

## Core Labels

- `bug`: confirmed or likely incorrect behavior
- `enhancement`: improvement request that fits current direction
- `docs`: documentation-only or documentation-heavy work
- `tests`: test-only or test-heavy work
- `backend`: backend-specific work, including NASM, LLVM bootstrap, or `ir-llvm`
- `language`: language-surface or semantic-model work
- `tooling`: CLI, build, packaging, repo automation, or GitHub workflow work

## State Labels

- `needs-repro`: not yet reproduced clearly
- `needs-design`: blocked on language or compiler design direction
- `good first issue`: small, bounded, and safe for a first contribution
- `blocked`: cannot move until another issue or decision is resolved

## Release Labels

- `stable`: directly relevant to stable release quality
- `dev`: relevant to the active development line

## Practical Rule

Prefer a small number of accurate labels.

Good:

- `bug`
- `backend`
- `dev`

Bad:

- five overlapping labels that all mean roughly "compiler problem"

## Related Docs

- [GOVERNANCE.md](/root/Nolqu/docs/community/GOVERNANCE.md)
- [CONTRIBUTING.md](/root/Nolqu/docs/community/CONTRIBUTING.md)
- [MAINTAINER_CHECKLIST.md](/root/Nolqu/docs/project/MAINTAINER_CHECKLIST.md)
