# Recall: A vector represents text through numbers. A vector's "meaning" is its direction.      #
# Different direction, different meaning, similar direction, similar meaning, etc. Vectors      #
# themselves contain no labels, literally only text meaning.
# We will use a vector database (with FAISS?) and an sql database together.

from transformers import AutoTokenizer, AutoModel
import torch
from services.download import rich_to_plain
from pathlib import Path
import json
import gzip
import os
import re

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


def _token_count(text: str, tokenizer) -> int:
    if not text:
        return 0
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
        text = rich_to_plain((ch.get("chunk") or "").strip())
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

    chunks = _expand_chunks_for_token_limit(
        chunks,
        tokenizer,
        max_length,
        overlap_tokens=REBALANCE_OVERLAP_TOKENS,
    )

# Loop through the chunks based on label, clean text up further, and then tokenize.             #
    for idx, chunk in enumerate(chunks):
        print(f'Embedding chunk {idx + 1} of {len(chunks)})')
        text = rich_to_plain((chunk.get("chunk") or "").strip())

        if not text:
            print(f"Empty chunk at index {idx}")
            continue

# Call the tokenizer function.                                                                  #
        tokens = tokenizer(
            text,                        # chunk text
            return_tensors="pt",        # change format from lists to pt tensors so ColBERT can read
            truncation=True,            # truncate chunks that go over the token limits
            padding="max_length",       # add zero tokens to make sure tensors are equal size. Helps the model embed faster
            max_length=max_length     # the token limit
        )
        tokens = {k: v.to(DEVICE) for k, v in tokens.items()}

# Warning message if a chunk was truncated, this means I need to make chunks shorter.           #
        if tokens["input_ids"].shape[1] == max_length:
            token_count = tokenizer(text, return_tensors="pt", truncation=False)["input_ids"].shape[1]
            if token_count > max_length:
                print(f"WARNING chunk", chunk.get("section"), " truncated from {token_count} tokens to {max_length}.")

# Embed the tokenized text by running it through ColBERT. Tell Pytorch not to track gradients.  #
# stops the collection of tracking data to save a lot of computing time.                        #
# At this point, we now have a set of embeddings for a chunk.                                   #
        with torch.no_grad():
            outputs = model(**tokens)
            token_embeddings = outputs.last_hidden_state.squeeze(0)
            attn_mask = tokens["attention_mask"].squeeze(0).bool()
            masked_embeddings = token_embeddings[attn_mask]
            if masked_embeddings.numel() == 0:
                masked_embeddings = token_embeddings[:1]
            chunk_vector = (
                masked_embeddings.mean(dim=0)
                .detach()
                .cpu()
                .numpy()
                .tolist()
            )
            colbert_vectors = (
                masked_embeddings.detach().cpu().numpy().astype("float32").tolist()
            )

        chunk["embedding"] = chunk_vector
        chunk["colbert"] = colbert_vectors
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
