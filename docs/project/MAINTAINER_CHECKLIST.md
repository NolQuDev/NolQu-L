# NolQu-L Maintainer Checklist

## Daily Maintenance

- keep `VERSION` and `CHANNEL` accurate
- keep docs aligned with current behavior
- keep examples aligned with supported semantics
- keep tests green
- keep `bootstrap/manifest.tsv` aligned with proven artifacts
- avoid confusing Reference Compiler R0 or legacy tooling with canonical stages

## Before Accepting A Meaningful Change

- check whether the change touches core language semantics
- check whether docs need updating
- check whether examples need updating
- check whether canonical bootstrap or R0 diagnostics coverage should be updated
- reject new architecture implemented through LLVM/Python compatibility paths

## Before A Pre-Release Move

- update [README.md](../../README.md) if user-visible behavior changed
- update [CHANGELOG.md](CHANGELOG.md)
- review [FEATURE_STATUS.md](../language/FEATURE_STATUS.md)
- review [DECISIONS.md](../language/DECISIONS.md) if semantics changed
- run:
  - `make bootstrap-test`
  - `make release-check`
  - `make test`

## Before A Stable Release

- make sure `CHANNEL` is appropriate
- confirm that pre-release-only language or backend assumptions are not being
  presented as stable defaults
- re-check public-facing docs and examples
- run the normal stable release flow in [RELEASING.md](RELEASING.md)

## Practical Rule

If a change would make the language surface less clear, more accidental, or
less consistent, stop and document the decision before merging more work on
top of it.
