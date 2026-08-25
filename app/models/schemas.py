from pydantic import BaseModel, Field
from typing import List, Dict

class SpanishChatRequest(BaseModel):
    message: str = Field(..., description="Ostatnia wiadomość użytkownika")
    system_instruction: str = Field(..., description="Główna instrukcja systemowa")
    chat_history: List[Dict[str, str]] = Field(..., description="Pełna historia rozmowy z session_state")

class SpanishChatResponse(BaseModel):
    quantum_style_applied: str
    response: str
