import streamlit as st
from gtts import gTTS
import requests
import io
import os
import re

# Adres URL Twojego backendu FastAPI
FASTAPI_URL = os.getenv("FASTAPI_URL", "https://onrender.com")

# Generujemy automatycznie adres dla drugiego endpointu (transkrypcji)
TRANSCRIBE_URL = FASTAPI_URL.replace("/quantum-chat", "/transcribe")

st.set_page_config(page_title="Quantum Spanish Assistant", page_icon="⚛️", layout="centered")
st.title("⚛️ Hybrid Quantum Spanish Assistant")
st.write("Speak into the microphone. Audio processing is handled securely via FastAPI & Groq SDK.")

st.sidebar.caption(f"Chat API: {FASTAPI_URL}")
st.sidebar.caption(f"Audio API: {TRANSCRIBE_URL}")

# Prawidłowa regulacja mikrofonu jako filtr wielkości pakietu audio
mic_sensitivity = st.sidebar.slider(
    "Microphone sensitivity filter",
    min_value=1000,
    max_value=50000,
    value=3000,
    step=1000,
    help="Higher value = ignores shorter or quieter recordings. Lower value = catches everything."
)

SYSTEM_INSTRUCTION = (
    "Eres un profesor nativo de español. Tu única tarea es mantener una conversación fluida. "
    "ESTRUCTURA OBLIGATORIA DE CADA RESPUESTA (Usa exactamente estos marcadores):\n\n"
    "SPANISH:\n"
    "(Escribe aquí de 2 a 3 frases cortas en español. La última frase DEBE ser una pregunta directa para el usuario)\n"
    "-> EN: (Traduce aquí las frases anteriores al inglés)\n\n"
    "PROMPTS:\n"
    "(Escribe exactamente 10 opciones reales y muy cortas de 2-4 palabras en ESPAÑOL para que el usuario responda a tu pregunta)\n"
    "-> EN: (Traduce la opción 1 al inglés)\n"
    "(Siguiente opción en hispánico)\n"
    "-> EN: (Traduce la siguiente opción al inglés, hasta completar 10 pares)\n\n"
)


def normalize_prompt(text):
    clean = re.sub(r"^\d+[\.\)]\s*", "", text or "").strip()
    clean = re.sub(r"^[\-•*\s>]+", "", clean)
    clean = clean.replace("**", "").strip()
    return clean[:120].rstrip() + ("..." if len(clean) > 120 else "")


def parse_ai_prompts(assistant_text):
    if not assistant_text:
        return []

    match = re.search(r"PROMPTS:(.*)", assistant_text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []

    prompts_block = match.group(1).strip()
    lines = [line.strip() for line in prompts_block.split("\n") if line.strip()]
    
    dynamic_prompts = []
    current_es = None

    for line in lines:
        if line.upper().startswith("SPANISH:") or line.upper().startswith("PROMPTS:"):
            continue
            
        if line.startswith("-> EN:"):
            en_translation = line.replace("-> EN:", "").strip()
            if current_es:
                dynamic_prompts.append({"es": current_es, "en": en_translation})
                current_es = None
        else:
            if not re.match(r"^(?:en|english)\s*:", line, re.I):
                current_es = normalize_prompt(line)

    return dynamic_prompts[:10]


def build_dynamic_prompts(assistant_text=""):
    ai_prompts = parse_ai_prompts(assistant_text)
    if ai_prompts and len(ai_prompts) >= 2:
        return ai_prompts

    return [
        {"es": "¿Cómo estás?", "en": "How are you?"},
        {"es": "Hola, mucho gusto.", "en": "Hello, nice to meet you."},
        {"es": "Quiero aprender español.", "en": "I want to learn Spanish."},
        {"es": "Estoy listo para practicar.", "en": "I am ready to practice."},
        {"es": "Muchas gracias por tu ayuda.", "en": "Thank you very much for your help."},
        {"es": "Por favor, habla más despacio.", "en": "Please, speak more slowly."},
        {"es": "No entiendo bien.", "en": "I don't understand well."},
        {"es": "¿Qué significa esto?", "en": "What does this mean?"},
        {"es": "Perfecto, vamos a continuar.", "en": "Perfect, let's continue."},
        {"es": "Tengo una pregunta.", "en": "I have a question."}
    ]
def transcribe_audio_via_backend(audio_bytes):
    """Wysyła plik audio do Twojego własnego backendu FastAPI jako wieloczęściowy formularz file."""
    try:
        with st.spinner("🎙️ Transcribing voice via backend proxy..."):
            # Wysyłamy plik jako klasyczny formularz HTTP POST multipart/form-data
            files = {"file": ("audio.webm", audio_bytes, "audio/webm")}
            res = requests.post(TRANSCRIBE_URL, files=files, timeout=20)
            
            if res.status_code == 200:
                return res.json().get("text", "").strip()
            else:
                st.error(f"❌ Backend Transcription Error: {res.status_code} - {res.text}")
    except Exception as e:
        st.error(f"❌ Failed to connect to transcription server: {str(e)}")
    return ""


def send_user_message(user_text):
    if not user_text or not user_text.strip():
        return

    text = user_text.strip()
    if not st.session_state.chat_history_display or st.session_state.chat_history_display[-1].get("role") != "user" or st.session_state.chat_history_display[-1].get("content") != text:
        st.session_state.chat_history_display.append({"role": "user", "content": text})

    payload = {
        "message": text,
        "system_instruction": SYSTEM_INSTRUCTION,
        "chat_history": st.session_state.chat_history_display
    }

    bot_response = ""
    with st.spinner("🧠 Backend is processing the request (Quantum + RAG)..."):
        try:
            response = requests.post(FASTAPI_URL, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                bot_response = data["response"]
                q_style = data["quantum_style_applied"]

                if q_style != "Normal":
                    st.toast(f"⚛️ Quantum effect: {q_style}", icon="⚛️")

                st.session_state.chat_history_display.append({"role": "assistant", "content": bot_response})
            else:
                st.error(f"❌ Backend error: {response.status_code}. {response.text}")
        except Exception as api_err:
            st.error(f"❌ Failed to communicate with FastAPI. Details: {str(api_err)}")

    if bot_response:
        spanish_block = ""
        match = re.search(r"SPANISH:(.*?)(PROMPTS:|$)", bot_response, re.DOTALL | re.IGNORECASE)
        if match:
            spanish_block = match.group(1).strip()
        else:
            spanish_block = bot_response

        lines = spanish_block.split("\n")
        clean_spanish_lines = []
        for line in lines:
            line_strip = line.strip()
            if line_strip and not line_strip.startswith("-> EN:") and not line_strip.startswith("("):
                clean_spanish_lines.append(line_strip)

        clean_audio_text = " ".join(clean_spanish_lines)
        if clean_audio_text:
            try:
                tts = gTTS(text=clean_audio_text, lang='es')
                tts.save("/tmp/web_response.mp3")
                st.session_state.play_audio = True
            except Exception as tts_err:
                st.error(f"⚠️ Audio generation failed: {str(tts_err)}")


if "chat_history_display" not in st.session_state:
    st.session_state.chat_history_display = []

if "play_audio" not in st.session_state:
    st.session_state.play_audio = False

st.subheader("🎛️ Microphone and Conversation")

if st.button("🔄 Reset conversation"):
    if os.path.exists("/tmp/web_response.mp3"):
        os.remove("/tmp/web_response.mp3")
    st.session_state.clear()
    st.rerun()

# Aktywne nagrywanie głosu
audio_file = st.audio_input("Click the microphone icon to start speaking in Spanish", key="microphone_input")

if audio_file is not None:
    audio_bytes = audio_file.read()
    
    # Warunek czułości (rozmiaru pliku)
    if len(audio_bytes) > mic_sensitivity:
        user_text = transcribe_audio_via_backend(audio_bytes)
        
        if user_text and ("last_processed" not in st.session_state or st.session_state.last_processed != user_text):
            st.session_state.last_processed = user_text
            send_user_message(user_text)
            st.rerun()
    else:
        st.warning("⚠️ Audio recording too quiet or too short. Adjust the sensitivity filter if needed.")

# Wyświetlanie kompletnego zestawu 10 podpowiedzi
latest_assistant = ""
for msg in reversed(st.session_state.chat_history_display):
    if msg["role"] == "assistant":
        latest_assistant = msg["content"]
        break

st.session_state.current_prompts = build_dynamic_prompts(latest_assistant)

with st.sidebar:
    st.header("💡 Suggested responses")
    # Pętla generuje pełne 10 podpowiedzi z bazy AI
    for idx, prompt in enumerate(st.session_state.current_prompts[:10], start=1):
        if st.button(f"{idx}. {prompt['es']} — {prompt['en']}", key=f"suggestion_{idx}", use_container_width=True):
            send_user_message(prompt["es"])
            st.rerun()

# Okno konwersacji chatu
for msg in reversed(st.session_state.chat_history_display):
    if msg["role"] == "user":
        st.info(f"**You:** {msg['content']}")
    elif msg["role"] == "assistant":
        content = msg["content"]
        spanish_match = re.search(r"SPANISH:(.*?)(PROMPTS:|$)", content, re.DOTALL | re.IGNORECASE)
        
        with st.chat_message("assistant"):
            if spanish_match:
                st.markdown("🗣️ *Conversation:*")
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

if os.path.exists("/tmp/web_response.mp3") and st.session_state.get("play_audio", False):
    st.audio("/tmp/web_response.mp3", format="audio/mp3", autoplay=True)
    st.session_state.play_audio = False
