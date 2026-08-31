# ⚛️ Hybrid Quantum-AI Spanish Assistant

An advanced, cloud-deployed language learning MVP that combines **conversational AI**, **virtual quantum computing simulation**, and an ultra-fast **multimodal voice processing pipeline**. Powered entirely by the stable Google Gemini 3.6 ecosystem, this assistant adapts its coaching style dynamically and provides real-time contextual helpers for students.

---

## 🚀 Key Features

* **Cloud-Native Speech-to-Text:** Processes raw webm/ogg audio chunks from the browser directly through the Google Gemini Multimodal Audio SDK for sub-second, error-free transcription.
* **Dynamic Contextual Scaffolding:** Generates exactly 10 real-time, context-aware suggested Spanish responses with English translations tailored directly to the AI's latest question.
* **Quantum Style Adaptation:** Integrates a virtual quantum circuit layer (via PennyLane & PyTorch) that processes text tokens to dynamically shift the AI's teaching persona and linguistic complexity.
* **Production-Grade Architecture:** Features a clean separation of concerns with a FastAPI backend router, production environment variable validation (Pydantic Settings), and persistent session memory management (Streamlit State).
* **Audio Synthesis (TTS):** Automatically generates native Spanish audio responses utilizing gTTS via temporary container-safe storage paths (`/tmp`).

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit (v1.42.0+ native audio components), HTML5/JavaScript
* **Backend Framework:** FastAPI, Uvicorn, Python 3.11
* **AI & Multimodal Core:** Google GenerativeAI SDK (`gemini-3.6-flash`), gTTS
* **Quantum & ML Simulation:** PennyLane, PyTorch, Autoray
* **Database & DevOps:** PostgreSQL (Neon.tech via SSL), SQLAlchemy ORM, Docker

---

## 📋 Architecture & Data Flow

1. **Audio Capture:** User records voice via Streamlit's native `st.audio_input` controller.
2. **Signature Verification:** Frontend computes an immediate cryptographic hash signature (`last_audio_signature`) to eliminate duplicate requests and mitigate server-side CPU throttling.
3. **Multimodal Ingestion:** FastAPI passes the raw audio buffer directly into the Google GenAI SDK pipeline, bypassing unstable legacy speech-recognition binaries.
4. **LLM Synthesis:** The context-aware prompt enforces a strict structural response containing the native Spanish dialogue block, English translation layer, and exactly 10 customized reaction prompts.

---

## ⚙️ Environment Variables & Deployment

The application is containerized and optimized for serverless platforms like Render.com.

### Backend Configurations (`quantum-spanish-backend`)
* `ENVIRONMENT`: `production`
* `GEMINI_API_KEY`: `your_secure_gemini_api_token`
* `DATABASE_URL`: `postgresql://user:pass@host/db?sslmode=require`
* `LLM_PROVIDER`: `gemini`

### Frontend Configurations (`quantum-spanish-frontend`)
* `FASTAPI_URL`: `https://onrender.com`

---

## 💻 Local Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com
   cd quantum-spanish-assistant
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_actual_api_key
   FASTAPI_URL=http://127.0.0.1:8000
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Backend (FastAPI):**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Run Frontend (Streamlit):**
   ```bash
   streamlit run frontend.py --server.port=8501
   ```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.
