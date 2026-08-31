import streamlit as st
from gtts import gTTS
import requests
import io
import os
import re

BACKEND_BASE = os.getenv("FASTAPI_URL", "http://127.0.0.1:8001").rstrip("/")
FASTAPI_CHAT_URL = f"{BACKEND_BASE}/api/v1/quantum-chat"
FASTAPI_TRANSCRIBE_URL = f"{BACKEND_BASE}/api/v1/transcribe"

st.set_page_config(page_title="Quantum Spanish Assistant", page_icon="⚛️", layout="centered")
st.title("⚛️ Hybrid Quantum Spanish Assistant")
st.write("Record your voice using the native recorder below to practice Spanish.")

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
        {"es": "Hola, mucho gusto.", "en": "Hello, nice to meet you."},
        {"es": "¿Cómo estás?", "en": "How are you?"},
        {"es": "Quiero aprender español.", "en": "I want to learn Spanish."},
        {"es": "Estoy listo para practicar.", "en": "I am ready to practice."},
        {"es": "Muchas gracias por tu ayuda.", "en": "Thank you very much for your help."},
        {"es": "Por favor, habla más despacio.", "en": "Please, speak more slowly."},
        {"es": "No entiendo bien.", "en": "I don't understand well."},
        {"es": "¿Qué significa esto?", "en": "What does this mean?"},
        {"es": "Perfecto, vamos a continuar.", "en": "Perfect, let's continue."},
        {"es": "Tengo una pregunta.", "en": "I have a question."}
    ]

def send_user_message(user_text):
    if not user_text or not user_text.strip():
        return
    text = user_text.strip()
    st.session_state.chat_history_display.append({"role": "user", "content": text})
    
    sanitized_history = []
    for msg in st.session_state.chat_history_display:
        if msg.get("content") and "❌" not in msg.get("content"):
            sanitized_history.append({"role": msg["role"], "content": msg["content"]})

    payload = {"message": text, "system_instruction": SYSTEM_INSTRUCTION, "chat_history": sanitized_history}
    bot_response = ""
    with st.spinner("🧠 AI is processing your request..."):
        try:
            response = requests.post(FASTAPI_CHAT_URL, json=payload, timeout=30)
            if response.status_code == 200:
                bot_response = response.json().get("response", "").strip()
                if bot_response:
                    st.session_state.chat_history_display.append({"role": "assistant", "content": bot_response})
            else:
                st.error(f"❌ Backend error: {response.text}")
        except Exception as api_err:
            st.error(f"❌ Connection failed: {str(api_err)}")

    if bot_response and "❌" not in bot_response:
        spanish_block = ""
        match = re.search(r"SPANISH:(.*?)(PROMPTS:|$)", bot_response, re.DOTALL | re.IGNORECASE)
        spanish_block = match.group(1).strip() if match else bot_response
        clean_lines = [l.strip() for l in spanish_block.split("\n") if l.strip() and not l.strip().startswith("-> EN:")]
        clean_audio_text = " ".join(clean_lines)
        if clean_audio_text:
            try:
                tts = gTTS(text=clean_audio_text, lang='es')
                tts.save("/tmp/web_response.mp3")
                st.session_state.play_audio = True
            except Exception:
                pass

if "chat_history_display" not in st.session_state:
    st.session_state.chat_history_display = []
if "play_audio" not in st.session_state:
    st.session_state.play_audio = False
if "last_audio_signature" not in st.session_state:
    st.session_state.last_audio_signature = None

if st.button("🔄 Reset conversation"):
    if os.path.exists("/tmp/web_response.mp3"):
        os.remove("/tmp/web_response.mp3")
    st.session_state.clear()
    st.rerun()

# Oryginalny widok nagrywania Streamlit
audio_file = st.audio_input("Record a voice message")

if audio_file is not None:
    audio_bytes = audio_file.getvalue()
    current_signature = hash(audio_bytes)
    if current_signature != st.session_state.last_audio_signature:
        st.session_state.last_audio_signature = current_signature
        with st.spinner("🎙️ Transcribing audio..."):
            try:
                files = {"file": ("audio.webm", audio_bytes, "audio/webm")}
                res = requests.post(FASTAPI_TRANSCRIBE_URL, files=files, timeout=30)
                if res.status_code == 200:
                    transcribed_text = res.json().get("text", "").strip()
                    if transcribed_text:
                        send_user_message(transcribed_text)
                        st.rerun()
                else:
                    st.error(f"❌ Transcription error: {res.text}")
            except Exception as e:
                st.error(f"❌ Failed to connect to transcription server: {str(e)}")

latest_assistant = st.session_state.chat_history_display[-1]["content"] if st.session_state.chat_history_display and st.session_state.chat_history_display[-1]["role"] == "assistant" else ""
st.session_state.current_prompts = build_dynamic_prompts(latest_assistant)

with st.sidebar:
    st.header("💡 Suggested responses")
    for idx, prompt in enumerate(st.session_state.current_prompts[:10], start=1):
        if st.button(f"{idx}. {prompt['es']} — {prompt['en']}", key=f"suggestion_{idx}", use_container_width=True):
            send_user_message(prompt["es"])
            st.rerun()

for msg in reversed(st.session_state.chat_history_display):
    if msg.get("content") and "❌" not in msg.get("content"):
        if msg["role"] == "user":
            st.info(f"**You:** {msg['content']}")
        else:
            spanish_match = re.search(r"SPANISH:(.*?)(PROMPTS:|$)", msg["content"], re.DOTALL | re.IGNORECASE)
            with st.chat_message("assistant"):
                raw_text = spanish_match.group(1).strip() if spanish_match else msg["content"]
                formatted = [f":orange[{l.replace('-> EN:', '').strip()}]" if l.strip().startswith("-> EN:") else l.strip() for l in raw_text.split("\n") if l.strip()]
                st.markdown("\n\n".join(formatted))

if os.path.exists("/tmp/web_response.mp3") and st.session_state.get("play_audio", False):
    st.audio("/tmp/web_response.mp3", format="audio/mp3", autoplay=True)
    st.session_state.play_audio = False
