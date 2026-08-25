# Deployment guide for Render + Neon + Groq

This project is prepared for cloud deployment with:
- Render for backend and frontend
- Neon.tech for PostgreSQL
- Groq as the LLM provider
- pgvector for vector search

## 1) Required environment variables

Create a `.env` file in the project root based on `.env.example`.

Example:

```env
PROJECT_NAME="Quantum Spanish Assistant API"
VERSION="1.0.0"
API_V1_STR="/api/v1"
ENVIRONMENT="production"
LLM_PROVIDER="groq"
LLM_MODEL="llama3"
OLLAMA_BASE_URL="http://localhost:11434"
GROQ_API_KEY="your_groq_api_key"
GROQ_MODEL="llama-3.1-8b-instant"
DATABASE_URL="postgresql://user:password@host:5432/dbname"
VECTOR_DB_PROVIDER="pgvector"
PGVECTOR_CONNECTION_STRING="postgresql://user:password@host:5432/dbname"
PGVECTOR_COLLECTION="quantum_spanish_docs"
CHROMA_PERSIST_DIRECTORY="./chroma_db"
ENABLE_WEB_INGESTION="true"
FASTAPI_URL="https://your-backend-render-url.onrender.com/api/v1/quantum-chat"
```

## 2) Neon setup

1. Create a PostgreSQL database in Neon.tech.
2. Copy the connection string.
3. Paste it into:
   - `DATABASE_URL`
   - `PGVECTOR_CONNECTION_STRING`

## 3) Groq setup

1. Create a Groq account.
2. Generate an API key.
3. Save it as `GROQ_API_KEY`.
4. Model suggestion: `llama-3.1-8b-instant`

## 4) Render setup

Use the included `render.yaml` file.

In Render, set environment variables manually for:
- `GROQ_API_KEY`
- `DATABASE_URL`
- `PGVECTOR_CONNECTION_STRING`
- `FASTAPI_URL`

## 5) Deployment order

1. Deploy the backend service first.
2. Copy its public URL.
3. Put that URL into `FASTAPI_URL` for the frontend service.
4. Deploy the frontend service.

## 6) Important note

This project no longer depends on local Ollama at runtime. The LLM call is routed through Groq by default.

If local development is needed again, switch:

```env
LLM_PROVIDER="ollama"
```

and provide a working `OLLAMA_BASE_URL`.
