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
    
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response="SPANISH:\nError: GEMINI_API_KEY no está configurado.\n-> EN: Error: GEMINI_API_KEY is missing."
        )

    contents = []
    for msg in payload.chat_history:
        role = "model" if msg.get("role") == "assistant" else "user"
        content = msg.get("content", "").strip()
        if content and "❌" not in content and "Backend error" not in content and "problem técnico" not in content:
            contents.append({"role": role, "parts": [{"text": content}]})

    contents.insert(0, {
        "role": "user",
        "parts": [{"text": f"[SYSTEM INSTRUCTION - ACT AS THIS PROFILE]:\n{payload.system_instruction}"}]
    })

    # POPRAWKA: Czysty URL bez wstrzykiwania f-stringa
    url = "https://googleapis.com"
    
    query_params = {"key": gemini_key}
    headers = {"Content-Type": "application/json"}
    payload_data = {"contents": contents}

    try:
        response = requests.post(url, headers=headers, json=payload_data, params=query_params, timeout=20)
        if response.status_code == 200:
            ai_response = response.json()["candidates"]["content"]["parts"]["text"].strip()
            return SpanishChatResponse(quantum_style_applied="Normal", response=ai_response)
        else:
            return SpanishChatResponse(
                quantum_style_applied="Normal",
                response=f"SPANISH:\nError Gemini ({response.status_code}): {response.text}\n-> EN: Gemini API Error."
            )
    except Exception as e:
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=f"SPANISH:\nError de conexión: {str(e)}.\n-> EN: Connection error."
        )
