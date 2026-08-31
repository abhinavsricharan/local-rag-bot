import sys
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

def evaluate_retrieval(query: str):
    print(f"--- Evaluation for Query: '{query}' ---")
    
    print("1. Loading embedding model (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    print("2. Connecting to local vector store (Chroma)...")
    vectorstore = Chroma(persist_directory="data/chroma_db", embedding_function=embeddings)
    
    print("3. Embedding user query and calculating distance to document chunks...\n")
    # similarity_search_with_score returns documents and distance scores
    # Chroma defaults to squared L2 distance. Lower score means higher similarity.
    results = vectorstore.similarity_search_with_score(query, k=3)
    
    for i, (doc, score) in enumerate(results):
        print(f"--- Chunk {i+1} | Distance Score: {score:.4f} ---")
        print(f"Source: {doc.metadata.get('source', 'Unknown')} (Page {doc.metadata.get('page', 0)})")
        print(f"Content snippet (showing overlap context):")
        print(f"{doc.page_content}\n")

if __name__ == "__main__":
    test_query = "What happens if there is a security breach?"
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
    evaluate_retrieval(test_query)
