from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import google.generativeai as genai
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

    try:
        genai.configure(api_key=gemini_key.strip())
        
        history_contents = []
        for msg in payload.chat_history:
            role = "model" if msg.get("role") == "assistant" else "user"
            content = msg.get("content", "").strip()
            if content and "❌" not in content and "Backend error" not in content and "problem técnico" not in content:
                history_contents.append({
                    "role": role,
                    "parts": [content]
                })

        # POPRAWKA: Przejście na aktualny model dla generowania tekstu chatu
        model = genai.GenerativeModel(
            model_name="gemini-3.6-flash",
            system_instruction=payload.system_instruction
        )
        
        chat = model.start_chat(history=history_contents)
        response = chat.send_message(payload.message.strip())
        
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=response.text.strip()
        )
    except Exception as e:
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=f"SPANISH:\nError de SDK Gemini: {str(e)}.\n-> EN: Gemini SDK error."
        )
