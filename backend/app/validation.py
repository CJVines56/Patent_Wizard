from chunking import chunk_text     # Call chunking function
from embed import embed_chunks      # Call embed function
import torch                        # Deep learning framework
import torch.nn.functional as F

# 5 population factoids, all relatively similar
docs = [
    "The population of Texas is 31.29 million.",
    "College Station, Texas has a population of 128,023 people.",
    "Texas A&M University has 24757 engineering students.",
    "There are 821 engineering faculty members at Texas A&M University.",
    "At Texas Tech University, there are 6087 engineering students."
]

# Query
query = "How many engineering students are there at Texas A&M University?"

def average_pool(emb):
    """Convert (seq_len, hidden_dim) → (hidden_dim,) by averaging over tokens."""
    return emb.mean(dim=0)

def run_validation():
    # Embed documents
    doc_embeddings = []
    for doc in docs:
        chunks = chunk_text(doc, chunk_size=50)  # big enough so each factoid = 1 chunk
        emb = embed_chunks(chunks)[0]            # (seq_len, 768)
        pooled = average_pool(emb)               # (768,)
        doc_embeddings.append(pooled)

    # Embed query
    query_emb = average_pool(embed_chunks(chunk_text(query))[0])

    # Compute cosine similarities via a dot product
    sims = [F.cosine_similarity(query_emb, d, dim=0).item() for d in doc_embeddings]

    # Print results
    for i, (doc, score) in enumerate(zip(docs, sims)):
        print(f"String {i+1}: {doc} (score={score:.3f})")

    best = sims.index(max(sims))
    print(f"\nBest match: String {best+1}")

if __name__ == "__main__":
    run_validation()