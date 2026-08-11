import os
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

class VectorService:
    def __init__(self):
        # Inicjalizacja modelu osadzeń wektorowych na Twoim RTX 5080
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        # Lokalne ścieżki przechowywania danych wektorowych
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.persist_directory = os.path.join(self.base_dir, "chroma_db")
        
        # ŹRÓDŁA DANYCH: Bot sam pobierze wiedzę z tych stron przy starcie!
        # Możesz tu dopisać dowolne darmowe strony z gramatyką lub słownictwem.
        self.urls_to_scrape = [
            "https://wikipedia.org",
            "https://wikipedia.org"
        ]

    def auto_fetch_web_knowledge(self):
        """
        Automatycznie pobiera dane ze stron www, tnie na fragmenty 
        i zapisuje bezpośrednio w bazie ChromaDB.
        """
        print("🌐 [Web Ingestion] Rozpoczynam automatyczne pobieranie wiedzy z internetu...")
        
        try:
            # 1. Scrapowanie stron www w locie przy użyciu LangChain
            loader = WebBaseLoader(self.urls_to_scrape)
            documents = loader.load()
            print(f"📥 Pomyślnie pobrano {len(documents)} źródła internetowe.")

            # 2. Fragmentacja pobranego tekstu HTML
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=700, 
                chunk_overlap=100
            )
            chunks = text_splitter.split_documents(documents)

            # 3. Wstrzyknięcie i zapis wektorów do bazy ChromaDB
            Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"🚀 [RAG Sukces] Baza wiedzy zasilona automatycznie ({len(chunks)} fragmentów wektorowych)!")
            
        except Exception as e:
            print(f"⚠️ Nie udało się automatycznie pobrać danych www: {str(e)}")

    def get_relevant_context(self, query: str, k: int = 2) -> str:
        """Przeszukuje bazę wektorową i wyciąga kontekst internetowy pasujący do zapytania."""
        try:
            if not os.path.exists(self.persist_directory):
                return ""

            vector_db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            docs = vector_db.similarity_search(query, k=k)
            return "\n---\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"Błąd wyszukiwania wektorowego: {str(e)}")
            return ""

vector_service = VectorService()
