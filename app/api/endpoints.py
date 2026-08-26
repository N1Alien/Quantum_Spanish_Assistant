from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import requests
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

    # Rekonstrukcja wiadomości dla chatu
    messages = [{"role": "system", "content": payload.system_instruction}]
    for msg in payload.chat_history:
        role = "assistant" if msg.get("role") == "assistant" else "user"
        content = msg.get("content", "").strip()
        if content and "❌" not in content and "Backend error" not in content:
            messages.append({"role": role, "content": content})

    # Bezpośrednie żądanie HTTP POST z wymuszonym modelem produkcyjnym Llama 3.1
    url = "https://groq.com"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",  # Wymuszona prawidłowa nazwa modelu
        "messages": messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code == 200:
            ai_response = response.json()["choices"]["message"]["content"]
            return SpanishChatResponse(
                quantum_style_applied="Normal",
                response=ai_response
            )
        else:
            # Rejestrujemy błąd w strukturze, aby użytkownik widział poprawną instrukcję
            return SpanishChatResponse(
                quantum_style_applied="Normal",
                response=f"SPANISH:\nHubo un problema con la respuesta de AI. Por favor, intenta de nuevo.\n-> EN: There was a problem with the AI response. Please try again.\n\nPROMPTS:\nIntentar de nuevo\n-> EN: Try again"
            )
    except Exception as e:
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=f"SPANISH:\nError de conexión: {str(e)}.\n-> EN: Connection error.\n\nPROMPTS:\nIntentar de nuevo\n-> EN: Try again"
        )
