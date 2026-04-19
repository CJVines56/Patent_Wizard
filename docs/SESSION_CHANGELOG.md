# Session Changelog

## 2026-04-19 15:33:33 CDT
- File: [.gitignore](/mnt/c/Patent_Wizard/.gitignore)
- Lines changed: added ignore rules for [`.gitignore:40`](/mnt/c/Patent_Wizard/.gitignore:40) onward covering `backend/orchestrator/env` and `backend/orchestrator/.env`.
- Problem: push protection kept blocking `CJ_Branch` because secrets from local orchestrator env files were getting committed.
- Change: Added explicit ignore entries for local orchestrator env files.
- Why: Prevents future commits from accidentally including those secret-bearing local files.

- File: [backend/orchestrator/env](/mnt/c/Patent_Wizard/backend/orchestrator/env)
- Lines changed: removed from Git tracking via `git rm --cached` (file remains local).
- Problem: the last commit contained a LangSmith token in this tracked env file, triggering GitHub push protection.
- Change: untracked the file and rewrote the commit after staging the removal.
- Why: removes the secret from pushed commit history while preserving your local runtime env file.

## 2026-04-16 13:31:52 CDT
- File: [backend/orchestrator/tools.py](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py)
- Lines changed: [backend/orchestrator/tools.py:39](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py:39), [backend/orchestrator/tools.py:126](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py:126), [backend/orchestrator/tools.py:166](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py:166).
- Problem: nearVector/hybrid GraphQL retrieval in the API path used a single 60s timeout and failed too aggressively under slow vector search.
- Change: Added vector-query timeout schedule and retries in `_post_graphql` with defaults `180s -> 240s -> 300s` (`WEAVIATE_VECTOR_TIMEOUT_INITIAL_S`, `WEAVIATE_VECTOR_TIMEOUT_STEP_S`, `WEAVIATE_VECTOR_TIMEOUT_MAX_S`), while keeping non-vector GraphQL calls on `WEAVIATE_GRAPHQL_TIMEOUT_S` (default 60s).
- Why: Reduces repeated one-minute failures and gives nearVector retrieval enough time to complete before failing over.

- File: [backend/app/scripts/retrieve_rerank.py](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py)
- Lines changed: [backend/app/scripts/retrieve_rerank.py:67](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:67), [backend/app/scripts/retrieve_rerank.py:150](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:150), [backend/app/scripts/retrieve_rerank.py:190](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:190).
- Problem: validation/qrels retrieval path had no escalating retry policy for vector GraphQL timeouts.
- Change: Added the same vector-aware timeout escalation and retry behavior in `_post_graphql` for script-based retrieval.
- Why: Keeps runtime behavior consistent between API retrieval and validation runs.

## 2026-04-16 13:27:19 CDT
- File: [docs/SESSION_CHANGELOG.md](/mnt/c/Patent_Wizard/docs/SESSION_CHANGELOG.md)
- Lines changed: full file rewritten to normalize entry format.
- Problem: Existing entries used a `Reason` field but did not consistently separate issue symptoms from implementation details.
- Change: Standardized entries to explicit `Problem / Change / Why` sections while preserving timestamped file and line references.
- Why: Makes handoff/debug context faster to scan and reduces ambiguity about the root issue vs the implemented fix.

- File: [AGENTS.md](/mnt/c/Patent_Wizard/AGENTS.md)
- Lines changed: new file.
- Problem: No repository-level instruction guaranteed that Codex/other LLMs would consistently log modifications.
- Change: Added mandatory agent workflow requiring changelog updates for every task, with a strict entry template.
- Why: Enforces a persistent audit trail across model runs and reduces lost context between sessions.

## 2026-04-16 13:24:01 CDT
- File: [frontend/src/Results.jsx](/mnt/c/Patent_Wizard/frontend/src/Results.jsx)
- Lines changed: removed filter-based `rag` override in request payload at [frontend/src/Results.jsx:324](/mnt/c/Patent_Wizard/frontend/src/Results.jsx:324); removed now-unused `hasAnyFilterParams` helper.
- Problem: Patent-level search requests with filters were forcing `rag=false`, which made the request bypass graph eligibility.
- Change: Removed the filter-driven `rag` override from the frontend request payload and deleted the unused helper.
- Why: Preserves the default `rag=true` behavior unless explicitly turned off by the caller.

## 2026-04-16 13:23:24 CDT
- File: [backend/app/api/search.py](/mnt/c/Patent_Wizard/backend/app/api/search.py)
- Lines changed: [backend/app/api/search.py:20](/mnt/c/Patent_Wizard/backend/app/api/search.py:20), [backend/app/api/search.py:27](/mnt/c/Patent_Wizard/backend/app/api/search.py:27), [backend/app/api/search.py:30](/mnt/c/Patent_Wizard/backend/app/api/search.py:30), [backend/app/api/search.py:58](/mnt/c/Patent_Wizard/backend/app/api/search.py:58), [backend/app/api/search.py:136](/mnt/c/Patent_Wizard/backend/app/api/search.py:136), [backend/app/api/search.py:140](/mnt/c/Patent_Wizard/backend/app/api/search.py:140), [backend/app/api/search.py:158](/mnt/c/Patent_Wizard/backend/app/api/search.py:158), [backend/app/api/search.py:192](/mnt/c/Patent_Wizard/backend/app/api/search.py:192), [backend/app/api/search.py:230](/mnt/c/Patent_Wizard/backend/app/api/search.py:230), [backend/app/api/search.py:286](/mnt/c/Patent_Wizard/backend/app/api/search.py:286), [backend/app/api/search.py:291](/mnt/c/Patent_Wizard/backend/app/api/search.py:291), [backend/app/api/search.py:305](/mnt/c/Patent_Wizard/backend/app/api/search.py:305).
- Problem: It was difficult to diagnose why requests took direct retrieval paths, and graph eligibility was constrained more than intended.
- Change: Added request-level debug logging and a `debug_trace` flag, broadened graph eligibility logic, and made response mode labeling scope-agnostic.
- Why: Improves branch-level observability and aligns backend pathing with expected RAG behavior.

- File: [frontend/src/lib/api.js](/mnt/c/Patent_Wizard/frontend/src/lib/api.js)
- Lines changed: removed patent-scope forced `rag: false` behavior around [frontend/src/lib/api.js:25](/mnt/c/Patent_Wizard/frontend/src/lib/api.js:25).
- Problem: Patent-scope requests defaulted to `rag=false` even when not intended.
- Change: Kept `rag` defaulting to `true` (`scopedOpts.rag ?? true`) unless caller explicitly sets a value.
- Why: Prevents silent mode downgrades and keeps frontend defaults consistent across scopes.

## 2026-04-16 12:34:00 CDT
- File: [backend/app/scripts/retrieve_rerank.py](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py)
- Lines changed: [backend/app/scripts/retrieve_rerank.py:404](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:404), [backend/app/scripts/retrieve_rerank.py:411](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:411), [backend/app/scripts/retrieve_rerank.py:445](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:445), [backend/app/scripts/retrieve_rerank.py:710](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:710), [backend/app/scripts/retrieve_rerank.py:728](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:728), [backend/app/scripts/retrieve_rerank.py:782](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:782), [backend/app/scripts/retrieve_rerank.py:1303](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:1303), [backend/app/scripts/retrieve_rerank.py:1386](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:1386), [backend/app/scripts/retrieve_rerank.py:1448](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:1448), [backend/app/scripts/retrieve_rerank.py:1498](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:1498), [backend/app/scripts/retrieve_rerank.py:1535](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:1535).
- Problem: QREL claims that map to chunked claim IDs were underreported in MaxSim/rank diagnostics.
- Change: Added base-claim canonicalization, chunk-aware object-id resolution, and expanded per-query/per-topk diagnostics for candidate and reranked paths.
- Why: Ensures chunked relevant claims are evaluated consistently and diagnostic fields cover both retrieval stages.
