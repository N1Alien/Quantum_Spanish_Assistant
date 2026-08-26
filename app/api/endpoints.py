from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import SpanishChatRequest, SpanishChatResponse
from app.services.quantum_service import quantum_service
from app.services.ai_service import ai_service
from app.core.database import get_db
from app.models.chat_history import QuantumChatHistory

router = APIRouter()

@router.post("/quantum-chat", response_model=SpanishChatResponse, tags=["Quantum Language Core"])
def process_quantum_chat(payload: SpanishChatRequest, db: Session = Depends(get_db)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Tekst użytkownika nie może być pusty.")

    # 1. Obliczenia kwantowe (Styl)
    quantum_modifier = quantum_service.get_quantum_style_modifier(payload.message)
    
    # 2. RAG wyłączony w produkcji chmurowej z powodu blokad sieciowych Rendera
    context = ""
    
    # 3. Generujemy odpowiedź AI - JEŚLI BAZA DANYCH SIĘ WYWALI, TO I TAK ZADZIAŁA
    ai_response = ai_service.generate_spanish_response(
        chat_history_list=payload.chat_history,
        system_instruction=payload.system_instruction,
        quantum_modifier=quantum_modifier,
        context=context
    )
    
    # 4. Trwały zapis transakcji z pełnym cofnięciem transakcji w przypadku błędu (Rollback)
    # Dzięki temu awaria bazy danych Neon.tech NIE zablokuje i NIE wyłączy dostępu do sztucznej inteligencji
    try:
        history_record = QuantumChatHistory(
            user_message=payload.message,
            quantum_style=quantum_modifier,
            ai_response=ai_response
        )
        db.add(history_record)
        db.commit()
    except Exception as db_error:
        # W przypadku błędu bazy danych chmurowej kategorycznie cofamy transakcję,
        # oczyszczając sesję, aby aplikacja mogła bez przeszkód działać dalej
        db.rollback()
        print(f"⚠️ [Database Warning] Zapis historii pominięty: {str(db_error)}")
    
    return SpanishChatResponse(
        quantum_style_applied=quantum_modifier,
        response=ai_response
    )
