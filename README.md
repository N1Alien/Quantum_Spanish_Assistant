# Hybrid Quantum Spanish Assistant (Full-Stack AI System)

A cutting-edge, production-grade distributed system designed for intelligent Spanish language learning. The application fuses **Quantum Computing simulation (PennyLane + PyTorch)** on local GPU architecture with an autonomous **RAG (Retrieval-Augmented Generation)** pipeline. Upon startup, the system automatically scrapes grammar and vocabulary data from the web, allowing local LLM models to serve as highly accurate language tutors without data hallucinations.

## 🛠️ Tech Stack & Infrastructure

*   **Web Framework (Backend):** [FastAPI](https://tiangolo.com) – Asynchronous, high-performance API backend with automated Pydantic v2 data validation.
*   **User Interface (Frontend):** [Streamlit](https://streamlit.io) – Modern frontend utilizing `SpeechRecognition` (Google STT) for voice input and `gTTS` (Google Text-to-Speech) for fluent audio feedback.
*   **Quantum Core:** [PennyLane](https://pennylane.ai) – Quantum circuit simulation integrated with a **PyTorch** execution interface running natively on local GPU hardware (NVIDIA RTX 5080).
*   **AI Orchestration:** [LangChain](https://langchain.com) – Manages prompt templates, dynamic context injection, and document loading.
*   **Local LLM Engine:** [Ollama](https://ollama.com) – Powering `llama3` for dialogue generation and `nomic-embed-text` for real-time text vectorization.
*   **Vector Database:** [ChromaDB](https://trychroma.com) – High-density vector storage executing semantic similarity searches.
*   **Relational Database:** [PostgreSQL 15](https://postgresql.org) – Secure, persistent tracking of complete chat histories and conversation analytics via **SQLAlchemy ORM**.
*   **DevOps & Automation:** [Docker Compose](https://docker.com) for containerized database management and automated Bash orchestration (`run.sh`).

## 📐 Distributed Architecture

The system operates as decoupled microservices communicating securely via RESTful HTTP protocols:

```text
Quantum_Spanish_Assistant/
├── app/
│   ├── api/            # Presentation layer: FastAPI HTTP routes & endpoints
│   ├── core/           # System core: config (Pydantic Settings), DB connections
│   ├── models/         # SQLAlchemy ORM database schemas & Pydantic models
│   ├── services/       # Business logic: QuantumService, AIService, VectorService
│   └── main.py         # FastAPI application entry point and startup events
├── .env                # Secured system environment configurations
├── app.py              # Streamlit client application (Voice UI & Audio synthesis)
├── docker-compose.yml  # Multi-container infrastructure definition (PostgreSQL on port 5433)
├── run.sh              # Single-command automated shell orchestrator (with process cleanup)
└── README.md           # Technical documentation
```

## 🚀 Key Engineering Features

1.  **Autonomous Web Data Ingestion:** Implements a *Self-Sustaining Data Agent* loop on startup. Using LangChain's `WebBaseLoader` and `BeautifulSoup4`, the backend dynamically scrapes live linguistic data, chunks it (`RecursiveCharacterTextSplitter`), generates embeddings, and saves it into ChromaDB before accepting network requests.
2.  **Quantum Style Modification:** Features a Variational Quantum Circuit (VQC) with rotation (`RX`) and entangling (`CNOT`) gates. Text lengths and mathematical properties are mapped to a 3-qubit register. PauliZ expectation values modulate the LLM's teaching style (e.g., triggering localized Spanish idioms or context-aware surprise questions).
3.  **Production Network Isolation:** Configured with multi-project port stability. The containerized PostgreSQL database maps to system port `5433`, eliminating local daemon port allocation collisions.
4.  **Bulletproof DevOps Automation:** The entire full-stack system launches with a single `./run.sh` invocation. The script implicitly verifies database health, spins up services headlessly in the background, launches the local browser, and uses Linux environment `trap` handlers to gracefully terminate all process forks upon receiving `SIGINT` (`Ctrl+C`).

## 📦 Single-Command Initialization (Linux/macOS)

### 1. Prerequisites
Ensure the system has a running [Ollama](https://ollama.com) engine with the specified models pulled:
```bash
ollama pull llama3
ollama pull nomic-embed-text
```

### 2. Launching the System
Clone the project structure, activate your environment, and execute the automated shell program:
```bash
# Set up Python Virtual Environment
python -m venv .venv
source .venv/bin/activate  # (.venv/bin/activate.fish for Fish Shell)
pip install -r requirements.txt

# Grant execution rights and run the automated orchestrator
chmod +x run.sh
./run.sh
```
The script will initialize the dockerized PostgreSQL layer, start the web scraping ingestion engine, spin up the backend and frontend nodes simultaneously, and automatically open your default browser.

## 🌍 Cross-Platform Compatibility Notes

While the application core is completely cross-platform, please note the following environment considerations:

*   **Operating Systems (Windows/macOS/Linux):** The application backend, Streamlit frontend, and PostgreSQL Docker layer are 100% platform-agnostic and will run on Windows, macOS, and Linux out of the box. 
*   **Orchestration Script (`run.sh`):** The single-command automation script is designed natively for UNIX-like environments (Linux/macOS). To use this one-click automation on Windows, you must run it inside **WSL2 (Windows Subsystem for Linux)**. Alternatively, Windows users can launch the services manually by running `uvicorn app.main:app` and `streamlit run app.py` in separate terminal windows.
*   **Hardware Requirements (Local AI):** This project runs heavyweight open-source LLMs and tensor math completely locally to guarantee maximum privacy and data ownership. Running the PyTorch tensors and Ollama inference loops requires a system with a dedicated GPU (optimized for CUDA-enabled NVIDIA architectures). On hardware lacking a dedicated GPU, Ollama will fallback to CPU inference, which may drastically increase response latency.

## 💼 Technical Interview Preparation (Q&A for Authors)

*   **Why split the system into FastAPI and Streamlit instead of writing everything in a single UI script?**
    *Answer:* To strictly adhere to the principle of microservice decoupling and horizontal scaling. Heavy workloads like PyTorch tensor operations, quantum register execution via PennyLane, and vector searches belong in a dedicated, high-throughput backend layer (FastAPI). The client interface (Streamlit) remains lightweight and task-focused on voice streaming and audio rendering. This enables swapping the frontend for a mobile app or a production web framework (React/Vue) in the future without editing core AI logic.
*   **What is the benefit of your background process management pattern in the Bash script?**
    *Answer:* It solves the critical enterprise issue of "zombie processes" clogging ports in dev environments. By recording background process identifiers (`$!`) into variables (`BACKEND_PID`, `FRONTEND_PID`) and attaching a `trap` hook to `SIGINT` / `EXIT`, the OS guarantees that whenever the main shell process stops, all child background server forks are immediately and safely killed, preventing port locking on `8000` and `8501`.
*   **How does the system ensure relational database session safety under load?**
    *Answer:* By utilizing an architectural Dependency Injection pattern via FastAPI's sub-dependencies. Using the `yield` statement inside a structured `try...finally` block creates an elegant scope boundary for database transaction sessions. Once an API call satisfies its data query, the connection pool socket is guaranteed to close cleanly, preventing memory leaks and database connection exhaustion.
