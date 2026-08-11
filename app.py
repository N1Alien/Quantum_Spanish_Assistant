import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import requests
import io
import os
import re

# Definiujemy punkt końcowy naszego działającego obok backendu FastAPI
FASTAPI_URL = "http://127.0.0.1:8000/api/v1/quantum-chat"

# Konfiguracja strony w przeglądarce Opera / Chrome
st.set_page_config(page_title="Quantum Spanish Assistant", page_icon="⚛️", layout="centered")
st.title("⚛️ Hybrydowy Kwantowy Asystent Hiszpańskiego")
st.write("Mów do mikrofonu. Interfejs przesyła dane do produkcyjnego API FastAPI.")

# 1. GŁÓWNA INSTRUKCJA SYSTEMOWA DLA NAUCZYCIELA HISZPAŃSKIEGO
SYSTEM_INSTRUCTION = (
    "Eres un profesor nativo de español. Tu única tarea es mantener una conversación fluida. "
    "ESTRUCTURA OBLIGATORIA DE CADA RESPUESTA (Usa exactamente estos marcadores):\n\n"
    "SPANISH:\n"
    "(Escribe aquí de 2 a 3 frases cortas en español. La última frase DEBE ser una pregunta directa para el usuario)\n"
    "-> EN: (Traduce aquí las frases anteriores al inglés)\n\n"
    "PROMPTS:\n"
    "(Escribe exactamente 10 opciones reales y muy cortas de 2-4 palabras en ESPAÑOL para que el usuario responda a tu pregunta)\n"
    "-> EN: (Traduce la opción 1 al inglés)\n"
    "(Siguiente opción en español)\n"
    "-> EN: (Traduce la siguiente opção na angielski, i tak do uzupełnienia 10 par)\n\n"
)

# Inicjalizacja stanów pamięci podręcznej wyświetlania
if "chat_history_display" not in st.session_state:
    st.session_state.chat_history_display = []

if "current_prompts" not in st.session_state:
    st.session_state.current_prompts = "Rozpocznij rozmowę..."

if "play_audio" not in st.session_state:
    st.session_state.play_audio = False

# 2. INTERFEJS UŻYTKOWNIKA: PANEL STEROWANIA
st.subheader("🎛️ Konfiguracja i nagrywanie")

if st.button("🔄 Resetuj widok rozmowy"):
    if os.path.exists("web_response.mp3"):
        os.remove("web_response.mp3")
    st.session_state.clear()
    st.rerun()

# Nowoczesny element Streamlit zbierający dźwięk bezpośrednio w przeglądarce
audio_file = st.audio_input("Kliknij ikonę mikrofonu, aby zacząć mówić po hiszpańsku", key="microphone_input")

if audio_file is not None:
    audio_bytes = audio_file.read()
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 150
    
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio_data = recognizer.record(source)
        
    try:
        # Zamiana mowy na tekst (Google STT)
        user_text = recognizer.recognize_google(audio_data, language="es-ES")
        
        # Zapobiegamy podwójnemu wysyłaniu tego samego żądania przy odświeżaniu strony
        if "last_processed" not in st.session_state or st.session_state.last_processed != user_text:
            st.session_state.last_processed = user_text
            
            # Przygotowujemy strukturę żądania sieciowego (Payload)
            payload = {
                "message": user_text,
                "system_instruction": SYSTEM_INSTRUCTION
            }
            
            with st.spinner("🧠 Backend przetwarza dane (Kwanty + RAG + Postgres)..."):
                # --- STRZAŁ HTTP DO BACKENDU FASTAPI ---
                response = requests.post(FASTAPI_URL, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    bot_response = data["response"]
                    q_style = data["quantum_style_applied"]
                    
                    # Pokazujemy użytkownikowi, jaki styl wyliczyły kubity na backendzie
                    if q_style != "Normal":
                        st.toast(f"⚛️ Efekt kwantowy: {q_style}", icon="⚛️")
                    
                    # Dodajemy do lokalnej pamięci wyświetlania
                    st.session_state.chat_history_display.append({"role": "user", "content": user_text})
                    st.session_state.chat_history_display.append({"role": "assistant", "content": bot_response})
                else:
                    st.error("Błąd połączenia z produkcyjnym backendem FastAPI.")
                    bot_response = ""
            
            # --- GENEROWANIE I FILTROWANIE AUDIO ---
            if bot_response:
                spanish_block = ""
                match = re.search(r"SPANISH:(.*?)(PROMPTS:|$)", bot_response, re.DOTALL | re.IGNORECASE)
                if match:
                    spanish_block = match.group(1).strip()
                else:
                    spanish_block = bot_response
                    
                # Wyciągamy czysty tekst hiszpański (usuwamy linie tłumaczeń -> EN:)
                lines = spanish_block.split("\n")
                clean_spanish_lines = []
                for line in lines:
                    line_strip = line.strip()
                    if line_strip and not line_strip.startswith("-> EN:") and not line_strip.startswith("("):
                        clean_spanish_lines.append(line_strip)
                        
                clean_audio_text = " ".join(clean_spanish_lines)
                if clean_audio_text:
                    tts = gTTS(text=clean_audio_text, lang='es')
                    tts.save("web_response.mp3")
                    st.session_state.play_audio = True
                    st.rerun()
                    
    except Exception as e:
        st.error(f"🔕 Problem z dekodowaniem mowy: {e}")

# 3. PARSER PODPOWIEDZI (PANEL BOCZNY)
for msg in reversed(st.session_state.chat_history_display):
    if msg["role"] == "assistant":
        content = msg["content"]
        prompts_match = re.search(r"PROMPTS:(.*)", content, re.DOTALL | re.IGNORECASE)
        if prompts_match:
            st.session_state.current_prompts = prompts_match.group(1).strip()
        break

with st.sidebar:
    st.header("💡 Respuestas sugeridas")
    formatted_prompts = []
    
    for line in st.session_state.current_prompts.split("\n"):
        line_strip = line.strip()
        if not line_strip:
            continue
            
        if line_strip.startswith("-> EN:") or "-> en:" in line_strip.lower():
            clean_en = line_strip.replace("-> EN:", "").replace("-> en:", "").strip()
            formatted_prompts.append(f"-> EN: :orange[*{clean_en}*]\n\n---")
        else:
            clean_es = re.sub(r"^\d+[\.\)]\s*", "", line_strip).strip()
            clean_es = clean_es.lstrip("- ").strip()
            if clean_es and not any(kw in clean_es.lower() for kw in ["generate", "option", "prompt", "real", "vocabulary"]):
                formatted_prompts.append(f"**{clean_es}**")
                
    st.markdown("\n\n".join(formatted_prompts))

# 4. RENDEROWANIE OKNA ROZMOWY
for msg in reversed(st.session_state.chat_history_display):
    if msg["role"] == "user":
        st.info(f"**Ty:** {msg['content']}")
    elif msg["role"] == "assistant":
        content = msg["content"]
        spanish_match = re.search(r"SPANISH:(.*?)(PROMPTS:|$)", content, re.DOTALL | re.IGNORECASE)
        
        with st.chat_message("assistant"):
            if spanish_match:
                st.markdown("🗣️ **Conversación:**")
                raw_text = spanish_match.group(1).strip()
                formatted_lines = []
                for line in raw_text.split("\n"):
                    line_strip = line.strip()
                    if line_strip.startswith("-> EN:"):
                        clean_en = line_strip.replace("-> EN:", "").strip()
                        formatted_lines.append(f":orange[{clean_en}]")
                    elif line_strip:
                        formatted_lines.append(f"{line_strip}")
                st.markdown("\n\n".join(formatted_lines))
            else:
                formatted_lines = []
                for line in content.split("\n"):
                    line_strip = line.strip()
                    if any(m in line_strip.upper() for m in ["PROMPTS", "SPANISH", "VOCABULARY"]):
                        continue
                    if line_strip.startswith("-> EN:"):
                        clean_en = line_strip.replace("-> EN:", "").strip()
                        formatted_lines.append(f":orange[{clean_en}]")
                    elif line_strip:
                        formatted_lines.append(f"{line_strip}")
                st.markdown("\n\n".join(formatted_lines))

# Automatyczne odtwarzanie wygenerowanego głosu nauczyciela
if os.path.exists("web_response.mp3") and st.session_state.get("play_audio", False):
    st.audio("web_response.mp3", format="audio/mp3", autoplay=True)
    st.session_state.play_audio = False
