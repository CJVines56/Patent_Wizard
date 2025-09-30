from chunking import chunk_text
from embed import embed_chunks

def run_pipeline(query):
    # Step 1: Chunk the text
    chunks = chunk_text(query, chunk_size=10)
    print("Chunks:")
    for i, c in enumerate(chunks):
        print(f"  {i+1}: {c}")

    # Step 2: Embed chunks
    embeddings = embed_chunks(chunks)
    print("\nEmbedded Vector Shapes:")
    for i, matrix in enumerate(embeddings):
        print(f"  Chunk {i+1}: {matrix.shape}")

if __name__ == "__main__":
    query = "This is a test query that will be chunked and then embedded using ColBERT. How many engineering students are there at Texas A&M University?"
    
    run_pipeline(query)