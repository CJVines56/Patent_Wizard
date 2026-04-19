import os
import uuid
import pandas as pd

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# ----------------- CONFIG -----------------
MD_DIR = "patents/markdown"          # folder containing .md files
METADATA_CSV = "patents/sample_manifest.csv"
CHROMA_DIR = "chroma_db"          # where Chroma will persist
COLLECTION_NAME = "patent_docs"


# Confirm if embedding exist or not
add_texts = not os.path.exists(CHROMA_DIR)


def load_metadata(csv_path: str) -> dict:
    """
    Load metadata CSV and return mapping: doc_id (str) -> metadata dict
    Only keep the first 6 columns as metadata:
      - index
      - doc_id
      - title
      - filing_date
      - classification
      - authors
    """
    df = pd.read_csv(csv_path, dtype={"doc_id": str})

    metadata_map = {}
    for _, row in df.iterrows():
        doc_id = row["doc_id"]

        # Select only the first 6 columns
        meta = {
            "index": row["index"],
            "doc_id": row["doc_id"],
            "title": row["title"],
            "filing_date": row["filing_date"],
            "classification": row["classification"],
            "authors": row["authors"],
        }

        metadata_map[doc_id] = meta

    return metadata_map


def load_markdown_files(md_dir: str) -> dict:
    """
    Load all .md files from md_dir.
    Assumes filenames are `<doc_id>.md` and returns:
      {doc_id (str): text}
    """
    md_map = {}
    for fname in os.listdir(md_dir):
        if fname.lower().endswith(".md"):
            file_name = os.path.splitext(fname)[0]  # e.g. "sample_01_123_meat" from "sample_01_123_meat.md"
            doc_id = file_name.split("_")[2]   # e.g. "12402636" from "12402636.md"
            path = os.path.join(md_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                md_map[doc_id] = f.read()
    return md_map

#def main():

if add_texts:
    # 1. Load metadata and markdown
    metadata_map = load_metadata(METADATA_CSV)
    md_map = load_markdown_files(MD_DIR)

    # 2. Text splitter for chunking documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    texts = []
    metadatas = []
    ids = []

    # 3. Iterate over markdown docs, match with metadata by doc_id
    for doc_id, content in md_map.items():
        file_metadata = metadata_map.get(doc_id)

        if file_metadata is None:
            # Skip documents that don't have a corresponding metadata row
            print(f"Warning: No metadata found for doc_id={doc_id}, skipping.")
            continue

        # You can optionally add the filename/source field if useful
        file_metadata = {
            **file_metadata
            }

        # Split into chunks
        chunks = splitter.split_text(content)

        for idx, chunk in enumerate(chunks):
            texts.append(chunk)
            chunk_metadata = {
                **file_metadata,
                "chunk_index": idx,
            }
            metadatas.append(chunk_metadata)
            ids.append(str(uuid.uuid4()))

# 4. Create / populate Chroma store via LangChain
model_name = "BAAI/bge-small-en"
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}
hf = HuggingFaceEmbeddings(
    model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)
vector_storage = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DIR,
    embedding_function=hf,
)

if add_texts:
    # 5. Add documents
    vector_storage.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
        batch_size=64
    )

# retriever = vector_storage.as_retriever(
#     search_kwargs={"k": 5}
# )
    # 6. Persist to disk
    # vector_store.persist()
    # print(
    #     f"Inserted {len(texts)} chunks into collection "
    #     f"'{COLLECTION_NAME}' at '{CHROMA_DIR}'."
    # )


#if __name__ == "__main__":
#    main()