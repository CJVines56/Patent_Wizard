# Chunking function
# Text will be whatever extracted input text
# Chunk size is the number of words per chunk, default size of 50
def chunk_text(text, chunk_size=50):
    words = text.split()                                    # Break the text up by whitespace
    chunks = []                                             # Initialize a list of the chunks
    for i in range(0, len(words), chunk_size):              # Loop through the words
        chunks.append(" ".join(words[i:i+chunk_size]))      # Cut the words into chunk size pieces, then add them to the chunks list
    return chunks

# Check for a possible pre programmed or build in chunker