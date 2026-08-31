# Pipeline Evaluation and Chunking Strategy

This document addresses corner cases in the RAG pipeline, specifically focusing on how large documents are processed, how text segments are managed without losing context, and how the underlying mathematical retrieval works.

## 1. Handling Large PDF Documents
When processing large PDFs (e.g., hundreds of pages), loading the entire document into an AI's memory at once is impossible. Our pipeline utilizes the `PyPDFDirectoryLoader`, which streams documents page by page. This ensures that memory consumption remains stable regardless of the file size, allowing the system to scale to thousands of pages seamlessly.

## 2. Segmenting Strategy and Topic Overlap
Once loaded, the text must be broken down into digestible pieces for the vector database and the AI model. 

We utilize a **Recursive Character Text Splitter** with the following parameters:
- **Chunk Size**: 500 characters.
- **Chunk Overlap**: 50 characters.

### Why Overlapping Segments?
Documents are rarely formatted perfectly. If we split a document rigidly at 500 characters, a single topic or even a single sentence might be cut in half, leaving the AI with incomplete context. 

By enforcing a 50-character overlap, the end of Chunk A is duplicated at the beginning of Chunk B. If a topic spans across two chunks, this overlap acts as a bridge. When the database searches for a specific topic, it will retrieve the chunks containing the full context without abrupt cut-offs.

## 3. Query Embedding and Retrieval Math
When a user asks a question, the system does not simply search for matching keywords. 

1. **Query Embedding**: The user's English query is passed to the `nomic-embed-text` model, which translates the question into a high-dimensional mathematical vector (embedding) representing its semantic meaning.
2. **Distance Calculation**: The system compares this query vector against all the document segment vectors stored in the Chroma database.
3. **Similarity Scoring**: It calculates the geometric distance between the query vector and the segment vectors. Segments with the closest proximity in the embedding space (lowest distance scores) are mathematically the most semantically relevant to the question.

## 4. Evaluation Pipeline Snapshot
We built an evaluation script (`evaluate_rag.py`) to test this exact behavior. Below is a snapshot of the pipeline taking a query, embedding it, calculating the distance, and returning the most relevant chunks.

```text
--- Evaluation for Query: 'What happens if there is a security breach?' ---
1. Loading embedding model (nomic-embed-text)...
2. Connecting to local vector store (Chroma)...
3. Embedding user query and calculating distance to document chunks...

--- Chunk 1 | Distance Score: 310.3277 ---
Source: data\nic_cybersecurity_guidelines.pdf (Page 0)
Content snippet (showing overlap context):
Vulnerability scanning must be performed quarterly.
4. Incident Response:
Any security breach must be reported to the NIC CERT within 24 hours.
System logs must be retained for a minimum of 1 year.

--- Chunk 2 | Distance Score: 398.6416 ---
Source: data\nic_cybersecurity_guidelines.pdf (Page 0)
Content snippet (showing overlap context):
NIC Cybersecurity Guidelines for UPSC Portals
1. Introduction:
This document outlines the cybersecurity guidelines for all UPSC web portals managed by NIC.
All portals must implement TLS 1.3 for encryption.
2. Access Control:
Multi-factor authentication (MFA) is mandatory for all administrative access.
Passwords must be at least 14 characters long and rotated every 90 days.
3. Security Audits:
Annual security audits are required for all UPSC IT infrastructure.
```

As demonstrated, the system successfully embedded the query and fetched Chunk 1 as the primary answer, which directly addresses incident response protocols, achieving the best distance score.
