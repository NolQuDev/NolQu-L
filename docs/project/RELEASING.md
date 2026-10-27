# NolQu-L Releasing

## Tracks

- `dev`: active work, including `a`, `b`, and `rc` versions
- `stable`: public release line

## Current development version

`VERSION` contains `1.0.0-alpha.1`; `CHANNEL` remains `dev`. The maintainer
requested this prerelease naming reset on 2026-10-27 before the initial push to
`NolQuDev/NolQu-L`. Use `v1.0.0-alpha.1` only as a tag name when a release/tag
is actually approved and created. Updating metadata does not publish a release.
No tag, stable promotion or bootstrap milestone is implied by this version.

Older labels such as `1.0.2a1`, their release notes, artifact hashes and test
receipts are historical and stay unchanged. Consumers comparing raw version
strings must accept the new value; `1.0.0-alpha.1` does not sort as an upgrade
from `1.0.2a1`. Source/ABI contracts and canonical seed bytes are unaffected.

## Typical Flow

1. Update [VERSION](/root/Nolqu/VERSION).
2. Set the correct release track in [CHANNEL](/root/Nolqu/CHANNEL).
3. Update [README.md](/root/Nolqu/README.md) if user-facing behavior changed.
4. Add release notes to [docs/project/CHANGELOG.md](/root/Nolqu/docs/project/CHANGELOG.md).
5. Check whether any feature moved between `core`, `experimental`, or `syntax-only` status in [CORE_LANGUAGE.md](/root/Nolqu/docs/language/CORE_LANGUAGE.md) and [FEATURE_STATUS.md](/root/Nolqu/docs/language/FEATURE_STATUS.md).
6. Run `make bootstrap-test` and confirm `bootstrap/manifest.tsv` matches the
   artifacts actually proven by tests.
7. If legacy LLVM behavior changed, verify it remained compatibility-only and
   update its frozen status documentation when necessary.
8. Keep legal and project-policy docs aligned: [LICENSE](/root/Nolqu/LICENSE), [TRADEMARK.md](/root/Nolqu/docs/community/TRADEMARK.md), [CONTACT.md](/root/Nolqu/docs/community/CONTACT.md), [CONTRIBUTING.md](/root/Nolqu/docs/community/CONTRIBUTING.md), [SECURITY.md](/root/Nolqu/docs/community/SECURITY.md), [CODE_OF_CONDUCT.md](/root/Nolqu/docs/community/CODE_OF_CONDUCT.md), [AUTHORS.md](/root/Nolqu/docs/community/AUTHORS.md), [SUPPORT.md](/root/Nolqu/docs/community/SUPPORT.md), [GOVERNANCE.md](/root/Nolqu/docs/community/GOVERNANCE.md), [FAQ.md](/root/Nolqu/docs/community/FAQ.md), [STYLE_GUIDE.md](/root/Nolqu/docs/community/STYLE_GUIDE.md), [COMPATIBILITY.md](/root/Nolqu/docs/project/COMPATIBILITY.md), [PACKAGING.md](/root/Nolqu/docs/project/PACKAGING.md), [INSTALL.md](/root/Nolqu/docs/project/INSTALL.md), [BACKENDS.md](/root/Nolqu/docs/compiler/BACKENDS.md), [PROJECT_STRUCTURE.md](/root/Nolqu/docs/project/PROJECT_STRUCTURE.md), [TESTING.md](/root/Nolqu/docs/compiler/TESTING.md), [COMMANDS.md](/root/Nolqu/docs/project/COMMANDS.md), [IR.md](/root/Nolqu/docs/compiler/IR.md), [TERMINOLOGY.md](/root/Nolqu/docs/language/TERMINOLOGY.md), [DECISIONS.md](/root/Nolqu/docs/language/DECISIONS.md), [KNOWN_LIMITATIONS.md](/root/Nolqu/docs/language/KNOWN_LIMITATIONS.md), [ERRORS.md](/root/Nolqu/docs/language/ERRORS.md), [ROADMAP_SHORT.md](/root/Nolqu/docs/project/ROADMAP_SHORT.md), [STATE_OF_PROJECT.md](/root/Nolqu/docs/project/STATE_OF_PROJECT.md), [REPO_INDEX.md](/root/Nolqu/docs/project/REPO_INDEX.md), [MAINTAINER_CHECKLIST.md](/root/Nolqu/docs/project/MAINTAINER_CHECKLIST.md), [RELEASE_NOTES_TEMPLATE.md](/root/Nolqu/docs/project/RELEASE_NOTES_TEMPLATE.md), [LABELS.md](/root/Nolqu/docs/project/LABELS.md), [.github/CODEOWNERS](/root/Nolqu/.github/CODEOWNERS), and [DESIGN_PRINCIPLES.md](/root/Nolqu/docs/language/DESIGN_PRINCIPLES.md).
5. Run:
   `make dev`
   `make release-check`
6. If preparing a stable release, switch channel and run:
   `make stable`

## Notes

- alpha, beta, and rc builds should stay on `dev`
- only final public releases should move to `stable`
- keep docs and tests aligned before tagging a release
- `make release-check` should pass before moving from alpha to beta, beta to rc, or rc to stable
- do not promote an experimental feature to "stable language" without docs, examples, and tests
- do not label Reference Compiler R0 as Stage 0 or self-hosted
- do not silently widen frozen LLVM/Python compatibility paths
- do not mark a bootstrap stage complete without a predecessor-built artifact
  and repeatable evidence
- do not let legal, contact, or trademark docs drift away from the current public project identity
