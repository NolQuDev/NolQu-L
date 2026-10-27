# Branch roles

| Branch | Purpose | Current role |
| --- | --- | --- |
| `Main` | Integration of tested development, fixes and documentation | Default branch; may contain Alpha or later work |
| `Dev` | Alpha development | Keep `VERSION` in `MAJOR.MINOR.PATCH-alpha.N` form |
| `Rel` | Release Candidate preparation through final release | Empty until an RC is ready |

`Rel` currently has an empty file tree: no Alpha code, version metadata,
artifacts or placeholder README. A Git branch needs a commit; the empty commit
reserves the name and does not erase earlier history or publish an RC.

Normal development goes from `Dev` to tested integration in `Main`. Beta work,
if needed, can stay in `Main`; `Dev` remains Alpha until the maintainer changes
this policy. Populate `Rel` from a qualified source revision only when an RC
version, changelog and required release evidence are ready. Freeze ordinary
features there and focus on release-blocking fixes through the final release.
Do not populate `Rel` with the current Alpha snapshot.

Linux qualification runs on the three named branches once they contain the
workflow. It rejects non-Alpha versions for `Dev` and Alpha/Beta versions for
`Rel`; pull requests use their destination branch's rule. `Main` allows mixed
integration. The empty `Rel` branch has no workflow to execute yet.

Branch names and a green development job do not create a release or prove
stable maturity. No automatic tagging, publishing, protection rules or promotion
is enabled by this policy. Keep [PUBLICATION.md](PUBLICATION.md) exclusions on
every populated branch.
