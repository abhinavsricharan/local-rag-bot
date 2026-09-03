# On-Premises Hosting and Multi-User Deployment Guide

## Overview

This guide details the technical and operational requirements for hosting the UPSC IT Wing Local RAG Bot on on-premises private infrastructure. Running on-premises ensures complete data sovereignty: no documents, candidate information, or query transcripts ever leave your local network.

---

## 1. Can You Host Completely on CPU?

Yes. Dedicated GPUs are not strictly required to deploy and serve this application.

### How CPU Hosting Works
- The Phi-3 Mini model has 3.8 billion parameters. When quantized to 4-bit (Q4_0), the model size shrinks to approximately 2.2 GB.
- Because it is 2.2 GB, the entire model fits comfortably into standard system RAM.
- Modern x86-64 processors with AVX2 or AVX-512 instruction sets handle the matrix math directly.

### The Trade-Off: Memory Bandwidth and Concurrency
- When running on a CPU, single-user generation speed is typically 8 to 18 tokens per second on modern hardware, which is fast enough for reading responses in real time.
- The primary limitation of CPU hosting is memory bandwidth. Standard system RAM (DDR4 or DDR5) provides roughly 50 to 80 GB/s of bandwidth, which is shared across all CPU cores.
- If several users submit questions at the exact same moment, token generation slows down proportionally because the cores compete for memory bus access.
- In contrast, dedicated GPUs provide high-bandwidth video memory (300 to 900+ GB/s), allowing multiple parallel user streams without noticeable degradation.

---

## 2. Hardware Sizing Matrix

### Scenario A: Small Team (2 to 5 Concurrent Users)

In standard office environments, queries are naturally staggered throughout the day. Simultaneous clicks are rare, making a CPU-only setup practical.

#### Option 1: CPU-Only Setup (Cost-Effective)
- Processor: 8 to 16 physical cores (e.g., AMD Ryzen 7/9, Intel Core i7/i9, or single-socket Intel Xeon Silver / AMD EPYC).
- RAM: 32 GB DDR4 or DDR5 (configured in dual-channel or quad-channel mode to maximize memory throughput).
- Storage: 50 GB NVMe PCIe Gen3 or Gen4 SSD.
- Performance: Single-user responses take 4 to 8 seconds. If 2 or 3 users prompt simultaneously, responses take 10 to 18 seconds.

#### Option 2: Entry-Level GPU Setup (Optimal Responsiveness)
- GPU: 1x NVIDIA RTX 3060 (12 GB VRAM) or RTX 4060 Ti (16 GB VRAM) or workstation NVIDIA RTX A2000.
- Processor: Any standard 6 to 8 core CPU.
- RAM: 16 GB to 32 GB.
- Performance: Instant prompt processing; steady 35 to 50 tokens per second across all active users.

---

### Scenario B: Departmental Scale (20+ Concurrent Users)

With 20 or more users actively using the dashboard, overlap is guaranteed, and request queues form.

#### Option 1: High-End Multi-Socket CPU Server
- Processor: Dual-socket server (e.g., 2x AMD EPYC or 2x Intel Xeon Gold, providing 32 to 64 physical cores).
- RAM: 64 GB to 128 GB registered ECC RAM populated across all memory channels.
- Performance: Multiple parallel streams can run, but high traffic bursts will cause queuing, resulting in 15 to 30 second wait times per request.

#### Option 2: Enterprise GPU Server (Recommended for High Concurrency)
- GPU: 1x NVIDIA A10 (24 GB VRAM), NVIDIA L4 (24 GB VRAM), or NVIDIA RTX 3090 / 4090 (24 GB VRAM).
- Processor: 16-core CPU.
- RAM: 64 GB system RAM.
- Storage: 100 GB NVMe SSD.
- Concurrency Configuration: With 24 GB VRAM, you can set OLLAMA_NUM_PARALLEL=8 to 12, allowing 8 to 12 completely parallel generation streams without queue delays.

---

## 3. Technical Justification for RAM and GPU Requirements

A common question when planning infrastructure is: "If the quantized model is only 2.2 GB, why do we need 32 GB of system RAM or a 12 GB to 24 GB GPU?"

The answer lies in the mathematical combination of static weights, the dynamic Key-Value (KV) cache created for every concurrent user, operating system overhead, and memory bus bandwidth physics.

### 3.1. Static Base Footprint (Model Weights)
Before any user types a query, the system must keep both local models resident in memory:
- Phi-3 Mini (3.82 billion parameters, Q4_0 quantized): 2.2 GB
- nomic-embed-text (137 million parameters, FP16): 0.3 GB
- Total static model weight memory: 2.5 GB

### 3.2. The Dynamic Variable: Key-Value (KV) Cache per User Slot
When an LLM generates text, it retains the mathematical representation of all previous tokens in a scratchpad called the Key-Value (KV) cache. Without this cache, the model would need to reprocess the entire document context for every single new word generated.

The memory required by the KV cache follows an exact mathematical formula:
KV Cache Memory = 2 * Layers * Attention Heads * Head Dimension * Context Length * Bytes per Element

For Phi-3 Mini:
- Number of layers: 32
- Attention heads: 32
- Head dimension: 96
- Data precision: 2 bytes (FP16)
- Memory per token: 2 * 32 * 32 * 96 * 2 bytes = 393,216 bytes (approximately 0.384 MB per token)

In our RAG pipeline, each request includes the system prompt, retrieved document chunks, user question, and generated answer, averaging roughly 4,096 tokens in the active context window:
- KV Cache per user slot (at 4,096 tokens): 4,096 * 0.384 MB = 1.57 GB of dedicated memory per slot.

When multiple users query simultaneously, Ollama provisions parallel context slots:
- 1 concurrent user slot: 1.57 GB
- 4 concurrent user slots (OLLAMA_NUM_PARALLEL=4): 4 * 1.57 GB = 6.28 GB
- 8 concurrent user slots (OLLAMA_NUM_PARALLEL=8): 8 * 1.57 GB = 12.56 GB
- 12 concurrent user slots (OLLAMA_NUM_PARALLEL=12): 12 * 1.57 GB = 18.84 GB

### 3.3. Application, Operating System, and Runtime Overhead
Beyond the models and the KV cache, other components require dedicated RAM:
- Host Operating System (Windows Server or Linux kernel, background daemons, security agents): 2.5 GB to 3.5 GB.
- Python runtime, Streamlit multi-user session state buffers, LangChain memory, and in-memory ChromaDB vector search structures: 1.5 GB to 2.5 GB.
- CUDA context and PyTorch driver workspace (on GPU systems): 1.0 GB.
- Total system and application overhead: roughly 5.0 GB to 6.0 GB.

### 3.4. Why 32 GB System RAM is Required for CPU Hosting (2 to 5 Users)
Summing up the requirements for a 4-slot CPU host:
- Operating System and background tasks: 3.0 GB
- Streamlit application and ChromaDB: 2.0 GB
- Model static weights (Phi-3 Mini + embeddings): 2.5 GB
- 4 parallel KV cache slots: 6.3 GB
- Total minimum active working set: 13.8 GB

If this system were hosted on a 16 GB machine:
1. The working set (13.8 GB) leaves less than 2 GB of free buffer. Any sudden spike in document chunk size or background processes pushes memory usage to 100%, causing the OS to swap memory pages to the hard drive. Swapping reduces token generation speed to less than 1 token per second.
2. Memory Bus Channeling: Standard 32 GB configurations use two 16 GB sticks in dual-channel mode (or four 8 GB sticks in quad-channel mode). This doubles the physical memory bus width, providing 50 to 80 GB/s bandwidth instead of 25 GB/s. Because CPU inference is strictly memory-bandwidth bound, dual-channel 32 GB RAM literally doubles token generation speed compared to a single 16 GB stick.

### 3.5. Why 12 GB VRAM is Required for GPU Hosting (2 to 5 Users)
Summing up the VRAM requirements for a 4-slot GPU host:
- CUDA context and driver runtime: 1.0 GB
- Phi-3 Mini static weights: 2.2 GB
- nomic-embed-text static weights: 0.3 GB
- 4 parallel KV cache slots: 6.3 GB
- Total required dedicated VRAM: 9.8 GB

Why an 8 GB GPU is insufficient:
- Consumer GPUs with 8 GB VRAM (such as an RTX 3050, RTX 3070 8GB, or RTX 4060 8GB) do not have enough room for 9.8 GB. When VRAM fills up, CUDA drivers either crash with an Out-Of-Memory (OOM) error or fall back to system RAM over the slow PCIe bus, degrading generation speed by over 80%.
- A 12 GB GPU (such as an RTX 3060 12GB or RTX 4060 Ti 16GB) provides 9.8 GB of working room plus a 2.2 GB safety margin to absorb longer context queries without spilling over.

### 3.6. Why 24 GB VRAM and 64 to 128 GB RAM are Required for 20+ Users
At departmental scale with 8 to 12 active parallel streams:
- Static model weights: 2.5 GB
- CUDA runtime: 1.2 GB
- 8 to 12 KV cache slots: 12.6 GB to 18.8 GB
- Total required VRAM: 16.3 GB to 22.5 GB

A 24 GB enterprise GPU (such as the NVIDIA A10, L4, or RTX 3090/4090) is the exact mathematical threshold needed to house 8 to 12 completely parallel streams without dropping requests or queueing users. On CPU servers, supporting 20+ active users across multi-socket NUMA nodes requires 64 GB to 128 GB registered ECC RAM across all memory channels to avoid CPU core starvation.

---

## 4. Step-by-Step On-Premises Setup

### Step 1: Configure Ollama for Network Access and Concurrency

By default, Ollama only listens on localhost (127.0.0.1). To allow access across your internal network or from other server processes, configure the following system environment variables on the hosting machine:

#### On Windows Server (PowerShell as Administrator):
```powershell
[System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'Machine')
[System.Environment]::SetEnvironmentVariable('OLLAMA_NUM_PARALLEL', '4', 'Machine')
[System.Environment]::SetEnvironmentVariable('OLLAMA_MAX_LOADED_MODELS', '2', 'Machine')
[System.Environment]::SetEnvironmentVariable('OLLAMA_FLASH_ATTENTION', '1', 'Machine')
```

#### On Linux Server (/etc/systemd/system/ollama.service.d/environment.conf):
```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_FLASH_ATTENTION=1"
```

Explanation of settings:
- OLLAMA_HOST=0.0.0.0:11434: Binds the Ollama API to all network interfaces.
- OLLAMA_NUM_PARALLEL=4: Allocates 4 concurrent slots in memory to process up to 4 user questions at once.
- OLLAMA_MAX_LOADED_MODELS=2: Keeps both the text generation model (phi3) and the embedding model (nomic-embed-text) loaded in memory together, avoiding constant swapping.
- OLLAMA_FLASH_ATTENTION=1: Enables optimized attention calculation to save memory and increase speed.

After setting these variables, restart the Ollama service.

---

### Step 2: Serve the Streamlit Dashboard Across the Intranet

To make the user interface reachable by team members on the local network, bind Streamlit to all network interfaces:

```bash
streamlit run streamlit.py --server.address 0.0.0.0 --server.port 8501
```
(Alternatively, `streamlit run app.py` can be used interchangeably).

Colleagues on the same local network or connected via corporate VPN can now access the bot in their browser at:
```text
http://<SERVER_INTERNAL_IP>:8501
```
(For example: http://192.168.1.100:8501 or http://10.0.5.20:8501)

Each user connection receives an isolated session state, meaning conversation histories and inspection views do not interfere with one another.

---

### Step 3: Production Hardening with NGINX Reverse Proxy (Optional)

For formal enterprise deployment with custom domain names and HTTPS, place an NGINX reverse proxy in front of Streamlit.

Sample NGINX configuration snippet (/etc/nginx/conf.d/upsc_bot.conf):
```nginx
server {
    listen 80;
    server_name upsc-bot.internal;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name upsc-bot.internal;

    ssl_certificate /etc/ssl/certs/upsc_internal.crt;
    ssl_certificate_key /etc/ssl/private/upsc_internal.key;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

---

## 5. Operational Maintenance and Best Practices

1. Shared Vector Store Integrity:
   Ensure the data/chroma_db folder is pre-indexed before launching the multi-user service. During multi-user querying, the database operates in read-only mode, preventing file locking conflicts across sessions.

2. Document Updates:
   When adding new policies or PDFs to the data directory, schedule index updates during low-usage maintenance windows.

3. Monitoring Memory:
   Keep an eye on system RAM and VRAM usage. The baseline memory requirement is roughly 4 GB for the operating system and Streamlit, 2.5 GB for Phi-3 Mini, and 0.5 GB for nomic-embed-text, totaling approximately 7 GB of baseline working memory before parallel KV cache allocation.
