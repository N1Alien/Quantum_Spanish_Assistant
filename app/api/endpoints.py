from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from groq import Groq
from app.core.config import settings

router = APIRouter()

class SpanishChatRequest(BaseModel):
    message: str = Field(..., description="Ostatnia wiadomość użytkownika")
    system_instruction: str = Field(..., description="Główna instrukcja systemowa")
    chat_history: List[Dict[str, str]] = Field(..., description="Pełna historia rozmowy")

class SpanishChatResponse(BaseModel):
    quantum_style_applied: str
    response: str

@router.post("/quantum-chat", response_model=SpanishChatResponse, tags=["Quantum Language Core"])
def process_quantum_chat(payload: SpanishChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Tekst użytkownika nie może być pusty.")
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Brakuje klucza GROQ_API_KEY na backendzie.")

    try:
        # Rekonstrukcja wiadomości bezpośrednio dla natywnego API Groq
        messages = [{"role": "system", "content": payload.system_instruction}]
        
        for msg in payload.chat_history:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            content = msg.get("content", "").strip()
            if content and "❌" not in content and "Backend error" not in content:
                messages.append({"role": role, "content": content})

        # Oficjalne wywołanie SDK Groq - omija problemy z paczkami LangChain
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.7
        )
        
        ai_response = completion.choices[0].message.content
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=ai_response
        )
    except Exception as e:
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=f"❌ Błąd Groq API: {str(e)}"
        )
