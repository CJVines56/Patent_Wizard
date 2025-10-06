'''
Getting Set Up:
Remember to Ctrl+Shift+P, Poetrynvs, pick the Python 3.12 one and select Python.exe
Gitbash for terminal, navigate to main folder c/ECEN_403/Patent_Wizard
Remember to Push and Pull!!! Stay updated!!!

Notes:
Late interaction is key. Want to cater to ColBERT's strengths to beat out LangChain
'''
from chunking import chunk_text
from embed import embed_chunks

def run_pipeline(query):
    # Extract text
    

    # Chunk text
    chunks = chunk_text(query, chunk_size=10)   # Define chunk size here!
    print("Chunks:")
    for i, c in enumerate(chunks):
        print(f"  {i+1}: {c}")

    # Embed
    embeddings = embed_chunks(chunks)
    # Present vector shapes, first value is the number of tokens, second is the number of vectors
    print("\nEmbedded Vector Shapes:")
    for i, matrix in enumerate(embeddings):
        print(f"  Chunk {i+1}: {matrix.shape}")

if __name__ == "__main__":
    query = "This is a test query that will be chunked and then embedded using ColBERT. How many engineering students are there at Texas A&M University?"
    
    run_pipeline(query)