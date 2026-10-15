from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from groq import Groq, RateLimitError
import logging
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

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

    groq_key = settings.GROQ_API_KEY.strip()
    if not groq_key:
        raise HTTPException(status_code=503, detail="AI chat is not configured: GROQ_API_KEY is missing.")

    try:
        messages = [{"role": "system", "content": payload.system_instruction}]
        history = payload.chat_history
        # The frontend includes the current user message in its history; send it once.
        if history and history[-1].get("role") == "user" and history[-1].get("content", "").strip() == payload.message.strip():
            history = history[:-1]
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "").strip()
            if role in {"user", "assistant"} and content and "❌" not in content and "Backend error" not in content and "problem técnico" not in content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": payload.message.strip()})

        with Groq(api_key=groq_key) as client:
            completion = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
            )
        answer = completion.choices[0].message.content or ""
        if not answer.strip():
            raise HTTPException(status_code=502, detail="The AI returned an empty response. Please try again.")
        return SpanishChatResponse(
            quantum_style_applied="Normal",
            response=answer.strip()
        )
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail="The AI service is busy or its request limit was reached. Please wait briefly and try again.") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Groq chat request failed (model=%s)", settings.GROQ_MODEL)
        raise HTTPException(status_code=502, detail="The AI chat request failed. Please try again shortly.") from e
