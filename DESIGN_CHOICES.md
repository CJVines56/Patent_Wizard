# Design Choices

## LMDB Storage Format
Decision: Store ColBERT token vectors as NumPy `.npy` bytes (uncompressed).
Rationale: Self-describing dtype/shape with reasonable overhead; simpler to decode correctly.
Alternatives:
- Raw float32 bytes
  - Pros: Fastest, smallest overhead.
  - Cons: Must store/track dtype + shape separately; easier to misdecode.
- JSON
  - Pros: Human-readable.
  - Cons: Huge size, slow IO/parse, not practical for large vectors.

## LMDB Compression
Decision: No compression initially.
Rationale: Highest retrieval quality and simplest pipeline; measure performance first.
Alternatives:
- Float16
  - Pros: ~2x smaller, typically minimal quality loss.
  - Cons: Some precision loss; extra conversion step.
- INT8 / PQ
  - Pros: 4x-16x smaller.
  - Cons: More quality loss, higher complexity.

## Token Dimensionality Reduction (Experimental)
Decision: When producing 128-d token vectors, apply an explicit linear projection
from 768 -> 128 with no bias, then L2-normalize per token.
Rationale: Provides a deterministic, explicit reduction step without assuming
model-specific ColBERT heads or hidden configs.
Notes:
- The projection layer is initialized once and reused.
- This is a temporary stand-in for a true ColBERT head and can be swapped later.

## Token Vector Variants
Decision: Store four LMDB variants per claim ID:
- 768_f32
- 768_f16
- 128_f32
- 128_f16
Rationale: Enables empirical comparisons of size/quality tradeoffs without
re-ingesting claims.

## LMDB Keying Strategy
Decision: Use the Weaviate object UUID as the LMDB key.
Rationale: Direct mapping between Weaviate chunk records and ColBERT vectors.
Alternatives:
- `doc_id:chunk_index`
  - Pros: Human-readable, deterministic.
  - Cons: Diverges from Weaviate IDs; requires extra mapping layer.
- Separate `chunk_id`
  - Pros: Explicit and portable.
  - Cons: Another ID to generate/maintain.

## LMDB Sharding
Decision: Single LMDB file to start.
Rationale: Simpler to manage and integrate; sharding can be added when corpus grows.
Alternatives:
- Per-shard LMDB (e.g., by hash prefix or date range)
  - Pros: Smaller files, better cache locality, easier partial rebuilds.
  - Cons: Routing logic, more handles, more operational complexity.

## Write Stage
Decision: Write LMDB entries during the Weaviate store step.
Rationale: Weaviate UUID is available at insert time; keeps embedding and storage concerns separated.
Alternatives:
- Write during embedding
  - Pros: Immediate persistence while vectors are in memory.
  - Cons: Requires stable ID earlier; tighter coupling in the pipeline.

## Target LMDB Location
Decision: Use `backend/lmdb/`.
Rationale: Clear top-level data location, separate from app code.
Alternatives:
- `backend/app/lmdb/`
  - Pros: Co-locates with application code.
  - Cons: Mixes data with code.

## Retrieval Workflow (Target)
1) Download and chunk
2) Embed with ColBERT
3) Weaviate applies MUVERA encoding to multi-vector field at index time
4) Retrieve Weaviate UUIDs and load ColBERT vectors from LMDB by UUID
# MUVERA multi-vector indexing (Weaviate)
Weaviate’s MUVERA expects **multi-vector** inputs and encodes them internally into fixed-length vectors for indexing.

Doc-aligned config (local client):

```python
from weaviate.classes.config import Configure

client.collections.create(
    name="PatentData",
    properties=[...],
    vector_config=[
        Configure.MultiVectors.self_provided(
            name="colbert",
            encoding=Configure.VectorIndex.MultiVector.Encoding.muvera(),
        )
    ],
)
```

Insert usage:

```python
collection.data.insert(
    properties={...},
    vector={"colbert": multi_vector_colbert},
)
```

Notes:
- You must send **multi‑vector ColBERT** at ingest **and** query time.
- MUVERA encodes internally; you don’t store a separate “muvera” vector.

Weaviate batching
- `store.py` uses `collection.data.insert_many` to batch inserts.
- Batch size is controlled by `WEAVIATE_BATCH_SIZE` (default 128).

LMDB ColBERT storage
- ColBERT token vectors are stored in LMDB for reranking.
- Stored as FP16 by default (`LMDB_VECTOR_DTYPE=float16`) to save ~2× space.
- Map size grows automatically on `MDB_MAP_FULL` by `LMDB_MAP_GROW_GB` (default 10 GB).
