import json
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

def load_metadata():
    metadata_path = os.path.join("data", "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def ingest_documents():
    print("Loading documents from data directory...")
    loader = PyPDFDirectoryLoader("data")
    docs = loader.load()

    metadata = load_metadata()

    # Attach metadata to documents
    for doc in docs:
        filename = os.path.basename(doc.metadata.get("source", ""))
        if filename in metadata:
            doc.metadata.update(metadata[filename])
            
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    print("Generating embeddings and storing in Chroma...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory="./chroma_db")
    
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_documents()
