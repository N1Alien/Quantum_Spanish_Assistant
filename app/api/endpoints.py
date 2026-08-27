from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import requests
import os

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
    
    # Pobieramy klucz Gemini bezpośrednio ze środowiska Rendera
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response="SPANISH:\nError: GEMINI_API_KEY no está configurado en Render.\n-> EN: Error: GEMINI_API_KEY is not configured on Render.\n\nPROMPTS:\nConfigurar clave\n-> EN: Configure key"
        )

    # Rekonstrukcja historii dla formatu Google Gemini API
    # Gemini wymaga struktury: {"role": "user"|"model", "parts": [{"text": "..."}]}
    contents = []
    for msg in payload.chat_history:
        role = "model" if msg.get("role") == "assistant" else "user"
        content = msg.get("content", "").strip()
        if content and "❌" not in content and "Backend error" not in content and "problem técnico" not in content:
            contents.append({
                "role": role,
                "parts": [{"text": content}]
            })

    # Dodajemy aktualną instrukcję systemową bezpośrednio na początek kontekstu chatu
    contents.insert(0, {
        "role": "user",
        "parts": [{"text": f"[SYSTEM INSTRUCTION - ACT AS THIS PROFILE]:\n{payload.system_instruction}"}]
    })

    # Oficjalny endpoint Google Gemini 2.5 Flash
    url = f"https://googleapis.com{gemini_key}"
    headers = {"Content-Type": "application/json"}
    payload_data = {"contents": contents}

    try:
        response = requests.post(url, headers=headers, json=payload_data, timeout=20)
        if response.status_code == 200:
            # Wyciągamy wygenerowany tekst z oficjalnej struktury JSON Google Gemini
            ai_response = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            return SpanishChatResponse(
                quantum_style_applied="Normal",
                response=ai_response
            )
        else:
            return SpanishChatResponse(
                quantum_style_applied="Normal",
                response=f"SPANISH:\nError de API Gemini ({response.status_code}): {response.text}\n-> EN: Gemini API Error.\n\nPROMPTS:\nIntentar de nuevo\n-> EN: Try again"
            )
    except Exception as e:
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=f"SPANISH:\nError de conexión Gemini: {str(e)}.\n-> EN: Gemini Connection error.\n\nPROMPTS:\nIntentar de nuevo\n-> EN: Try again"
        )
