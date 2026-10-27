# NolQu-L Security

NolQu-L is an experimental language and toolchain. It should not yet be assumed
safe for high-trust or hostile-input production environments.

## Current Scope

- this project is still under active development
- malformed inputs, backend mismatches, or incomplete features may still exist
- experimental paths such as LLVM bridge work should be treated with extra care

## Reporting

If you believe you found a security issue, parser crash, memory-safety issue,
or unsafe code-generation problem, report it privately to:

- `nolqudev@gmail.com`
- `nolquteam@gmail.com`
- `nolqucontact@gmail.com`

Include, when possible:

- NolQu-L version
- host platform
- backend used
- minimal repro input
- observed output or crash behavior

## Disclosure

Please prefer responsible disclosure before public posting when the issue could
affect users running generated binaries or shared tooling.
