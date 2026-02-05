# Recall: A vector represents text through numbers. A vector's "meaning" is its direction.      #
# Different direction, different meaning, similar direction, similar meaning, etc. Vectors      #
# themselves contain no labels, literally only text meaning.
# We will use a vector database (with FAISS?) and an sql database together.

from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from backend.app.services.download import rich_to_plain
from pathlib import Path
import json
import gzip
import os
import re
import warnings

warnings.filterwarnings(
    "ignore",
    message="Token indices sequence length is longer than the specified maximum sequence length.*",
)

DEFAULT_MODEL_NAME = "colbert-ir/colbertv2.0"
MODEL_NAME = (
    os.environ.get("COLBERT_MODEL_PATH")
    or os.environ.get("COLBERT_MODEL_NAME")
    or os.environ.get("MODEL_NAME")
    or DEFAULT_MODEL_NAME
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Remember to alter model path anytime you download a new snapshot!
# MODEL_PATH = r"C:/Users/Christian Casteel/.cache/huggingface/hub/models--colbert-ir--colbertv2.0/snapshots/c1e84128e85ef755c096a95bdb06b47793b13acf"

LOCAL_ONLY = bool(
    os.environ.get("TRANSFORMERS_OFFLINE") == "1"
    or os.environ.get("HF_HUB_OFFLINE") == "1"
    or os.environ.get("LOCAL_MODEL_ONLY") == "1"
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

TOKEN_VECTOR_DIM = int(os.environ.get("TOKEN_VECTOR_DIM", "768"))
TOKEN_VECTOR_DTYPE = os.environ.get("TOKEN_VECTOR_DTYPE", "float16").lower()
USE_TOKEN_PROJECTION = bool(
    os.environ.get("USE_TOKEN_PROJECTION", "1") in {"1", "true", "True", "yes", "YES"}
)
COLBERT_VARIANTS = os.environ.get(
    "COLBERT_VARIANTS",
    "768_f32,768_f16,128_f32,128_f16",
).lower()

if TOKEN_VECTOR_DIM not in {768, 128}:
    raise ValueError("TOKEN_VECTOR_DIM must be 768 or 128")
if TOKEN_VECTOR_DTYPE not in {"float16", "float32"}:
    raise ValueError("TOKEN_VECTOR_DTYPE must be 'float16' or 'float32'")
if TOKEN_VECTOR_DIM == 128 and not USE_TOKEN_PROJECTION:
    raise ValueError("TOKEN_VECTOR_DIM=128 requires USE_TOKEN_PROJECTION=True")

_TOKEN_PROJECTION = None  # Experimental stand-in for a ColBERT head; replace later.


def _get_token_projection():
    global _TOKEN_PROJECTION
    if not (_variant_enabled("128_f32") or _variant_enabled("128_f16") or TOKEN_VECTOR_DIM == 128):
        return None
    if _TOKEN_PROJECTION is None:
        proj = torch.nn.Linear(768, 128, bias=False)
        proj.to(DEVICE)
        proj.eval()
        _TOKEN_PROJECTION = proj
    return _TOKEN_PROJECTION


def _variant_enabled(name: str) -> bool:
    if COLBERT_VARIANTS in {"all", "*"}:
        return True
    enabled = {v.strip() for v in COLBERT_VARIANTS.split(",") if v.strip()}
    return name in enabled


def _build_token_variants(token_vectors: torch.Tensor) -> dict[str, object]:
    variants: dict[str, object] = {}
    if _variant_enabled("768_f32"):
        variants["768_f32"] = token_vectors.to(torch.float32).detach().cpu().numpy()
    if _variant_enabled("768_f16"):
        variants["768_f16"] = token_vectors.to(torch.float16).detach().cpu().numpy()
    if _variant_enabled("768_i8"):
        max_abs = token_vectors.abs().max(dim=1, keepdim=True).values
        scale = max_abs / 127.0
        scale = torch.where(scale == 0, torch.ones_like(scale), scale)
        q = torch.clamp((token_vectors / scale).round(), -127, 127).to(torch.int8)
        variants["768_i8"] = {
            "data": q.detach().cpu().numpy(),
            "scale": scale.detach().cpu().numpy().astype("float32"),
        }
    if _variant_enabled("128_f32") or _variant_enabled("128_f16"):
        proj = _get_token_projection()
        if proj is None:
            raise RuntimeError("Token projection layer not initialized")
        projected = proj(token_vectors)
        projected = F.normalize(projected, p=2, dim=1)
        if _variant_enabled("128_f32"):
            variants["128_f32"] = projected.to(torch.float32).detach().cpu().numpy()
        if _variant_enabled("128_f16"):
            variants["128_f16"] = projected.to(torch.float16).detach().cpu().numpy()
    return variants


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
        text = rich_to_plain((ch.get("text") or ch.get("chunk") or "").strip())
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
def embed_chunks(chunks, tokenizer, model, max_length=350):
    print("Starting embedding process...")
# Our list of embeddings, and runs ColBERT in evaluation mode. Model normally runs in train()   #
# mode, which will drop embeddings and normalize to prevent overfitting.                        #
    embeddings = []
    model.eval()

    model_max = getattr(tokenizer, "model_max_length", None)
    effective_max = max_length
    if model_max and isinstance(model_max, int):
        effective_max = min(max_length, model_max)

    chunks = _expand_chunks_for_token_limit(
        chunks,
        tokenizer,
        effective_max,
        overlap_tokens=REBALANCE_OVERLAP_TOKENS,
    )

# Loop through the chunks based on label, clean text up further, and then tokenize.             #
    progress_every = int(os.environ.get("EMBED_PROGRESS_EVERY", "50"))
    for idx, chunk in enumerate(chunks):
        if progress_every > 0 and (idx == 0 or (idx + 1) % progress_every == 0):
            print(f"Embedding chunk {idx + 1} of {len(chunks)})")
        text = rich_to_plain((chunk.get("text") or chunk.get("chunk") or "").strip())

        if not text:
            print(f"Empty chunk at index {idx}")
            continue

# Call the tokenizer function.                                                                  #
        tokens = tokenizer(
            text,                        # chunk text
            return_tensors="pt",        # change format from lists to pt tensors so ColBERT can read
            truncation=True,            # truncate chunks that go over the token limits
            padding="max_length",       # add zero tokens to make sure tensors are equal size. Helps the model embed faster
            max_length=effective_max     # the token limit
        )
        tokens = {k: v.to(DEVICE) for k, v in tokens.items()}

# Warning message if a chunk was truncated, this means I need to make chunks shorter.           #
        if tokens["input_ids"].shape[1] == effective_max:
            token_count = _token_count(text, tokenizer)
            if token_count > effective_max:
                print(
                    f"WARNING chunk {chunk.get('section')} truncated from "
                    f"{token_count} tokens to {effective_max}."
                )

# Embed the tokenized text by running it through ColBERT. Tell Pytorch not to track gradients.  #
# stops the collection of tracking data to save a lot of computing time.                        #
# At this point, we now have a set of embeddings for a chunk.                                   #
        with torch.no_grad():
            outputs = model(**tokens)
            token_embeddings = outputs.last_hidden_state.squeeze(0)
            if token_embeddings.shape[-1] != 768:
                raise ValueError(
                    f"Expected 768-d token embeddings, got {token_embeddings.shape[-1]}"
                )
            attn_mask = tokens["attention_mask"].squeeze(0).bool()
            masked_embeddings = token_embeddings[attn_mask]
            if masked_embeddings.numel() == 0:
                masked_embeddings = token_embeddings[attn_mask.sum().item():]
            chunk_vector = (
                masked_embeddings.mean(dim=0)
                .detach()
                .cpu()
                .numpy()
                .tolist()
            )
            token_vectors = masked_embeddings
            colbert_variants = _build_token_variants(token_vectors)
            if TOKEN_VECTOR_DIM == 768:
                colbert_vectors = colbert_variants.get(
                    "768_f16" if TOKEN_VECTOR_DTYPE == "float16" else "768_f32"
                )
            else:
                colbert_vectors = colbert_variants.get(
                    "128_f16" if TOKEN_VECTOR_DTYPE == "float16" else "128_f32"
                )
            if colbert_vectors is None:
                raise RuntimeError("Configured ColBERT variant not available")

        chunk["embedding"] = chunk_vector
        chunk["colbert"] = colbert_vectors
        chunk["colbert_variants"] = colbert_variants
        embeddings.append(chunk)

    return embeddings

def embed_query(query, tokenizer, model, max_length=256):
    model.eval()
 
    tokens = tokenizer(
        query, 
        return_tensors="pt", 
        truncation=True, 
        padding="max_length", 
        max_length=max_length
        )
    tokens = {k: v.to(DEVICE) for k, v in tokens.items()}
    
    with torch.no_grad():
        outputs = model(**tokens)

    token_embeddings = outputs.last_hidden_state.squeeze(0)
    attn_mask = tokens["attention_mask"].squeeze(0).bool()
    masked_embeddings = token_embeddings[attn_mask]
    if masked_embeddings.numel() == 0:
        masked_embeddings = token_embeddings[:1]
    query_vector = masked_embeddings.mean(dim=0, keepdim=True)
    query_vector = query_vector.detach().cpu().numpy().astype("float32")  # keep 2D
    return query_vector


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
