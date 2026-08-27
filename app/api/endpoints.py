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

    # 1. Budujemy czystą, bezpieczną strukturę wiadomości dla oficjalnego SDK
    messages = [
        {"role": "system", "content": payload.system_instruction},
        {"role": "user", "content": payload.message.strip()}
    ]

    try:
        # 2. Inicjalizacja oficjalnego klienta Groq SDK
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # 3. Wywołanie potoku za pomocą oficjalnego i stabilnego modelu Llama 3
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.7
        )
        
        ai_response = completion.choices[0].message.content.strip()
        
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=ai_response
        )
        
    except Exception as e:
        # Awaryjny fallback struktury tekstowej zgodny z parserem frontendu (w razie awarii chmury)
        fallback_text = (
            "SPANISH:\n¡Hola! Lo siento, hubo un problema técnico. ¿Podemos continuar la conversación?\n"
            "-> EN: Hello! I'm sorry, there was a technical problem. Can we continue the conversation?\n\n"
            "PROMPTS:\nSí, claro.\n-> EN: Yes, of course.\n¿Qué pasó?\n-> EN: What happened?"
        )
        print(f"⚠️ [Groq Exception] Details: {str(e)}")
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=fallback_text
        )
