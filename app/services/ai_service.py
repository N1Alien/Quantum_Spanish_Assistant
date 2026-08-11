from langchain_ollama import OllamaLLM
from app.core.config import settings

class AIService:
    def __init__(self):
        self.llm = OllamaLLM(
            model=settings.LLM_MODEL,
            base_url="http://localhost:11434"
        )

    def generate_spanish_response(self, user_message: str, system_instruction: str, quantum_modifier: str, context: str) -> str:
        """Generuje ustrukturyzowaną odpowiedź, wzbogaconą o styl kwantowy oraz wiedzę z RAG."""
        full_instruction = system_instruction
        if quantum_modifier != "Normal":
            full_instruction += f"\n[MODYFIKATOR STYLU AI: {quantum_modifier}]"

        # Dodajemy sekcję kontekstu z bazy wektorowej do promptu głównego
        full_prompt = f"""
{full_instruction}

DODATKOWA WIEDZA POMOCNICZA Z WGRANYCH PODRĘCZNIKÓW (Użyj, jeśli pasuje do kontekstu lekcji):
{context}

Wypowiedź użytkownika do przetworzenia: {user_message}
(Pamiętaj o zachowaniu znaczników SPANISH: oraz PROMPTS: wraz z tłumaczeniami -> EN:)
ODPOWIEDŹ:"""

        try:
            return self.llm.invoke(full_prompt)
        except Exception as e:
            return f"Błąd komunikacji z lokalnym modelem AI: {str(e)}"

ai_service = AIService()
