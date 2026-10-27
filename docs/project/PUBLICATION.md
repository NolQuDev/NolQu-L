# Public source and private development files

Publish compiler sources, canonical bootstrap artifacts and hashes, tests,
examples, public interface/architecture contracts, and release documentation.
Record user-visible changes in [CHANGELOG.md](CHANGELOG.md). Keep concise design
and behavior contracts next to their implementation.

Keep master development prompts, concept DOCX attachments, agent instructions,
plans/specifications under `docs/superpowers/`, session reports, handoff notes,
local configuration, credentials, conversations, environments and raw working
evidence outside public source publication. Preserve local copies as needed.
Public summaries must state results and limitations without copying those files.

`.gitignore` protects new untracked files. It does not remove already tracked
files. `tools/check_publication.py` therefore checks the selected tracked paths;
Linux CI runs this required gate and its controls before compiler qualification.
For an explicit source snapshot, pass `--manifest` with a JSON `files` array
of objects containing `path`. An empty selection or blocked path fails.

This path check is not a content/secret audit or a Git-history cleanup. Removing
a file from the current branch leaves its earlier commits accessible. Rewriting
published history requires a separate coordinated cleanup; no such rewrite is
claimed here. Bootstrap hashes and historical technical evidence are not
renamed or invented when private work records are excluded.

Optional MCP design resources report an absent master document explicitly.
They do not use an obsolete document or fabricated design text as a fallback.
