from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import SpanishChatRequest, SpanishChatResponse
from app.services.quantum_service import quantum_service
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.core.database import get_db  # NOWE
from app.models.chat_history import QuantumChatHistory  # NOWE

router = APIRouter()

@router.post("/quantum-chat", response_model=SpanishChatResponse, tags=["Quantum Language Core"])
def process_quantum_chat(payload: SpanishChatRequest, db: Session = Depends(get_db)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Tekst użytkownika nie może być pusty.")

    # 1. Obliczenia kwantowe modyfikujące styl wypowiedzi AI
    quantum_modifier = quantum_service.get_quantum_style_modifier(payload.message)
    
    # 2. Automatyczne przeszukiwanie wiedzy pobranej z internetu
    context = vector_service.get_relevant_context(payload.message, k=2)
    
    # 3. Generowanie lekcji za pomocą Llama 3
    ai_response = ai_service.generate_spanish_response(
        user_message=payload.message,
        system_instruction=payload.system_instruction,
        quantum_modifier=quantum_modifier,
        context=context
    )
    
    # 4. NOWE: Trwały zapis do bazy danych PostgreSQL
    try:
        history_record = QuantumChatHistory(
            user_message=payload.message,
            quantum_style=quantum_modifier,
            ai_response=ai_response
        )
        db.add(history_record)
        db.commit()
    except Exception as e:
        print(f"Błąd zapisu transakcji w bazie danych: {str(e)}")
        # Cichy błąd, aby użytkownik i tak dostał lekcję, nawet przy awarii zapisu
    
    return SpanishChatResponse(
        quantum_style_applied=quantum_modifier,
        response=ai_response
    )
