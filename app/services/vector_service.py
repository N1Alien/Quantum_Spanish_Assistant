import os
from app.core.config import settings

class VectorService:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.persist_directory = settings.CHROMA_PERSIST_DIRECTORY
        self.urls_to_scrape = [
            "https://wikipedia.org",
            "https://wikipedia.org",
        ]
        self.vector_provider = (settings.VECTOR_DB_PROVIDER or "chroma").lower()
        self.embeddings = None
        self.pg_vector = None
        self.chroma_client = None

    def initialize_vector_db(self):
        """Inicjalizacja bazy bez obciążania pamięci RAM (Serverless Embeddings)."""
        if self.pg_vector is not None or self.chroma_client is not None:
            return

        if self.vector_provider == "pgvector":
            try:
                from langchain_postgres import PGVector
                from langchain_groq import GroqEmbeddings

                # Używamy zdalnego API Groq do generowania wektorów - zużycie RAM = 0 MB!
                self.embeddings = GroqEmbeddings(
                    model="mixedbread-ai/mxbai-embed-large",
                    groq_api_key=settings.GROQ_API_KEY
                )
                
                self.pg_vector = PGVector(
                    connection=settings.PGVECTOR_CONNECTION_STRING,
                    collection_name=settings.PGVECTOR_COLLECTION,
                    embeddings=self.embeddings,
                )
            except Exception as e:
                print(f"⚠️ Błąd inicjalizacji PGVector: {str(e)}")
                self.pg_vector = None
        else:
            try:
                from langchain_ollama import OllamaEmbeddings
                from langchain_community.vectorstores import Chroma
                self.chroma_client = Chroma
                self.embeddings = OllamaEmbeddings(
                    model="nomic-embed-text",
                    base_url=settings.OLLAMA_BASE_URL,
                )
            except Exception as e:
                print(f"⚠️ Błąd inicjalizacji Chroma: {str(e)}")
                self.chroma_client = None

    def auto_fetch_web_knowledge(self):
        self.initialize_vector_db()
        if not self.embeddings:
            print("⚠️ Brak aktywnego dostawcy embeddings. Pomijam pobieranie wiedzy.")
            return

        try:
            from langchain_community.document_loaders import WebBaseLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            print("🌐 [Web Ingestion] Rozpoczynam automatyczne pobieranie wiedzy z internetu...")
            loader = WebBaseLoader(self.urls_to_scrape)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
            chunks = text_splitter.split_documents(documents)

            if self.vector_provider == "pgvector" and self.pg_vector is not None:
                self.pg_vector.add_documents(chunks)
                print(f"🚀 [RAG Sukces] Zasilono PGVector ({len(chunks)} fragmentów)!")
                return

            if self.chroma_client is not None:
                from langchain_community.vectorstores import Chroma
                Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory,
                )
                print(f"🚀 [RAG Sukces] Zasilono Chroma ({len(chunks)} fragmentów)!")

        except Exception as e:
            print(f"⚠️ Nie udało się automatycznie pobrać danych www: {str(e)}")

    def get_relevant_context(self, query: str, k: int = 2) -> str:
        self.initialize_vector_db()
        try:
            if self.vector_provider == "pgvector" and self.pg_vector is not None:
                docs = self.pg_vector.similarity_search(query, k=k)
                return "\n---\n".join([doc.page_content for doc in docs])

            if self.chroma_client is not None and os.path.exists(self.persist_directory):
                from langchain_community.vectorstores import Chroma
                vector_db = Chroma(

                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )
                docs = vector_db.similarity_search(query, k=k)
                return "\n---\n".join([doc.page_content for doc in docs])

            return ""
        except Exception as e:
            print(f"Błąd wyszukiwania wektorowego: {str(e)}")
            return ""

vector_service = VectorService()
