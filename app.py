"""
Local RAG Bot - Streamlit Dashboard
UPSC IT Wing Document Intelligence System

Azure AI Foundry-style UI with cosine similarity metrics,
retrieval inspection, and local Ollama model integration.
"""

import os
import json
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from generate_sample_pdfs import generate_sample_pdfs

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_DIR = "data"
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "phi3"
FALLBACK_ANSWER = (
    "The provided documents do not contain information to answer this query."
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="UPSC IT Wing - Local RAG Bot",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "index_status" not in st.session_state:
    st.session_state.index_status = "Not indexed"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def load_metadata():
    """Load document metadata from metadata.json."""
    metadata_path = os.path.join(DATA_DIR, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def list_pdf_files():
    """Return a list of PDF filenames in the data directory."""
    if not os.path.exists(DATA_DIR):
        return []
    return [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".pdf")]


def build_vectorstore(pdf_files):
    """Load PDFs, split into chunks, embed, and store in Chroma."""
    if not pdf_files:
        return None

    metadata = load_metadata()
    all_docs = []

    for pdf_file in pdf_files:
        filepath = os.path.join(DATA_DIR, pdf_file)
        loader = PyPDFLoader(filepath)
        docs = loader.load()
        for doc in docs:
            filename = os.path.basename(doc.metadata.get("source", ""))
            if filename in metadata:
                doc.metadata.update(metadata[filename])
        all_docs.extend(docs)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    splits = text_splitter.split_documents(all_docs)

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )
    return vectorstore


def query_rag(vectorstore, question, system_prompt, top_k):
    """Run the RAG pipeline: retrieve, score, synthesize."""
    embeddings = vectorstore._embedding_function

    # Retrieve with cosine similarity scores
    results = vectorstore.similarity_search_with_score(question, k=top_k)

    if not results:
        return FALLBACK_ANSWER, [], ""

    # Build context from retrieved chunks
    context_parts = []
    retrieval_details = []

    for i, (doc, distance) in enumerate(results):
        cosine_similarity = 1.0 - distance
        source = os.path.basename(doc.metadata.get("source", "Unknown"))
        page = doc.metadata.get("page", 0)
        title = doc.metadata.get("title", source)

        context_parts.append(doc.page_content)
        retrieval_details.append(
            {
                "rank": i + 1,
                "source": source,
                "page": page,
                "title": title,
                "content": doc.page_content,
                "cosine_distance": round(distance, 4),
                "cosine_similarity": round(cosine_similarity, 4),
                "similarity_pct": round(cosine_similarity * 100, 2),
            }
        )

    context = "\n\n---\n\n".join(context_parts)

    # Build the prompt
    prompt = (
        f"{system_prompt}\n\n"
        f"Use the following pieces of context to answer the question at the end.\n"
        f"If you don't know the answer based on the context, say: "
        f'"{FALLBACK_ANSWER}"\n\n'
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )

    # Check if any result is relevant enough (similarity > 0.2)
    max_similarity = max(d["cosine_similarity"] for d in retrieval_details)
    if max_similarity < 0.2:
        return FALLBACK_ANSWER, retrieval_details, prompt

    # Synthesize answer with phi3
    try:
        llm = Ollama(model=LLM_MODEL)
        answer = llm.invoke(prompt)
    except Exception as e:
        answer = f"Error connecting to Ollama ({LLM_MODEL}): {str(e)}"

    return answer, retrieval_details, prompt


# ---------------------------------------------------------------------------
# Sidebar - Setup and Grounding Data Panel
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Setup and Grounding Data")

    # System prompt configuration
    st.subheader("System Prompt")
    system_prompt = st.text_area(
        "Configure the system prompt for the LLM:",
        value=(
            "You are an expert assistant for the UPSC IT Wing. "
            "Answer questions strictly based on the provided document context. "
            "Be precise, factual, and cite specific policies or guidelines when possible. "
            "Do not fabricate information."
        ),
        height=120,
        label_visibility="collapsed",
    )

    st.divider()

    # Document upload
    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Attach additional candidate biodata PDFs:",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        os.makedirs(DATA_DIR, exist_ok=True)
        for uploaded_file in uploaded_files:
            save_path = os.path.join(DATA_DIR, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"Saved {len(uploaded_files)} file(s) to data/")

    st.divider()

    # Load sample PDFs
    st.subheader("Sample Documents")
    if st.button("Load Sample PDFs", use_container_width=True):
        generated = generate_sample_pdfs()
        if generated:
            st.success(f"Generated {len(generated)} sample PDF(s)")
        else:
            st.info("All sample PDFs already exist")

    pdf_files = list_pdf_files()
    if pdf_files:
        st.caption(f"Documents in data/: {len(pdf_files)}")
        for pf in pdf_files:
            st.text(f"  - {pf}")
    else:
        st.warning("No PDFs found in data/")

    st.divider()

    # Chunking settings (fixed/locked)
    st.subheader("Chunking Settings (Locked)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Chunk Size", CHUNK_SIZE)
    with col2:
        st.metric("Chunk Overlap", CHUNK_OVERLAP)

    st.divider()

    # Top-k slider
    st.subheader("Retrieval Settings")
    top_k = st.slider("Top-K Matches", min_value=1, max_value=5, value=3)

    st.divider()

    # Index button and status
    st.subheader("Vector Store")
    if st.button("Index Documents", use_container_width=True):
        if not pdf_files:
            st.error("No PDFs to index. Upload or load sample PDFs first.")
        else:
            with st.spinner("Indexing documents..."):
                st.session_state.vectorstore = build_vectorstore(pdf_files)
                st.session_state.index_status = (
                    f"Indexed: {len(pdf_files)} document(s)"
                )
            st.success("Indexing complete")

    # Status indicator
    status_color = (
        "green" if "Indexed" in st.session_state.index_status else "orange"
    )
    st.markdown(
        f"Status: :{status_color}[{st.session_state.index_status}]"
    )

# ---------------------------------------------------------------------------
# Main panel - Query and Results Interface
# ---------------------------------------------------------------------------
st.title("UPSC IT Wing - Local RAG Bot")
st.caption(
    "Query interface for UPSC IT Wing documents. "
    "Powered by Ollama (phi3) and ChromaDB with cosine similarity retrieval."
)

# Render chat history
for entry in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(entry["question"])

    with st.chat_message("assistant"):
        st.write(entry["answer"])

        # Expandable retrieval details
        with st.expander("View thought process and retrieval"):
            # Query embedding explanation
            st.markdown("**Step 1 - Query Vectorization:**")
            st.info(
                f'Your query "{entry["question"]}" was converted into a '
                f"high-dimensional embedding vector using the {EMBEDDING_MODEL} model. "
                f"This vector represents the semantic meaning of your question "
                f"in the same mathematical space as the document chunks."
            )

            # Retrieved chunks
            st.markdown("**Step 2 - Cosine Similarity Ranking:**")
            if entry["retrieval_details"]:
                for detail in entry["retrieval_details"]:
                    st.markdown(f"---")
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    with col_a:
                        st.markdown(
                            f"**Chunk {detail['rank']}** - "
                            f"{detail['title']}"
                        )
                        st.caption(
                            f"Source: {detail['source']} (Page {detail['page']})"
                        )
                    with col_b:
                        st.metric(
                            "Cosine Distance",
                            f"{detail['cosine_distance']:.4f}",
                        )
                    with col_c:
                        st.metric(
                            "Cosine Similarity",
                            f"{detail['similarity_pct']}%",
                        )
                    st.text(detail["content"])
            else:
                st.warning("No chunks retrieved.")

            # Exact prompt
            st.markdown("**Step 3 - Constructed Prompt to phi3:**")
            st.code(entry["prompt"], language="text")

# Chat input
question = st.chat_input("Ask a question about UPSC IT Wing documents...")

if question:
    if st.session_state.vectorstore is None:
        st.error(
            "Vector store not indexed. "
            "Use the sidebar to load sample PDFs and index documents first."
        )
    else:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching documents and generating answer..."):
                answer, retrieval_details, prompt = query_rag(
                    st.session_state.vectorstore,
                    question,
                    system_prompt,
                    top_k,
                )

            st.write(answer)

            # Expandable retrieval details
            with st.expander("View thought process and retrieval"):
                st.markdown("**Step 1 - Query Vectorization:**")
                st.info(
                    f'Your query "{question}" was converted into a '
                    f"high-dimensional embedding vector using the {EMBEDDING_MODEL} model. "
                    f"This vector represents the semantic meaning of your question "
                    f"in the same mathematical space as the document chunks."
                )

                st.markdown("**Step 2 - Cosine Similarity Ranking:**")
                if retrieval_details:
                    for detail in retrieval_details:
                        st.markdown(f"---")
                        col_a, col_b, col_c = st.columns([2, 1, 1])
                        with col_a:
                            st.markdown(
                                f"**Chunk {detail['rank']}** - "
                                f"{detail['title']}"
                            )
                            st.caption(
                                f"Source: {detail['source']} (Page {detail['page']})"
                            )
                        with col_b:
                            st.metric(
                                "Cosine Distance",
                                f"{detail['cosine_distance']:.4f}",
                            )
                        with col_c:
                            st.metric(
                                "Cosine Similarity",
                                f"{detail['similarity_pct']}%",
                            )
                        st.text(detail["content"])
                else:
                    st.warning("No chunks retrieved.")

                st.markdown("**Step 3 - Constructed Prompt to phi3:**")
                st.code(prompt, language="text")

        # Save to history
        st.session_state.chat_history.append(
            {
                "question": question,
                "answer": answer,
                "retrieval_details": retrieval_details,
                "prompt": prompt,
            }
        )
