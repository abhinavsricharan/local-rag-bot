# Data Directory Overview

This folder contains all the data required for the local RAG pipeline to function.

## 1. Vector Store (`chroma_db/`)
This is the mathematical brain of the chatbot. When the system reads the PDF documents, it converts the text into mathematical representations known as embeddings. These embeddings allow the system to perform fast similarity searches to find the exact paragraphs that answer your questions. This entire database is stored locally in the `chroma_db` folder, ensuring no data ever leaves the machine.

## 2. Document Metadata (`metadata.json`)
This acts as our library catalog. For each PDF placed in this directory, this file holds the corresponding title, date, and keywords. When the ingestion script processes the PDFs, it attaches this metadata to the chunks of text. This helps the AI understand the exact source and context of the information it is reading.

## 3. Template PDFs
The PDF files located here are demonstration templates outlining mock cybersecurity and e-Governance guidelines for the UPSC IT Wing. 
*Note: These are completely fabricated for testing purposes and do not reflect any real government infrastructure or policy.* 
To use this system with real data, simply place your own official PDF documents in this folder and update `metadata.json` accordingly.
