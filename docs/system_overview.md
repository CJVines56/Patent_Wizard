# Patent Wizard – System Overview

## 1. Data Ingestion & Chunking (`backend/app/services/download.py`)

1. `bulk_dataset_download()` orchestrates pulling USPTO weekly archives (ZIP/TAR). It now accepts `batch_size` + `on_batch` so callers can stream chunk lists in manageable batches instead of holding the entire weekly dump in memory.
2. For each patent XML:
   - Metadata (`doc_id`, `title`, `filing_date`, CPC classification, inventors, etc.) is extracted.
   - Text sections are converted to simplified rich text via `elem_to_rich_text()` so inline formatting (e.g., `<sup>`) survives.
   - `_fig_refs_in_elem()` identifies figure references in description/claim paragraphs. It collects both `idref` attributes (e.g., `DRAWINGS-0001`) and any numeric mentions (“FIG. 1”), which later map to specific figure assets.
   - `_collect_figure_assets()` scans `<drawings>/<figure>/<img>` tags and reads matching image files from the archive. Each figure captures filename, referenced IDs, figure number, and raw bytes.
   - `_attach_fig_images_to_chunks()` takes the chunks just emitted for that patent, resolves their `fig_refs` against the collected assets, base64-encodes the image bytes, and attaches a `fig_images` array directly on each chunk.
3. Sampling helpers (`write_random_patent_sample`, `write_patent_sample_by_ids`) write per-patent Markdown folders under `uspto_bulk_data/sampled`, drop the original image files into `images/`, and emit `backend/app/db/sample_chunks.jsonl` so the demo backend has material to load.

Key helpers:

- `make_parser()` – hardened `lxml` parser (no DTD/entities, `huge_tree`, recover toggles).
- `iter_uspto_subdocs()` – streaming generator that slices the massive weekly XML into discrete `<us-patent-application>` blobs without parsing.
- `rich_to_plain()` – strips the minimal rich text back to plain text; used downstream by embedding, dataset catalog, and UI snippets.

## 2. Embedding (`backend/app/embed.py`)

1. Loads the ColBERTv2 tokenizer/model (Hugging Face) once at import.
2. `embed_chunks()` expects a list of chunk dicts. For each chunk:
   - `rich_to_plain()` cleans the text.
   - The tokenizer truncates/pads to `max_length` and the ColBERT model produces contextual embeddings.
   - The mean of token embeddings (per chunk) becomes a dense vector saved back onto the chunk (`chunk["embedding"]`).
3. `embed_query()` mirrors the chunk pathway for user queries so retrieval can operate in the same vector space.

## 3. Storage (`backend/app/store.py`)

1. Uses the Weaviate Python client (`weaviate.connect_to_local`) to talk to a local vector database.
2. `ensure_collection()` guarantees the `PatentData` collection exists with schema fields: document metadata, chunk text, and `fig_images` (JSON string that carries base64 images).
3. `store_embeddings()` takes the enriched chunk dicts (now with vectors + metadata) and inserts them into Weaviate. The frontend ultimately queries through the FastAPI layer rather than directly from Weaviate in this POC, but the storage step makes the vector data available for future semantic retrieval work.

## 4. Demo Dataset Loader (`backend/app/db/dataset.py`)

- `_load_sampled_chunks()` reads the JSONL emitted by the download step and groups chunks by `doc_id`.
- `_build_catalog_from_chunks()` builds lightweight catalog entries (title, snippet, search_text, metadata) for each patent. It also collects up to six unique `fig_images` per doc so the API can surface figure previews without having to stream the full chunk list.
- The resulting `CATALOG` is an in-memory list used by the naive retrieval service.

## 5. Retrieval & API (`backend/app/services/retrieval.py`, `backend/app/api/search.py`)

1. `naive_filter()` performs a case-insensitive substring match against `title`, `snippet`, and `search_text`. It returns Pydantic `SearchItem` objects (including `fig_images`).
2. `/api/search` (`backend/app/api/search.py`):
   - Accepts `q`, `k`, `k_extra`, and `rag` flags.
   - Calls `naive_filter()`, slices the top-`k` “cited” items, and exposes the rest as “other” results.
   - If `rag=true` (default), it calls `make_fake_answer()` (placeholder orchestrator) to generate a mock RAG answer referencing the cited items with `[1]`, `[2]` style citations.
   - Returns a `SearchResponse` envelope that the frontend expects.

## 6. Frontend (`frontend/src`)

1. `src/lib/api.js` – wraps the `/api/search` call, enforcing `rag=true`.
2. `Results.jsx` – main results page:
   - Reads the `q` query parameter, fetches from the API, and renders state (loading/error/result).
   - Builds `figureEntries` from any `fig_images` found on the cited items and shows them in a “Referenced Figures” card above the answer card. Each entry renders the base64 image and labels it with the figure ID or filename.
   - Displays the query text, fake RAG answer, and an inline `SearchBar` for quick refinements.
   - A fixed sidebar lists cited patents with metadata and links to Google Patents when possible.
3. Other components/tabs (e.g., `App.jsx`, `components/`, etc.) form the landing/search experience but the RAG visualization lives primarily in `Results.jsx`.

## 7. Putting It All Together

1. **Run the download/sampling pipeline** (`bulk_dataset_download` or your existing command) to refresh the Markdown samples and `sample_chunks.jsonl`. This step now attaches per-chunk `fig_images` so later stages can display figures inline.
2. **Optionally embed & store** – call `embed_chunks` followed by `store_embeddings` to push vectors/metadata into Weaviate when you want semantic retrieval beyond the demo dataset.
3. **Start FastAPI** (`uvicorn backend.app.main:app --reload`). The app loads `CATALOG` from `sample_chunks.jsonl`, exposing `/api/search`.
4. **Start the Vite frontend** – it calls the FastAPI endpoint and renders both the textual answer and figure gallery.

This document should give you the narrative to describe every phase of the workflow—downloading USPTO data, extracting & annotating chunks, embedding them, persisting vectors, serving them via the API, and finally showing the combined RAG + figure experience in the UI.
