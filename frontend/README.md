# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Christian Edits

Session date: 2026-03-05

This project frontend was updated with the following UX and dev-workflow changes:

- Added/confirmed app routing behavior with `Home` at `/` and `Results` at `/search`.
- Added a shared **Dev Tuning** system for frontend-only retrieval knobs:
  - `k`, `k_extra`, `alpha`, `retrieval_candidates`, `rerank_k`
  - Defaults set to: `k=10`, `k_extra=10`, `alpha=0.5`, `retrieval_candidates=400`, `rerank_k=200`
  - Stored in `localStorage` via `patent_miner_dev_tuning_v2`
- Added a reusable **Dev Tuning dropdown panel** component fixed at left-center on both hero and results pages.
- Updated API client to pass through tuning params to `/api/search` for future backend wiring (`k`, `k_extra`, `alpha`, `retrieval_k`, `retrieval_candidates`, `rerank_k`, `rerank_shard`).
- Added **Results-page preview fallback** when API is unavailable:
  - Shows mock results
  - Keeps page inspectable for frontend design/testing
- Added **resizable right Results panel**:
  - Drag left edge to resize
  - Width is persisted in `localStorage` (`patent_miner_results_panel_width_v1`)
- Added **Results/Filters tabs** in the right panel.
- Added frontend-only **Filters tab** for metadata filtering:
  - Author, CPC/classification, filing date range, kind, claim type, doc_id
  - Dynamic dropdown options from loaded result metadata
- Added **scrollable message history** on the left content area:
  - Each query/response is saved during session
  - Clicking a past entry restores that response view
- Standardized status banner layout/spacing for error/preview messages.

Primary files changed:

- `src/Home.jsx`
- `src/Results.jsx`
- `src/lib/api.js`
- `src/lib/devTuning.js` (new)
- `src/components/DevTuningPanel.jsx` (new)
- `src/App.jsx` (cleanup from early debug edits)
