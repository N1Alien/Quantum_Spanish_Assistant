from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class AIService:
    def __init__(self):
        # Używamy ChatOllama do obsługi pełnej struktury rozmowy (chat history)
        self.llm = ChatOllama(
            model="llama3",
            base_url="http://localhost:11434"
        )

    def generate_spanish_response(self, chat_history_list: list, system_instruction: str, quantum_modifier: str, context: str) -> str:
        """
        Generuje odpowiedź Ollamy na podstawie PEŁNEJ historii czatu,
        wstrzykując instrukcję systemową oraz kontekst z bazy wektorowej.
        """
        # Dynamicznie modyfikujemy instrukcję o styl kwantowy
        full_instruction = system_instruction
        if quantum_modifier != "Normal":
            full_instruction += f"\n[Kwantowy modyfikator stylu: {quantum_modifier}]"
        
        if context:
            full_instruction += f"\n\n[DODATKOWA WIEDZA POMOCNICZA Z RAG]:\n{context}"

        # Budujemy listę obiektów wiadomości dla LangChaina
        formatted_messages = [SystemMessage(content=full_instruction)]
        
        # Przepisujemy historię, którą dostaliśmy z bazy/frontendu
        for msg in chat_history_list:
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_messages.append(AIMessage(content=msg["content"]))

        try:
            # Invoke wysyła pełną strukturę czatu (identycznie jak ollama.chat)
            response = self.llm.invoke(formatted_messages)
            return response.content
        except Exception as e:
            return f"Błąd komunikacji z lokalnym modelem AI: {str(e)}"

ai_service = AIService()
