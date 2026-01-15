'''
Getting Set Up:
Remember to Ctrl+Shift+P, Poetrynvs, pick the Python 3.12 one and select Python.exe
Gitbash for terminal, navigate to main folder c/ECEN_403/Patent_Wizard
Remember to Push and Pull!!! Stay updated!!!
'''

# 10/28/2025 New main to run whole pipeline with weaviate. CURRENTLY USES WEAVIATE CLUSTER
from extract import extract_text
from embed import embed_chunks, tokenizer, model
from store import store_embeddings
import time


def run_pipeline():
    # === 1. Extract XML text ===
    print("Extracting text...")
    chunks = extract_text("C:/ECEN_403/Bulk_Dataset_Test/agricultural_implement_with_visual_sensors.xml")
    print(f"Extracted {len(chunks)} chunks")

    # === 2. Embed text ===
    print("Embedding text...")
    start = time.time()
    embeddings = embed_chunks(chunks, tokenizer, model)
    end = time.time()
    print(f"Embedded {len(embeddings)} chunks in {end - start:.2f} seconds")

    # === 3. Prepare chunk text for storage ===
    chunk_texts = [text for (_, text) in chunks]

    # === 4. Store in Weaviate ===
    print("Uploading embeddings to cluster...")
    metadata = {
        "doc_id": "20250301933",
        "priority_date": "Not Applicable",
        "cpc_code": "B 25 G 1/01",  # example code; optional
    }

    store_embeddings(embeddings, chunk_texts, metadata)

    print("Embeddings stored successfully.")


if __name__ == "__main__":
    run_pipeline()

'''
from extract import extract_text
#from chunking import chunk_text
from embed import embed_chunks
from embed import tokenizer, model
from store import store_embeddings
from embed import embed_query
import time

def run_pipeline():
    # Extract text
    print("Extracting text...")
    text = extract_text("C:/ECEN_403/Bulk_Dataset_Test/Sample_Patent_XML.xml")
    print("Successfully extracted text!")
    
    # Embed text
    start = time.time()
    print("Embedding text...")
    embeddings = embed_chunks(text,tokenizer,model)
    end = time.time()
    time_taken = end - start
    print(f"Took {time_taken:.3f} seconds to embed!")

    # Present vector shapes, first value is the number of tokens, second is the number of vectors
    #print("\nEmbedded Vector Shapes:")
    #for i, matrix in enumerate(embeddings):
    #    print(f"  Chunk {i+1}: {matrix.shape}")
    print("Storing embeddings in weaviate...")
    store_embeddings(embeddings)

run_pipeline()
'''

#####################################################################################################################

# Outdated script for testing faiss search function, which we will not be using.
'''
import faiss
query = "spring action shovel"
print("Searching FAISS...")
def search_faiss(query, tokenizer, model, index_path="patent_index.faiss", k=5, device="cpu"):
    """
    Embeds a query and searches the FAISS index for the top-k most similar vectors.
    """
    start = time.time()
    # 1. Embed the query
    query_vec = embed_query(query, tokenizer, model)

    # 2. Load the FAISS index
    index = faiss.read_index(index_path)
    print(f"Loaded index with {index.ntotal} vectors")

    # 3. Perform the search
    D, I = index.search(query_vec, k)

    end = time.time()
    time_taken = end - start
    print(f"Took {time_taken:.3f} seconds to search!")
    # 4. Show results
    print(f"Query: {query}")
    print("Top matches:")
    for rank, (idx, score) in enumerate(zip(I[0], D[0]), start=1):
        print(f"  {rank}. Vector ID {idx} — similarity {score:.4f}")

    return I, D

default = "This is a test query that will be chunked and then embedded using ColBERT. How many engineering students are there at Texas A&M University?"
run_pipeline(default)

query = "I think claims with guide screws are pretty neat. Just love guide screws, especially how they move linearly within a shaft."
search_faiss(query, tokenizer, model)
'''