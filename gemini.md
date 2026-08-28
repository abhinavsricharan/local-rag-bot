# Gemini Project Guidelines and Setup

## Project Goal
Build a lightweight local Retrieval-Augmented Generation (RAG) system using Phi-3-mini to query a collection of PDFs and structured metadata database without relying on external cloud APIs.

## Core Directives

1. Strict Punctuation Rules:
   - Do not use em dashes anywhere in the codebase, comments, commit messages, or documentation.
   - Use standard hyphens (-) or colons (:) when separation is necessary.

2. Zero Emoji Policy:
   - Do not include emojis anywhere in the repository.
   - This applies to source code, docstrings, markdown files, configuration files, and git logs.

3. Code and Implementation Standards:
   - Write very minimal code for all tasks with zero unnecessary boilerplate.
   - Verify all logic and validate responses prior to output.
   - Maintain clean, consistent formatting throughout all modules.

4. Documentation Requirements:
   - Write clear, concise, and technical descriptions.
   - Ensure all README and markdown files adhere strictly to the punctuation and emoji restrictions outlined above.

## System Prerequisites

- Python 3.10 or higher
- Local model runtime (such as Ollama) with Phi-3-mini installed and configured
- Local embedding model (such as nomic-embed-text)

## Setup Steps

1. Environment Configuration:
   - Initialize a Python virtual environment.
   - Activate the environment.

2. Dependency Installation:
   - Install minimal required packages for local vector storage, document parsing, and RAG orchestration.
   - Recommended packages: langchain, langchain-community, chromadb, pypdf.

3. Local Model Verification:
   - Ensure the local runtime daemon is active.
   - Verify Phi-3-mini responds to local test prompts.
   - Ensure the local embedding model is downloaded and ready for vectorization.

4. Document Ingestion and Metadata Processing:
   - Place source PDF documents in the designated data directory.
   - Structure metadata in JSON format linking document IDs, titles, dates, and keywords.
   - Parse PDFs and chunk content into manageable text segments.

5. Vector Indexing:
   - Pass document chunks and metadata to the local embedding model.
   - Index vector embeddings into the local Chroma vector store.

6. RAG Pipeline Execution:
   - Connect the local vector retriever to the Phi-3-mini model instance.
   - Run simple English queries to test end-to-end retrieval and local generation.
