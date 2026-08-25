import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import requests
import io
import os
import re

# API backend URL used by the frontend to send requests.
# On local development it defaults to the local FastAPI instance.
# In cloud deployment Render sets this via environment variables.
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8001/api/v1/quantum-chat")

st.set_page_config(page_title="Quantum Spanish Assistant", page_icon="⚛️", layout="centered")
st.title("⚛️ Hybrid Quantum Spanish Assistant")
st.write("Speak into the microphone. The interface sends the full conversation history to the production FastAPI backend.")

st.sidebar.caption(f"API endpoint: {FASTAPI_URL}")

mic_sensitivity = st.sidebar.slider(
    "Microphone sensitivity",
    min_value=100,
    max_value=4000,
    value=150,
    step=50,
    help="Lower value = more sensitive to quiet speech. Higher value = less sensitive to background noise."
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
    "(Siguiente opção na hiszpański)\n"
    "-> EN: (Traduce la siguiente opción al inglés, hasta completar 10 pares)\n\n"
)


def normalize_prompt(text):
    clean = re.sub(r"^\d+[\.\)]\s*", "", text or "").strip()
    clean = re.sub(r"^[\-•*\s>]+", "", clean)
    clean = clean.replace("**", "").strip()
    return clean[:120].rstrip() + ("..." if len(clean) > 120 else "")


def sanitize_prompt_line(text):
    line = normalize_prompt(text)
    if not line:
        return ""

    low = line.lower()
    if re.match(r"^(?:->\s*)?(?:en|english|español|espanol)\s*[:\-]", low):
        return ""
    if re.match(r"^(?:>|\s)*(?:en|english|español|espanol)\s*[:\-]", line, re.I):
        return ""
    if re.match(r"^(?:beginner|intermediate|advanced|principiante|intermedio|avanzado)\b", line, re.I):
        return ""
    if " > " in line or line.startswith(">"):
        return ""
    if "en:" in line.lower() and "español" in line.lower():
        return ""
    if low.startswith("english:") or low.startswith("español:"):
        return ""

    if len(line) < 3 or len(line) > 120:
        return ""
    return line


def generate_english_translation(spanish_text):
    direct_map = {
        "¿Puedes repetirlo más despacio?": "Can you repeat it more slowly?",
        "¿Qué significa esta palabra?": "What does this word mean?",
        "¿Puedes hablar más claro?": "Can you speak more clearly?",
        "¿Cómo se dice esto en español?": "How do you say this in Spanish?",
        "¿Puedes darme un ejemplo?": "Can you give me an example?",
        "¿Puedes explicarlo en español?": "Can you explain it in Spanish?",
        "¿Puedes corregir mi frase?": "Can you correct my sentence?",
        "¿Cómo se responde a eso?": "How do you respond to that?",
        "Quiero practicar pronunciación.": "I want to practice pronunciation.",
        "¿Puedes hacer una pregunta para practicar?": "Can you ask me a question to practice?",
        "¿Puedes explicarlo con una frase simple?": "Can you explain it with a simple sentence?",
        "¿Puedes corregir mi pronunciación?": "Can you correct my pronunciation?",
        "¿Podemos practicarlo juntos?": "Can we practice it together?",
        "¿Cómo se usa esta palabra en una frase?": "How is this word used in a sentence?",
        "¿Puedes decirme más sobre esto?": "Can you tell me more about this?",
        "¿Cómo puedo practicar esto en conversación?": "How can I practice this in conversation?",
        "¡Sí!": "Yes!",
        "¡No!": "No!",
        "¡Tal vez!": "Maybe!",
        "¡Habla despacio!": "Speak slowly!",
        "¡Usa palabras sencillas!": "Use simple words!",
        "¡Repite después de mí!": "Repeat after me!",
        "¡Hazme una pregunta!": "Ask me a question!",
        "¡Dime un chiste!": "Tell me a joke!",
        "¡Muy bien!": "Very good!",
        "¡Excelente!": "Excellent!",
        "¡Gracias!": "Thank you!",
        "¡Vamos!": "Let’s go!",
    }

    text = (spanish_text or "").strip()
    if text in direct_map:
        return direct_map[text]

    patterns = [
        (r"^¿?Puedes explicar\s+(.+?)\s+con un ejemplo\??$", "Can you explain {0} with an example?"),
        (r"^¿?Cómo se usa\s+(.+?)\s+en una frase\??$", "How is {0} used in a sentence?"),
        (r"^¿?Qué diferencia hay entre\s+(.+?)\s+y\s+otra palabra\??$", "What is the difference between {0} and another word?"),
        (r"^¿?Puedes decirme más sobre\s+(.+?)\??$", "Can you tell me more about {0}?"),
        (r"^¿?Cómo puedo practicar\s+(.+?)\s+en conversación\??$", "How can I practice {0} in conversation?"),
        (r"^¿?Cómo se dice\s+(.+?)\s+en español\??$", "How do you say {0} in Spanish?"),
        (r"^¿?Qué significa\s+(.+?)\??$", "What does {0} mean?"),
        (r"^¿?Puedes hablar más claro\??$", "Can you speak more clearly?"),
        (r"^¿?Puedes repetirlo más despacio\??$", "Can you repeat it more slowly?"),
        (r"^¿?Puedes explicarlo en español\??$", "Can you explain it in Spanish?"),
        (r"^¿?Puedes corregir mi frase\??$", "Can you correct my sentence?"),
        (r"^¿?Cómo se responde a eso\??$", "How do you respond to that?"),
        (r"^¿?Puedes hacer una pregunta para practicar\??$", "Can you ask me a question to practice?"),
        (r"^¿?Puedes hacer una pregunta sobre esto\??$", "Can you ask me a question about this?"),
        (r"^¿?Podemos practicarlo juntos\??$", "Can we practice it together?"),
        (r"^¿?Puedes explicarlo con una frase simple\??$", "Can you explain it with a simple sentence?"),
        (r"^¿?Puedes corregir mi pronunciación\??$", "Can you correct my pronunciation?"),
        (r"^¿?Cómo se usa esta palabra en una frase\??$", "How is this word used in a sentence?"),
        (r"^¿?Puedes darme un ejemplo\??$", "Can you give me an example?"),
    ]

    for pattern, template in patterns:
        match = re.match(pattern, text, re.IGNORECASE)
        if not match:
            continue
        if match.lastindex:
            captured = match.group(1).strip()
            return template.format(captured)
        return template

    if text.startswith("¿"):
        return "Can you explain that in English?"
    if text.startswith("¡"):
        return "Can you explain this expression in English?"
    if text.endswith("."):
        return "I want to practice this phrase."
    return "Can you help me with this expression?"


def extract_topic_keywords(text):
    if not text:
        return []
    words = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÜüÑñ]+", text.lower())
    stopwords = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "de", "del",
        "al", "por", "para", "con", "como", "que", "qué", "porque", "pero", "si", "no",
        "estoy", "quiero", "puedes", "podrías", "más", "menos", "muy", "también",
        "cuando", "donde", "cuál", "cómo", "este", "esta", "estos", "estas", "aquí",
        "ahora", "sobre", "hacia", "dentro", "fuera", "muy", "yo", "tú", "tu", "mi",
        "ese", "esa", "esos", "esas", "una", "él", "ella", "nosotros", "vosotros"
    }
    keywords = []
    for w in words:
        if len(w) > 3 and w not in stopwords:
            keywords.append(w)
    return keywords[:6]


def build_dynamic_prompts(user_text, assistant_text=""):
    text = (user_text or "").lower()
    has_venezuela = "venezuela" in text or "wenezuel" in text
    has_travel = any(word in text for word in ["viaje", "viajar", "vacac", "turismo", "pais", "destino", "ciudad", "playa", "naturaleza", "comida", "cultura"])

    if has_venezuela or has_travel:
        travel_prompts = [
            {"es": "Me interesan las playas y el mar.", "en": "I am interested in the beaches and the sea."},
            {"es": "Quiero visitar ciudades y monumentos.", "en": "I want to visit cities and monuments."},
            {"es": "Me gusta la comida local.", "en": "I like local food."},
            {"es": "Quiero conocer la naturaleza.", "en": "I want to get to know the nature."},
            {"es": "Me interesa la cultura y la historia.", "en": "I am interested in the culture and history."},
            {"es": "Me gustaría escuchar música local.", "en": "I would like to listen to local music."},
            {"es": "Quiero descansar y relajarme.", "en": "I want to rest and relax."},
            {"es": "Me interesan los paisajes y los parques.", "en": "I am interested in landscapes and parks."},
            {"es": "Quiero probar platos típicos.", "en": "I want to try typical dishes."},
            {"es": "Me gustaría hablar con la gente local.", "en": "I would like to talk to local people."},
        ]
        return travel_prompts

    curated = [
        {"es": "¿Cómo estás?", "en": "How are you?"},
        {"es": "¿Cómo te llamas?", "en": "What is your name?"},
        {"es": "¿Puedes hablar más despacio?", "en": "Can you speak more slowly?"},
        {"es": "No entiendo.", "en": "I do not understand."},
        {"es": "¿Qué significa esta palabra?", "en": "What does this word mean?"},
        {"es": "¿Puedes repetirlo?", "en": "Can you repeat it?"},
        {"es": "Quiero practicar español.", "en": "I want to practice Spanish."},
        {"es": "¿Dónde está el baño?", "en": "Where is the bathroom?"},
        {"es": "Gracias.", "en": "Thank you."},
        {"es": "Por favor.", "en": "Please."},
    ]
    return curated


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
    with st.spinner("🧠 Backend is processing the request (Quantum + RAG + Postgres)..."):
        response = requests.post(FASTAPI_URL, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            bot_response = data["response"]
            q_style = data["quantum_style_applied"]

            if q_style != "Normal":
                st.toast(f"⚛️ Quantum effect: {q_style}", icon="⚛️")

            st.session_state.chat_history_display.append({"role": "assistant", "content": bot_response})
        else:
            st.error(f"Backend error. Status code: {response.status_code}")

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
            tts = gTTS(text=clean_audio_text, lang='es')
            tts.save("web_response.mp3")
            st.session_state.play_audio = True


if "chat_history_display" not in st.session_state:
    st.session_state.chat_history_display = []

if "current_prompts" not in st.session_state:
    st.session_state.current_prompts = build_dynamic_prompts("")

if "play_audio" not in st.session_state:
    st.session_state.play_audio = False

st.subheader("🎛️ Configuration and recording")

if st.button("🔄 Reset conversation view and clear memory"):
    if os.path.exists("web_response.mp3"):
        os.remove("web_response.mp3")
    st.session_state.clear()
    st.rerun()

audio_file = st.audio_input("Click the microphone icon to start speaking in Spanish", key="microphone_input")

if audio_file is not None:
    audio_bytes = audio_file.read()
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = mic_sensitivity
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.3
    recognizer.pause_threshold = 0.8
    
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio_data = recognizer.record(source)
        
    try:
        user_text = recognizer.recognize_google(audio_data, language="es-ES")
        
        if "last_processed" not in st.session_state or st.session_state.last_processed != user_text:
            st.session_state.last_processed = user_text
            send_user_message(user_text)
            st.rerun()
                    
    except Exception:
        st.error("🔕 Network error while contacting the backend.")

# SUGGESTION PARSER
latest_user = ""
for msg in reversed(st.session_state.chat_history_display):
    if msg["role"] == "user":
        latest_user = msg["content"]
        break

latest_assistant = ""
for msg in reversed(st.session_state.chat_history_display):
    if msg["role"] == "assistant":
        latest_assistant = msg["content"]
        break

st.session_state.current_prompts = build_dynamic_prompts(latest_user, latest_assistant)

with st.sidebar:
    st.header("💡 Suggested responses")
    for idx, prompt in enumerate(st.session_state.current_prompts[:10], start=1):
        if st.button(f"{idx}. {prompt['es']} — {prompt['en']}", key=f"suggestion_{idx}", use_container_width=True):
            send_user_message(prompt["es"])
            st.rerun()

# RENDER CONVERSATION WINDOW
for msg in reversed(st.session_state.chat_history_display):
    if msg["role"] == "user":
        st.info(f"**You:** {msg['content']}")
    elif msg["role"] == "assistant":
        content = msg["content"]
        spanish_match = re.search(r"SPANISH:(.*?)(PROMPTS:|$)", content, re.DOTALL | re.IGNORECASE)
        
        with st.chat_message("assistant"):
            if spanish_match:
                st.markdown("🗣️ **Conversation:**")
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

if os.path.exists("web_response.mp3") and st.session_state.get("play_audio", False):
    st.audio("web_response.mp3", format="audio/mp3", autoplay=True)
    st.session_state.play_audio = False
