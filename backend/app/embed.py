# Recall: A vector represents text through numbers. A vector's "meaning" is its direction.      #
# Different direction, different meaning, similar direction, similar meaning, etc. Vectors      #
# themselves contain no labels, literally only text meaning.
# We will use a vector database (with FAISS?) and an sql database together.

from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from backend.app.env_bootstrap import coerce_path_string, load_project_env
from backend.app.services.download import rich_to_plain
from backend.app.vector_config import (
    ENABLED_COLBERT_VARIANTS,
    PRIMARY_COLBERT_VARIANT,
    PROJECTION_MODE,
    PROJECTION_PATH,
    TOKEN_VECTOR_DIM,
    TOKEN_VECTOR_DTYPE,
    assert_128_variant,
)
from contextlib import nullcontext
from pathlib import Path
import json
import gzip
import os
import re
import warnings
from typing import Any
import numpy as np

load_project_env()

warnings.filterwarnings(
    "ignore",
    message="Token indices sequence length is longer than the specified maximum sequence length.*",
)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
warnings.filterwarnings("ignore", category=FutureWarning, module=r"colbert\..*")
warnings.filterwarnings(
    "ignore",
    message="`torch.jit.script` is deprecated.*",
)
warnings.filterwarnings(
    "ignore",
    message="`torch.cuda.amp.GradScaler.*` is deprecated.*",
)
warnings.filterwarnings(
    "ignore",
    message="`torch.cuda.amp.autocast.*` is deprecated.*",
)
warnings.filterwarnings(
    "ignore",
    message="builtin type SwigPyPacked has no __module__ attribute",
)
warnings.filterwarnings(
    "ignore",
    message="builtin type SwigPyObject has no __module__ attribute",
)
warnings.filterwarnings(
    "ignore",
    message="builtin type swigvarlink has no __module__ attribute",
)
warnings.filterwarnings(
    "ignore",
    message="`huggingface_hub` cache-system uses symlinks by default.*",
)

DEFAULT_MODEL_NAME = "colbert-ir/colbertv2.0"


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _iter_hf_cache_roots() -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()

    def add(candidate: Path | None):
        if candidate is None:
            return
        key = str(candidate)
        if key in seen:
            return
        seen.add(key)
        roots.append(candidate)

    hub_cache = coerce_path_string(os.environ.get("HUGGINGFACE_HUB_CACHE"))
    add(hub_cache)

    hf_home = coerce_path_string(os.environ.get("HF_HOME"))
    if hf_home is not None:
        add(hf_home / "hub")

    add(Path.home() / ".cache" / "huggingface" / "hub")

    windows_users = Path("/mnt/c/Users")
    if windows_users.exists():
        for user_dir in sorted(p for p in windows_users.iterdir() if p.is_dir()):
            add(user_dir / ".cache" / "huggingface" / "hub")

    return roots


def _discover_local_colbert_snapshot() -> Path | None:
    for cache_root in _iter_hf_cache_roots():
        model_root = cache_root / "models--colbert-ir--colbertv2.0"
        if not model_root.exists():
            continue

        ref_main = model_root / "refs" / "main"
        if ref_main.exists():
            snapshot_name = ref_main.read_text(encoding="utf-8").strip()
            if snapshot_name:
                snapshot_path = model_root / "snapshots" / snapshot_name
                if snapshot_path.exists():
                    return snapshot_path

        snapshots_dir = model_root / "snapshots"
        if not snapshots_dir.exists():
            continue
        snapshots = sorted(
            (p for p in snapshots_dir.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if snapshots:
            return snapshots[0]

    return None


def _resolve_model_name() -> str:
    raw = (
        os.environ.get("COLBERT_MODEL_PATH")
        or os.environ.get("COLBERT_MODEL_NAME")
        or os.environ.get("MODEL_NAME")
        or ""
    ).strip()
    if raw:
        candidate = coerce_path_string(raw)
        if candidate is not None and candidate.exists():
            return str(candidate)
        return raw

    discovered = _discover_local_colbert_snapshot()
    if discovered is not None:
        return str(discovered)

    return DEFAULT_MODEL_NAME


MODEL_NAME = _resolve_model_name()


def _resolve_device() -> torch.device:
    requested = (os.environ.get("EMBED_DEVICE") or "auto").strip().lower()
    if requested and requested != "auto":
        device = torch.device(requested)
        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("EMBED_DEVICE requests CUDA, but torch.cuda.is_available() is false.")
        return device
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


DEVICE = _resolve_device()
EMBED_USE_AUTOCAST = DEVICE.type == "cuda" and _env_flag("EMBED_USE_AUTOCAST", True)
EMBED_BATCH_SIZE = max(1, int(os.environ.get("EMBED_BATCH_SIZE", "16" if DEVICE.type == "cuda" else "4")))
TOKENIZER_PAD_MULTIPLE = 8 if DEVICE.type == "cuda" else None

if hasattr(torch, "set_float32_matmul_precision"):
    try:
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass
if DEVICE.type == "cuda":
    torch.backends.cuda.matmul.allow_tf32 = True
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True


def _device_summary() -> str:
    if DEVICE.type == "cuda":
        try:
            return f"{DEVICE} ({torch.cuda.get_device_name(DEVICE)})"
        except Exception:
            return str(DEVICE)
    return str(DEVICE)


def _model_exec_context():
    if EMBED_USE_AUTOCAST:
        return torch.autocast(device_type="cuda", dtype=torch.float16)
    return nullcontext()
# Remember to alter model path anytime you download a new snapshot!
# MODEL_PATH = r"C:/Users/Christian Casteel/.cache/huggingface/hub/models--colbert-ir--colbertv2.0/snapshots/c1e84128e85ef755c096a95bdb06b47793b13acf"

LOCAL_ONLY = bool(
    os.environ.get("TRANSFORMERS_OFFLINE") == "1"
    or os.environ.get("HF_HUB_OFFLINE") == "1"
    or os.environ.get("LOCAL_MODEL_ONLY") == "1"
    or Path(MODEL_NAME).exists()
)

model_path = MODEL_NAME
# The block below will check for updates to colbert, and if there are newer versions, download  #
# them locally to the machine. Currently disabled for the sake of quick demos                   #
print("Checking for newer versions...")
# This finds the tokenizer associated with ColBERTv2. "from_pretrained" searches for the model  #
# locally, and if it is not present, it downloads it from the HuggingFace hub.                  #
tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    local_files_only=LOCAL_ONLY,
)

model = AutoModel.from_pretrained(
    model_path,
    local_files_only=LOCAL_ONLY,
).to(DEVICE)

print("Model and tokenizer loaded successfully from scratch!")                                           #

REBALANCE_OVERLAP_TOKENS = int(os.environ.get("REBALANCE_OVERLAP_TOKENS", "30"))
COLBERT_DOC_MAXLEN = int(os.environ.get("COLBERT_DOC_MAXLEN", "180"))
COLBERT_QUERY_MAXLEN = int(os.environ.get("COLBERT_QUERY_MAXLEN", "32"))
COLBERT_VARIANTS = ",".join(sorted(ENABLED_COLBERT_VARIANTS))

_PROJECTION_MATRIX: torch.Tensor | None = None
_PROJECTION_INFO: dict[str, str | tuple[int, int]] = {}


def _extract_projection_tensor(obj: Any) -> torch.Tensor:
    if isinstance(obj, torch.Tensor):
        return obj
    if isinstance(obj, dict) and "state_dict" in obj and isinstance(obj["state_dict"], dict):
        obj = obj["state_dict"]
    if isinstance(obj, dict):
        preferred = [
            "projection",
            "projection_weight",
            "projection.weight",
            "linear.weight",
            "proj.weight",
            "weight",
        ]
        for key in preferred:
            value = obj.get(key)
            if isinstance(value, torch.Tensor) and value.ndim == 2:
                return value
        two_d = [(k, v) for k, v in obj.items() if isinstance(v, torch.Tensor) and v.ndim == 2]
        if len(two_d) == 1:
            return two_d[0][1]
        found = [k for k, _ in two_d]
        raise ValueError(
            f"Could not resolve unique 2D projection matrix from {PROJECTION_PATH}. "
            f"Found candidates: {found}"
        )
    raise ValueError(
        f"Unsupported projection checkpoint format in {PROJECTION_PATH}. "
        "Expected Tensor or dict containing a 2D weight matrix."
    )


def _load_trained_projection_matrix() -> torch.Tensor:
    global _PROJECTION_MATRIX, _PROJECTION_INFO
    if _PROJECTION_MATRIX is not None:
        return _PROJECTION_MATRIX

    payload = torch.load(PROJECTION_PATH, map_location="cpu")
    matrix = _extract_projection_tensor(payload)
    if matrix.dtype not in {torch.float16, torch.float32}:
        raise ValueError(
            f"Projection matrix dtype must be float16 or float32, got {matrix.dtype} "
            f"from {PROJECTION_PATH}."
        )
    if matrix.ndim != 2:
        raise ValueError(f"Projection matrix must be rank-2, got shape={tuple(matrix.shape)}.")

    original_shape = tuple(matrix.shape)
    transposed = False
    if original_shape == (768, 128):
        matrix = matrix.transpose(0, 1).contiguous()
        transposed = True
    elif original_shape != (128, 768):
        raise ValueError(
            f"Projection matrix shape must be [128,768] (or [768,128] transposed). "
            f"Got {original_shape} from {PROJECTION_PATH}."
        )

    _PROJECTION_MATRIX = matrix.to(device=DEVICE)
    _PROJECTION_INFO = {
        "path": str(PROJECTION_PATH),
        "shape": tuple(_PROJECTION_MATRIX.shape),
        "dtype": str(_PROJECTION_MATRIX.dtype),
        "device": str(_PROJECTION_MATRIX.device),
        "transposed": str(transposed),
    }
    return _PROJECTION_MATRIX


def _projection_summary() -> str:
    proj = _load_trained_projection_matrix()
    shape = tuple(proj.shape)
    return (
        f"model={MODEL_NAME} projection_mode={PROJECTION_MODE} "
        f"projection_path={PROJECTION_PATH} projection_shape={shape} "
        f"final_token_dim={TOKEN_VECTOR_DIM} token_dtype={TOKEN_VECTOR_DTYPE} "
        f"device={_device_summary()} batch_size={EMBED_BATCH_SIZE} autocast={EMBED_USE_AUTOCAST}"
    )


def _project_tokens_128(masked_token_embeddings: torch.Tensor) -> torch.Tensor:
    if masked_token_embeddings.ndim != 2 or masked_token_embeddings.shape[1] != 768:
        raise ValueError(
            f"Expected token embeddings shape [T,768] before projection. "
            f"Got {tuple(masked_token_embeddings.shape)}."
        )
    proj = _load_trained_projection_matrix()
    tokens = masked_token_embeddings.to(device=DEVICE, dtype=proj.dtype)
    projected = tokens @ proj.transpose(0, 1)
    if projected.ndim != 2 or projected.shape[1] != 128:
        raise ValueError(
            f"Projected token embeddings must have shape [T,128]. Got {tuple(projected.shape)}."
        )
    return F.normalize(projected.to(torch.float32), p=2, dim=1)


def _build_token_variants(projected_token_vectors: torch.Tensor) -> dict[str, object]:
    if projected_token_vectors.ndim != 2 or projected_token_vectors.shape[1] != 128:
        raise ValueError(
            f"Token vectors must be [T,128] before variant export. "
            f"Got {tuple(projected_token_vectors.shape)}."
        )
    variants: dict[str, object] = {}
    if "128_f32" in ENABLED_COLBERT_VARIANTS:
        variants["128_f32"] = projected_token_vectors.to(torch.float32).detach().cpu().numpy()
    if "128_f16" in ENABLED_COLBERT_VARIANTS:
        variants["128_f16"] = projected_token_vectors.to(torch.float16).detach().cpu().numpy()
    if not variants:
        raise ValueError(
            f"No enabled 128-d variants found in configuration: {sorted(ENABLED_COLBERT_VARIANTS)}"
        )
    return variants


def normalize_text_for_embedding(text: str | None) -> str:
    """
    Shared normalization for all text that is sent to the embedding model.
    Keeping claims and queries on the same normalization path avoids drift.
    """
    return rich_to_plain((text or "").strip())


def _token_count(text: str, tokenizer) -> int:
    if not text:
        return 0
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Token indices sequence length is longer than the specified maximum sequence length.*",
        )
        return tokenizer(text, return_tensors="pt", truncation=False)["input_ids"].shape[1]


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts: list[str] = []
    for block in re.split(r"\n+", text):
        block = block.strip()
        if not block:
            continue
        splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", block)
        for s in splits:
            s = s.strip()
            if s:
                parts.append(s)
    return parts


def _split_oversize_text(text: str, tokenizer, max_length: int, overlap_tokens: int) -> list[str]:
    sentences = _split_sentences(text) or [text]
    parts: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sent in sentences:
        sent_tokens = _token_count(sent, tokenizer)
        if sent_tokens > max_length:
            if current:
                parts.append(" ".join(current).strip())
                current = []
                current_tokens = 0
            words = re.findall(r"\S+", sent)
            if not words:
                continue
            start = 0
            step = max(1, max_length - max(0, overlap_tokens))
            while start < len(words):
                end = min(len(words), start + max_length)
                parts.append(" ".join(words[start:end]).strip())
                start = start + step
            continue

        if current_tokens + sent_tokens <= max_length or not current:
            current.append(sent)
            current_tokens += sent_tokens
            continue

        parts.append(" ".join(current).strip())
        if overlap_tokens > 0:
            overlap: list[str] = []
            overlap_count = 0
            for s in reversed(current):
                overlap_count += _token_count(s, tokenizer)
                overlap.insert(0, s)
                if overlap_count >= overlap_tokens:
                    break
            current = overlap
            current_tokens = overlap_count
        else:
            current = []
            current_tokens = 0

        if current_tokens + sent_tokens <= max_length or not current:
            current.append(sent)
            current_tokens += sent_tokens
        else:
            current = [sent]
            current_tokens = sent_tokens

    if current:
        parts.append(" ".join(current).strip())
    return parts


def _expand_chunks_for_token_limit(chunks, tokenizer, max_length: int, overlap_tokens: int):
    expanded = []
    for ch in chunks:
        text = normalize_text_for_embedding(ch.get("text") or ch.get("chunk"))
        if not text:
            expanded.append(ch)
            continue
        token_count = _token_count(text, tokenizer)
        if token_count <= max_length:
            expanded.append(ch)
            continue
        parts = _split_oversize_text(text, tokenizer, max_length, overlap_tokens)
        part_count = len(parts)
        for idx, part in enumerate(parts, start=1):
            new_chunk = dict(ch)
            new_chunk["chunk"] = part
            new_chunk["text"] = part
            new_chunk["part_index"] = idx
            new_chunk["part_count"] = part_count
            expanded.append(new_chunk)
    return expanded


def _move_tokens_to_device(tokens: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    non_blocking = DEVICE.type == "cuda"
    return {k: v.to(DEVICE, non_blocking=non_blocking) for k, v in tokens.items()}


def _resolve_tokenizer_length(max_length: int, tokenizer_obj) -> tuple[int, int | None]:
    resolved = max(1, int(max_length))
    pad_multiple = TOKENIZER_PAD_MULTIPLE
    if not pad_multiple or resolved % pad_multiple == 0:
        return resolved, pad_multiple

    rounded_up = resolved + (pad_multiple - (resolved % pad_multiple))
    tokenizer_max = getattr(tokenizer_obj, "model_max_length", None)
    if isinstance(tokenizer_max, int) and tokenizer_max > 0 and rounded_up > tokenizer_max:
        return resolved, None

    return rounded_up, pad_multiple


def _tokenize_texts(
    texts: list[str],
    max_length: int,
    *,
    pad_to_multiple_of: int | None = None,
) -> dict[str, torch.Tensor]:
    kwargs = dict(
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=max_length,
    )
    if pad_to_multiple_of:
        kwargs["pad_to_multiple_of"] = pad_to_multiple_of
    return tokenizer(texts, **kwargs)


def embed_chunks(chunks, tokenizer, model, max_length=350):
    print("Starting embedding process...")
    print(f"[embed-config] {_projection_summary()}")
# Our list of embeddings, and runs ColBERT in evaluation mode. Model normally runs in train()   #
# mode, which will drop embeddings and normalize to prevent overfitting.                        #
    embeddings = []
    model.eval()

    model_max = getattr(tokenizer, "model_max_length", None)
    effective_max = max_length
    if model_max and isinstance(model_max, int):
        effective_max = min(max_length, model_max)
    requested_max = effective_max
    effective_max, pad_multiple = _resolve_tokenizer_length(effective_max, tokenizer)
    if effective_max != requested_max:
        print(
            f"[embed-config] adjusted max_length from {requested_max} to {effective_max} "
            f"to satisfy CUDA tokenizer padding"
        )

    chunks = _expand_chunks_for_token_limit(
        chunks,
        tokenizer,
        effective_max,
        overlap_tokens=REBALANCE_OVERLAP_TOKENS,
    )

# Loop through the chunks based on label, clean text up further, and then tokenize.             #
    progress_every = int(os.environ.get("EMBED_PROGRESS_EVERY", "50"))
    valid_chunks: list[dict] = []
    valid_texts: list[str] = []
    for idx, chunk in enumerate(chunks):
        text = normalize_text_for_embedding(chunk.get("text") or chunk.get("chunk"))
        if not text:
            print(f"Empty chunk at index {idx}")
            continue
        valid_chunks.append(chunk)
        valid_texts.append(text)

    total = len(valid_chunks)
    for start in range(0, total, EMBED_BATCH_SIZE):
        batch_chunks = valid_chunks[start:start + EMBED_BATCH_SIZE]
        batch_texts = valid_texts[start:start + EMBED_BATCH_SIZE]
        batch_end = start + len(batch_chunks)
        if progress_every > 0 and (start == 0 or batch_end % progress_every == 0 or batch_end == total):
            print(f"Embedding chunk {batch_end} of {total}")

        cpu_tokens = _tokenize_texts(
            batch_texts,
            effective_max,
            pad_to_multiple_of=pad_multiple,
        )
        attention_lengths = cpu_tokens["attention_mask"].sum(dim=1).tolist()

        for row, text in enumerate(batch_texts):
            if attention_lengths[row] == effective_max:
                token_count = _token_count(text, tokenizer)
                if token_count > effective_max:
                    print(
                        f"WARNING chunk {batch_chunks[row].get('section')} truncated from "
                        f"{token_count} tokens to {effective_max}."
                    )

        tokens = _move_tokens_to_device(cpu_tokens)

        with torch.inference_mode():
            with _model_exec_context():
                outputs = model(**tokens)
            token_embeddings = outputs.last_hidden_state
            if token_embeddings.shape[-1] != 768:
                raise ValueError(
                    f"Expected 768-d token embeddings, got {token_embeddings.shape[-1]}"
                )

        attention_mask = tokens["attention_mask"].bool()
        for row, chunk in enumerate(batch_chunks):
            masked_embeddings = token_embeddings[row][attention_mask[row]]
            if masked_embeddings.numel() == 0:
                raise ValueError("No non-padding tokens available after attention_mask filtering.")
            projected_tokens = _project_tokens_128(masked_embeddings)
            if projected_tokens.shape[-1] != 128:
                raise ValueError(
                    f"Projected token embeddings must be 128-d. Got {projected_tokens.shape[-1]}."
                )
            chunk_vector = (
                projected_tokens.mean(dim=0)
                .detach()
                .cpu()
                .numpy()
                .tolist()
            )
            colbert_variants = _build_token_variants(projected_tokens)
            colbert_vectors = colbert_variants.get(PRIMARY_COLBERT_VARIANT)
            if colbert_vectors is None:
                raise ValueError(
                    f"Configured primary ColBERT variant '{PRIMARY_COLBERT_VARIANT}' is unavailable. "
                    f"Available={sorted(colbert_variants.keys())}"
                )
            if np.asarray(colbert_vectors).shape[-1] != 128:
                raise ValueError("Configured ColBERT vectors are not 128-d.")

            chunk["embedding"] = chunk_vector
            chunk["colbert"] = colbert_vectors
            chunk["colbert_variants"] = colbert_variants
            embeddings.append(chunk)

    return embeddings

def embed_query(query, tokenizer, model, max_length=256):
    model.eval()
    query_text = normalize_text_for_embedding(query)

    effective_max, pad_multiple = _resolve_tokenizer_length(max_length, tokenizer)
    kwargs = dict(
        return_tensors="pt", 
        truncation=True, 
        padding="max_length", 
        max_length=effective_max,
    )
    if pad_multiple:
        kwargs["pad_to_multiple_of"] = pad_multiple

    tokens = tokenizer(query_text, **kwargs)
    tokens = _move_tokens_to_device(tokens)
    
    with torch.inference_mode():
        with _model_exec_context():
            outputs = model(**tokens)

    token_embeddings = outputs.last_hidden_state.squeeze(0)
    if token_embeddings.shape[-1] != 768:
        raise ValueError(f"Expected query token embeddings [T,768], got {tuple(token_embeddings.shape)}.")
    attn_mask = tokens["attention_mask"].squeeze(0).bool()
    masked_embeddings = token_embeddings[attn_mask]
    if masked_embeddings.numel() == 0:
        raise ValueError("No non-padding query tokens after attention_mask filtering.")
    projected_tokens = _project_tokens_128(masked_embeddings)
    if projected_tokens.shape[-1] != 128:
        raise ValueError("Query projection failed to produce 128-d tokens.")
    query_vector = projected_tokens.mean(dim=0, keepdim=True)
    query_vector = query_vector.detach().cpu().numpy().astype("float32")  # keep 2D
    return query_vector


def embed_query_tokens_for_shard(query: str, shard: str, max_length: int = 256):
    """
    Token-level query embeddings for a specific shard.
    Strictly uses trained 128-D projection.
    """
    shard = assert_128_variant(shard, context="embed_query_tokens_for_shard")
    query_text = normalize_text_for_embedding(query)
    effective_max, pad_multiple = _resolve_tokenizer_length(max_length, tokenizer)
    kwargs = dict(
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=effective_max,
    )
    if pad_multiple:
        kwargs["pad_to_multiple_of"] = pad_multiple
    tokens = tokenizer(query_text, **kwargs)
    tokens = _move_tokens_to_device(tokens)
    model.eval()
    with torch.inference_mode():
        with _model_exec_context():
            outputs = model(**tokens)
    token_embeddings = outputs.last_hidden_state.squeeze(0)
    if token_embeddings.shape[-1] != 768:
        raise ValueError(f"Expected query token embeddings [T,768], got {tuple(token_embeddings.shape)}.")
    attn_mask = tokens["attention_mask"].squeeze(0).bool()
    masked = token_embeddings[attn_mask]
    if masked.numel() == 0:
        raise ValueError("No non-padding query tokens after attention_mask filtering.")
    projected = _project_tokens_128(masked)
    variants = _build_token_variants(projected)
    if shard not in variants:
        raise ValueError(
            f"Requested shard '{shard}' unavailable. Enabled variants: {sorted(variants.keys())}"
        )
    if np.asarray(variants[shard]).shape[-1] != 128:
        raise ValueError(f"Variant '{shard}' produced non-128 vectors.")
    return variants[shard]


def _open_output(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "wt", encoding="utf-8")
    return path.open("w", encoding="utf-8")


def _open_input(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def save_embeddings_to_file(chunks, out_path: str | Path) -> Path:
    """
    Persist embedded chunks to disk as newline-delimited JSON.
    If the filename ends with .gz the output is gzip-compressed.
    """
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_output(path) as handle:
        for ch in chunks:
            handle.write(json.dumps(ch, ensure_ascii=False))
            handle.write("\n")
    print(f"[embed] Saved {len(chunks)} chunk embeddings to {path}")
    return path


def load_embeddings_from_file(path: str | Path):
    """
    Generator that yields embedded chunk dicts from a file created by
    save_embeddings_to_file.
    """
    path = Path(path)
    with _open_input(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def load_embeddings_into_weaviate(path: str | Path, batch_size: int = 128):
    """
    Stream embeddings from a saved file and insert them into Weaviate.
    Intended to run on a machine that can reach the Weaviate instance.
    """
    from backend.app.store import store_embeddings

    buffer = []
    total = 0
    for record in load_embeddings_from_file(path):
        buffer.append(record)
        if len(buffer) >= batch_size:
            store_embeddings(buffer)
            total += len(buffer)
            buffer.clear()
    if buffer:
        store_embeddings(buffer)
        total += len(buffer)
    print(f"[embed] Loaded {total} embeddings from {path} into Weaviate")


# Validate strict projection config at module import time.
_load_trained_projection_matrix()
print(f"[embed-init] {_projection_summary()}")
