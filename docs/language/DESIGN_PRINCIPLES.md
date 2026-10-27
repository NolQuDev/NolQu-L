# NolQu-L Design Principles

## 1. Keep The Surface Language Small

NolQu-L should stay readable and compact at the language surface. Complexity may
exist in the compiler, but it should not casually spill into the syntax or the
mental model users need.

## 2. Prefer Clarity Over Cleverness

Language rules, examples, and diagnostics should make behavior easier to
understand, not harder.

## 3. Keep One Semantic Center

Passing tests and explicit language rules are the source of truth. Reference
Compiler R0 is the current oracle; canonical stages must converge on those
rules without making LLVM or another compatibility path a language variant.

## 4. Let Internal Complexity Stay Internal

Backend and tooling sophistication are acceptable when they strengthen the
project, but they should not force the language itself to become chaotic or
overdesigned.

## 5. Treat Tests And Docs As Part Of The Design

If behavior matters, it should be visible in:

- docs
- examples when user-facing
- tests

## 6. Prefer Explicit Over Accidental Semantics

If a semantic rule becomes important, it should be documented and tested rather
than left as an implementation accident.

## 7. Stay Close To The Machine

NolQu-L's canonical chain begins at auditable machine bytes and must remain
honest about allocations, syscalls, calls, memory layout, and runtime checks.
Abstractions that obscure machine behavior are not NolQu-L abstractions.

## 8. Grow Carefully

New features should not be added just because they are possible. They should be
added when they strengthen the language without blurring its identity.

## Related Docs

- [CORE_LANGUAGE.md](/root/Nolqu/docs/language/CORE_LANGUAGE.md)
- [DECISIONS.md](/root/Nolqu/docs/language/DECISIONS.md)
- [STATE_OF_PROJECT.md](/root/Nolqu/docs/project/STATE_OF_PROJECT.md)
