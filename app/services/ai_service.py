from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.core.config import settings


class AIService:
    def __init__(self):
        provider = (settings.LLM_PROVIDER or "ollama").lower()
        self.llm = None

        if provider == "groq":
            try:
                from langchain_groq import ChatGroq
            except ImportError as exc:  # pragma: no cover - runtime dependency guard
                raise RuntimeError("langchain_groq is required when LLM_PROVIDER=groq") from exc

            self.llm = ChatGroq(
                model=settings.GROQ_MODEL,
                api_key=settings.GROQ_API_KEY,
            )
            return

        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover - runtime dependency guard
            raise RuntimeError("langchain_ollama is required when LLM_PROVIDER=ollama") from exc

        self.llm = ChatOllama(
            model=settings.LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

    def generate_spanish_response(self, chat_history_list: list, system_instruction: str, quantum_modifier: str, context: str) -> str:
        if self.llm is None:
            return "Błąd konfiguracji modelu AI. Sprawdź zmienne środowiskowe LLM_PROVIDER i klucz API."

        full_instruction = system_instruction
        if quantum_modifier != "Normal":
            full_instruction += f"\n[Kwantowy modyfikator stylu: {quantum_modifier}]"

        if context:
            full_instruction += f"\n\n[DODATKOWA WIEDZA POMOCNICZA Z RAG]:\n{context}"

        formatted_messages = [SystemMessage(content=full_instruction)]

        for msg in chat_history_list:
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_messages.append(AIMessage(content=msg["content"]))

        try:
            response = self.llm.invoke(formatted_messages)
            return response.content
        except Exception as e:
            provider_name = (settings.LLM_PROVIDER or "ollama").upper()
            return f"Błąd komunikacji z modelem AI ({provider_name}): {str(e)}"


ai_service = AIService()
