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

    # Budujemy czystą strukturę wiadomości
    messages = [
        {"role": "system", "content": payload.system_instruction},
        {"role": "user", "content": payload.message.strip()}
    ]

    try:
        # Inicjalizacja klienta Groq SDK
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # POPRAWKA ARCHITEKTONICZNA: Używamy jedynej, w 100% aktywnej i flagowej nazwy modelu w API Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        
        ai_response = completion.choices.message.content.strip()
        
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=ai_response
        )
        
    except Exception as e:
        error_details = str(e)
        fallback_text = (
            f"SPANISH:\nHubo un problema técnico con Groq API. Detalles del error: {error_details}\n"
            f"-> EN: Technical problem with Groq API. Error details: {error_details}\n\n"
            f"PROMPTS:\nIntentar de nuevo\n-> EN: Try again"
        )
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=fallback_text
        )
