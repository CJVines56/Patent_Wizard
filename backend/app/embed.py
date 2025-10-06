# embed.py


import torch                                        # Deep learning framework
from transformers import AutoTokenizer, AutoModel   # Autotokenizer takes strings and turns them into token IDs
                                                    # Automodel loads the ColBERT model  

MODEL_NAME = "colbert-ir/colbertv2.0"               # ColBERT model from Huggingface

print("Loading ColBERT model from HuggingFace...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)       # Turns text into tokens (downloads tokenizer)
model = AutoModel.from_pretrained(MODEL_NAME)               # Turns tokens into embeddings (ColBERT outputs multivector embeddings)

print("ColBERT model loaded!")

def embed_chunks(chunks, device="cuda" if torch.cuda.is_available() else "cpu"):    # Move model to GPU, otherwise use CPU
    model.to(device)
    embeddings = []         # Initialize list of embeddings

    # Loop through each chunk
    for chunk in chunks:
        # chunk is an individual chunk out of all chunks
        # "pt" is the format of the tokenized output
        # Truncation and max length prevent tokens from exceeeding the ColBERT token limit
        # .to(device) keeps the model and data on the same device, whether GPU or CPU
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=180).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            token_embeddings = outputs.last_hidden_state.squeeze(0).cpu()   # Controls GPU and CPU usage, swap to CPU for storage and printing
        embeddings.append(token_embeddings)                                 # Makes a list of the embedding "dimensions"
                                                                            # First number is number of tokens in the chunk
                                                                            # Second number is the size of the vector
    return embeddings
