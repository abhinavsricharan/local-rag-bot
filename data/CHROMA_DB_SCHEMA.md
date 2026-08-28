# Chroma DB Database Schema Explanation

The local vector store relies on an SQLite database (`chroma.sqlite3`) to manage metadata, text chunks, and document associations. Below is a breakdown of the critical tables and their roles in the RAG pipeline.

## Core Tables

### 1. `collections` & `collection_metadata`
Chroma organizes data into "collections" (think of them as distinct folders or tables for different projects). 
- **`collections`**: Stores the unique ID, name, and dimensionality of the embeddings in the collection.
- **`collection_metadata`**: Stores configuration and custom metadata tied to the entire collection rather than individual documents.

### 2. `embeddings`
This is a linking table. It maps every document chunk (`embedding_id`) that our ingestion script creates to a specific segment within a collection. It tracks the chronological insertion sequence (`seq_id`) and creation timestamp.

### 3. `embedding_metadata` & `embedding_metadata_array`
These tables store the actual contextual data. When the script parses the PDFs and our `metadata.json`, the output ends up here.
- **Text Chunks**: The actual paragraphs from the PDFs are stored as strings in these tables.
- **Custom Metadata**: The titles, keywords, dates, and page numbers we provide are stored as key-value pairs linked to the document chunk ID. When you ask a question, the AI retrieves the `string_value` from this table.

### 4. `segments` & `segment_metadata`
Segments define the physical storage partitions and search scopes for the data. For instance, Chroma uses one segment scope for vector (HNSW) search, one for metadata filtering, and one for full-text search.

### 5. `embeddings_queue`
This table acts as the ingestion staging area. When you run `python ingest.py`, documents and their raw mathematical vectors (BLOB format) are temporarily queued here before being processed and permanently indexed into the `.bin` graph files and the metadata tables.

## Full-Text Search Tables
### `embedding_fulltext_search` (and related `_data`, `_idx`, `_content`, `_docsize`, `_config` tables)
Chroma utilizes SQLite's FTS5 (Full-Text Search) extension to allow rapid keyword-based search over the text chunks. These virtual tables manage the inverted index, allowing the system to quickly locate specific terms (like "cybersecurity" or "PostgreSQL") within the `embedding_metadata` text.

---
*Note: The actual high-dimensional floating-point vectors used for similarity search are stored in the optimized `.bin` (HNSW graph) files outside of this SQLite database, as SQLite is not optimized for large-scale mathematical vector traversal.*
