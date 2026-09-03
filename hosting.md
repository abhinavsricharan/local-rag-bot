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

## 3. Step-by-Step On-Premises Setup

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
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

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

## 4. Operational Maintenance and Best Practices

1. Shared Vector Store Integrity:
   Ensure the data/chroma_db folder is pre-indexed before launching the multi-user service. During multi-user querying, the database operates in read-only mode, preventing file locking conflicts across sessions.

2. Document Updates:
   When adding new policies or PDFs to the data directory, schedule index updates during low-usage maintenance windows.

3. Monitoring Memory:
   Keep an eye on system RAM and VRAM usage. The baseline memory requirement is roughly 4 GB for the operating system and Streamlit, 2.5 GB for Phi-3 Mini, and 0.5 GB for nomic-embed-text, totaling approximately 7 GB of baseline working memory.
