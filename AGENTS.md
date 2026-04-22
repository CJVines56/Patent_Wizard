# AGENTS Instructions

This file applies to Codex and any other LLM agent operating in this repository.

## Required On Every User Request
1. Read this file before making decisions or edits.
2. Read the latest section in `docs/SESSION_CHANGELOG.md`.
3. If you change any file, append a new timestamped entry to `docs/SESSION_CHANGELOG.md` in the same task.

## Required Changelog Entry Template
Use this exact structure for each changed file:

- File: `<path>`
- Lines changed: `<line refs or short description of section changed>`
- Problem: `<short statement of what was wrong>`
- Change: `<short statement of what was implemented>`
- Why: `<short statement of why this implementation was chosen>`

## Timestamp Format
Section headers in `docs/SESSION_CHANGELOG.md` must use:

`## YYYY-MM-DD HH:MM:SS TZ`

Example:

`## 2026-04-16 13:27:19 CDT`

## Scope
- Do not skip changelog updates, even for documentation-only edits.
- Do not add changelog entries for command-only, analysis-only, or other no-file-change responses.
- Keep entries concise and factual.
- Prefer one section per task, grouping all files touched in that task.
