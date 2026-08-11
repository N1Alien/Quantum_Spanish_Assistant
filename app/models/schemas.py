from pydantic import BaseModel, Field

class SpanishChatRequest(BaseModel):
    message: str = Field(..., example="Hola, buenas tardes", description="Wiadomość wpisana lub wypowiedziana przez użytkownika")
    system_instruction: str = Field(..., description="Główna, restrykcyjna instrukcja formatowania roli nauczyciela")

class SpanishChatResponse(BaseModel):
    quantum_style_applied: str = Field(..., description="Nazwa stylu wygenerowanego przez obwód kwantowy")
    response: str = Field(..., description="Pełna strukturyzowana odpowiedź z modelu Llama 3")
