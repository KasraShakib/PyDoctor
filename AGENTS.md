# PYD Engineering Rules

These rules apply to all work in this repository and to every subdirectory unless a more specific `AGENTS.md` overrides them.

## Scope and Safety

- All project work must stay inside `C:\Users\ACER\Source\Repo\PYD`.
- Never create project files in the parent `Repo` directory.
- Never modify files, projects, or system settings outside PYD without explicit permission.
- Preserve existing user files and functionality. Inspect before changing anything.
- Do not install global software or modify the Windows PATH unless explicitly requested.
- Do not commit secrets, credentials, API keys, virtual environments, dependency caches, or build artifacts.

## Code Quality

- Keep code clean, readable, and modular.
- Separate the desktop interface from the Python diagnostic engine.
- Keep components independently testable.
- Avoid unnecessary frameworks and dependencies.
- Do not invent dependency versions; use versions supported by the installed toolchain.
- Prefer the smallest coherent change over broad rewrites.

## Testing and Verification

- Run relevant tests after changes to code or configuration.
- Run Ruff checks when the Python development environment is available.
- Never claim a test, build, or verification was executed unless it was actually executed.
- Report failures and skipped checks honestly.

## Documentation

- Update documentation when setup, architecture, or development workflows change.
- Record significant technical decisions in `docs/DECISIONS.md`.
- Keep instructions reproducible for a developer on Windows.

## Code Documentation Standards

- Use clear, professional English for all source code comments and docstrings.
- Write meaningful documentation for public modules, classes, and functions.
- Explain non-obvious logic, design decisions, constraints, and potential side effects.
- Avoid redundant comments that simply restate the code.
- Prefer readable, maintainable implementations over excessive inline documentation.
- Keep all project documentation professional, consistent, and focused on the product.