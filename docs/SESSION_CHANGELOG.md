# Session Changelog

## 2026-04-21 16:26:44 CDT
- File: [backend/app/api/search.py](C:/Users/Optim/Patent_Wizard/backend/app/api/search.py)
- Lines changed: `_retrieve_payload` helper inside the `/api/search` handler.
- Problem: the retrieval helper built a partially populated dict and then indexed optional keys, which could raise `KeyError`.
- Change: passed retrieval arguments directly into `retrieve_context()` and logged the same values explicitly.
- Why: removes the missing-key failure mode and keeps the call aligned with the helper signature.

## 2026-04-21 13:58:30 CDT
- File: [backend/orchestrator/tools.py](C:/Users/Optim/Patent_Wizard/backend/orchestrator/tools.py)
- Lines changed: top-level import block.
- Problem: `patent_miner_classes` was imported as a top-level module, which failed when the API imported `backend.orchestrator.tools`.
- Change: Switched the import to `backend.orchestrator.patent_miner_classes`.
- Why: Makes the orchestrator module resolvable through the package import path used by the API.

- File: [backend/orchestrator/nodes.py](C:/Users/Optim/Patent_Wizard/backend/orchestrator/nodes.py)
- Lines changed: top-level import block.
- Problem: `patent_miner_classes` was imported as a top-level module, which failed for the same reason as `tools.py`.
- Change: Switched the import to `backend.orchestrator.patent_miner_classes`.
- Why: Keeps orchestrator state types importable from the API entrypoint.

- File: [backend/orchestrator/graph.py](C:/Users/Optim/Patent_Wizard/backend/orchestrator/graph.py)
- Lines changed: top-level import block.
- Problem: sibling imports used bare module names, so package loading could not resolve `nodes` and `tools`.
- Change: Switched the imports to package-qualified `backend.orchestrator.*` paths.
- Why: Ensures the graph module can be imported consistently through `backend.orchestrator.graph`.

- File: [backend/app/main.py](C:/Users/Optim/Patent_Wizard/backend/app/main.py)
- Lines changed: startup import order near the env bootstrap block.
- Problem: orchestrator-dependent modules were imported before the orchestrator env was loaded, so `vector_config.py` could raise on missing `PROJECTION_PATH`.
- Change: Moved the router imports below the orchestrator env load so config is available before `search.py` imports `backend.orchestrator.tools`.
- Why: Makes API startup work in a clean process without requiring env vars to be preloaded externally.

- File: [backend/app/api/eval.py](C:/Users/Optim/Patent_Wizard/backend/app/api/eval.py)
- Lines changed: top-level `evaluate` import and `qrels_eval` handler import path.
- Problem: importing the eval router forced the entire retrieval/eval stack to load during API startup, which pulled in heavyweight model dependencies unnecessarily.
- Change: Moved the `evaluate` import inside the `qrels_eval` handler.
- Why: Defers expensive dependencies until the eval endpoint is actually called and keeps the API boot path lighter.

## 2026-04-20 12:02:09 CDT
- File: [backend/app/scripts/retrieve_rerank.py](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py)
- Lines changed: fusion config/env handling near [backend/app/scripts/retrieve_rerank.py:78](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:78), `_query_claim_rows` at [backend/app/scripts/retrieve_rerank.py:347](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:347), and client-side hybrid helpers at [backend/app/scripts/retrieve_rerank.py:615](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:615) through [backend/app/scripts/retrieve_rerank.py:868](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py:868).
- Problem: the client-side hybrid fallback fused BM25 and vector legs with rank-based RRF, which did not approximate Weaviate's relative-score hybrid behavior and offered no raw/normalized score diagnostics.
- Change: Added score-based relative fusion for the fallback path, requested BM25 raw scores from Weaviate, converted vector distance to higher-is-better relevance via `-distance`, kept the old RRF helper behind `CLIENT_HYBRID_FUSION_METHOD`, and added one-query debug logging for raw, normalized, fused, and source-leg metadata.
- Why: Makes fallback hybrid ranking closer to Weaviate-style score blending while preserving the ability to compare against the older RRF behavior.

- File: [backend/orchestrator/tools.py](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py)
- Lines changed: client hybrid config near [backend/orchestrator/tools.py:84](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py:84), `_query_claim_rows` at [backend/orchestrator/tools.py:659](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py:659), and hybrid fallback helpers at [backend/orchestrator/tools.py:719](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py:719) through [backend/orchestrator/tools.py:963](/mnt/c/Patent_Wizard/backend/orchestrator/tools.py:963).
- Problem: the orchestrator retrieval path had its own copy of the old RRF-only client-side hybrid fallback, so API retrieval would diverge from the script/eval path.
- Change: Mirrored the relative-score client-side fusion, BM25 score fetching, debug logging, and `CLIENT_HYBRID_FUSION_METHOD` switch into the orchestrator fallback path without changing successful server-side hybrid retrieval.
- Why: Keeps script-based evaluation and orchestrator retrieval aligned when hybrid falls back client-side.

- File: [tests/test_retrieve_rerank_eval.py](/mnt/c/Patent_Wizard/tests/test_retrieve_rerank_eval.py)
- Lines changed: added hybrid fusion helper tests at [tests/test_retrieve_rerank_eval.py:95](/mnt/c/Patent_Wizard/tests/test_retrieve_rerank_eval.py:95) through [tests/test_retrieve_rerank_eval.py:179](/mnt/c/Patent_Wizard/tests/test_retrieve_rerank_eval.py:179).
- Problem: there was no regression coverage for overlapping candidates, single-leg candidates, equal-score normalization, or preservation of the old RRF helper.
- Change: Added focused unit tests covering relative-score fusion ordering, degenerate equal-score handling, and the continued availability of the RRF fusion path.
- Why: Reduces the risk of silently breaking the new fallback math or losing the comparison path.

- File: [docs/SESSION_CHANGELOG.md](/mnt/c/Patent_Wizard/docs/SESSION_CHANGELOG.md)
- Lines changed: new top-of-file session entry.
- Problem: this task changed retrieval and test files without a matching timestamped audit entry.
- Change: Logged the hybrid fallback fusion update and its test coverage.
- Why: Preserves the repository handoff trail required by `AGENTS.md`.

## 2026-04-20 11:26:23 CDT
- File: [AGENTS.md](/mnt/c/Patent_Wizard/AGENTS.md)
- Lines changed: `Required On Every User Request` and `Scope`.
- Problem: the agent policy required changelog entries even for command-only or analysis-only responses with no repository edits.
- Change: Removed the no-file-change logging requirement and explicitly disallowed changelog entries for no-file-change responses.
- Why: Keeps `docs/SESSION_CHANGELOG.md` focused on actual repository modifications.

- File: [docs/SESSION_CHANGELOG.md](/mnt/c/Patent_Wizard/docs/SESSION_CHANGELOG.md)
- Lines changed: removed the recent no-file-change trace sections and added this policy-change entry.
- Problem: the changelog had accumulated command-only trace entries that were noise rather than durable file-change history.
- Change: Deleted the command-only/no-file-change sections from 2026-04-19 through 2026-04-20 and logged the cleanup.
- Why: Restores the changelog as a concise audit trail for substantive repo changes.

## 2026-04-19 16:24:24 CDT
- File: [backend/validation/doc_level_qrels.jsonl](/mnt/c/Patent_Wizard/backend/validation/doc_level_qrels.jsonl)
- Lines changed: new file with 40 JSONL rows derived from `backend/validation/qrels.jsonl`.
- Problem: the repository only had the older claim-level qrels filename, which made it unclear which file should be used for explicit patent-level evaluation inputs.
- Change: Added a separate doc-level qrels file named `doc_level_qrels.jsonl` containing `relevant_doc_ids` for the same query set.
- Why: Preserves the original claim-level file while giving future eval runs and agents a clearly named patent-level qrels input.

- File: [docs/SESSION_CHANGELOG.md](/mnt/c/Patent_Wizard/docs/SESSION_CHANGELOG.md)
- Lines changed: new top-of-file session entry.
- Problem: this task added a validation artifact and needed a matching timestamped audit entry.
- Change: Logged the new doc-level qrels file creation.
- Why: Keeps agent handoff history consistent with `AGENTS.md`.

## 2026-04-19 16:11:25 CDT
- File: [backend/app/scripts/retrieve_rerank.py](/mnt/c/Patent_Wizard/backend/app/scripts/retrieve_rerank.py)
- Lines changed: patent-level qrels normalization and evaluation flow around `_extract_relevant_doc_ids`, `evaluate`, per-query CSV/XLSX output fields, and `--filter-missing-qrels` help text.
- Problem: qrels evaluation still scored relevance at the claim level, so a relevant patent could be present in the top results without counting as a hit unless the expected claim id matched.
- Change: Normalized qrels rows to patent `doc_id` relevance, deduped ranked results by patent for scoring, updated diagnostics to report relevant patent ids/ranks, and switched missing-qrels filtering to patent presence checks.
- Why: Makes hit@10 and related metrics reflect patent-level retrieval success instead of over-penalizing claim-level mismatches.

- File: [backend/app/scripts/qrels_mode_sweep_excel.py](/mnt/c/Patent_Wizard/backend/app/scripts/qrels_mode_sweep_excel.py)
- Lines changed: `--filter-missing-qrels` CLI help text.
- Problem: sweep help text still described the filter in terms of relevant claims.
- Change: Updated the wording to relevant patents.
- Why: Keeps the sweep script aligned with the new patent-level evaluation behavior.

- File: [README.MD](/mnt/c/Patent_Wizard/README.MD)
- Lines changed: qrels evaluation notes near the single-file qrels example and API notes section.
- Problem: repository docs did not state that qrels are now normalized and scored at the patent level.
- Change: Documented that evaluation accepts either `relevant_doc_ids` or `relevant_claim_ids` and scores against patent `doc_id`s.
- Why: Reduces ambiguity for future runs and for agents reusing the eval tooling.

- File: [tests/test_retrieve_rerank_eval.py](/mnt/c/Patent_Wizard/tests/test_retrieve_rerank_eval.py)
- Lines changed: new file.
- Problem: there was no focused regression coverage for claim-based qrels being normalized into patent-level metrics.
- Change: Added tests covering doc-id extraction from qrels and patent-level scoring/output behavior.
- Why: Helps prevent the eval path from silently drifting back to claim-level semantics.

- File: [docs/SESSION_CHANGELOG.md](/mnt/c/Patent_Wizard/docs/SESSION_CHANGELOG.md)
- Lines changed: new top-of-file session entry.
- Problem: the prior task changed files without appending the required timestamped changelog entry.
- Change: Added a backfilled session entry for the patent-level qrels work.
- Why: Restores the audit trail expected by `AGENTS.md` for future agent handoffs.

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
