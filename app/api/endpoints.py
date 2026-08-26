from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import SpanishChatRequest, SpanishChatResponse
from app.services.quantum_service import quantum_service
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.core.database import get_db
from app.models.chat_history import QuantumChatHistory

router = APIRouter()

@router.post("/quantum-chat", response_model=SpanishChatResponse, tags=["Quantum Language Core"])
def process_quantum_chat(payload: SpanishChatRequest, db: Session = Depends(get_db)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Tekst użytkownika nie może być pusty.")

    # 1. Obliczenia kwantowe (Styl) - DZIAŁA W 100% W CHMURZE
    quantum_modifier = quantum_service.get_quantum_style_modifier(payload.message)
    
    # 2. Bezpieczny RAG chmurowy: Pomijamy sieć HuggingFace w produkcji, aby uniknąć blokad Rendera
    context = "" 
    # (Opcjonalnie lokalnie czytałby z vector_service, w chmurze dajemy pusty string)
    
    # 3. Generujemy odpowiedź, karmiąc bota pełną historią rozmowy - PRZEZ OFICJALNE API GROQ
    ai_response = ai_service.generate_spanish_response(
        chat_history_list=payload.chat_history,
        system_instruction=payload.system_instruction,
        quantum_modifier=quantum_modifier,
        context=context
    )
    
    # 4. Trwały zapis transakcji w bazie danych Neon.tech (Przez SSL)
    try:
        history_record = QuantumChatHistory(
            user_message=payload.message,
            quantum_style=quantum_modifier,
            ai_response=ai_response
        )
        db.add(history_record)
        db.commit()
    except Exception as e:
        print(f"Błąd zapisu historii: {str(e)}")
    
    return SpanishChatResponse(
        quantum_style_applied=quantum_modifier,
        response=ai_response
    )
