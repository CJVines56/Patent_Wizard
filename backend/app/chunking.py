'''
# Text will be whatever extracted input text
# Chunk size is the number of words per chunk, default size of 50
def chunk_text(text, chunk_size=50):
    words = text.split()                                    # Break the text up by whitespace
    chunks = []                                             # Initialize a list of the chunks
    for i in range(0, len(words), chunk_size):              # Loop through the words
        chunks.append(" ".join(words[i:i+chunk_size]))      # Cut the words into chunk size pieces, then add them to the chunks list
    return chunks
'''

# Use statistical chunking or section by section chunking?

# I say section by section unless there are grievous errors.
# No need to add extra computing time for something like this.
#def chunk_text(text):

# Possible issues: Irrelevant text, Large descriptions, Claims referencing each other?

# 10/15/2025 create new chunking function, this time without word count chunking, but instead
# chunking by section: abstract, description paragraphs, and per claim

import os
print(os.path.getsize("patent_index.faiss"))

import faiss
index = faiss.read_index("patent_index.faiss")
print(f"Index loaded successfully. Contains {index.ntotal} vectors.")

import numpy as np
