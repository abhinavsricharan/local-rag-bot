# Data Directory Overview

This folder contains all the data required for the local RAG pipeline to function.

## 1. Vector Store (`chroma_db/`)
This is the mathematical brain of the chatbot. When the system reads the PDF documents, it converts the text into mathematical representations known as embeddings. 

Inside this directory, you will find two types of data:
- **`chroma.sqlite3`**: A lightweight relational database that stores the document metadata (titles, dates, keywords) and the exact text chunks extracted from the PDFs.
- **Binary Index Files (`.bin`)**: These files hold the mathematical vectors (embeddings) structured in a highly optimized graph format (HNSW). This graph allows the system to perform lightning-fast similarity searches to find the exact paragraphs that answer your questions. 

*Note: Because the `.bin` files are large and specific to the local machine's generation, they are not uploaded to GitHub. You must run `python ingest.py` on your local machine to generate these vector files before querying.*

## 2. Document Metadata (`metadata.json`)
This acts as our library catalog. For each PDF placed in this directory, this file holds the corresponding title, date, and keywords. When the ingestion script processes the PDFs, it attaches this metadata to the chunks of text. This helps the AI understand the exact source and context of the information it is reading.

## 3. Template PDFs
The PDF files located here are demonstration templates outlining mock cybersecurity and e-Governance guidelines for the UPSC IT Wing. 
*Note: These are completely fabricated for testing purposes and do not reflect any real government infrastructure or policy.* 
To use this system with real data, simply place your own official PDF documents in this folder and update `metadata.json` accordingly.
