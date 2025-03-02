import streamlit as st
import base64
import os
import re
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from groq import Groq

# Sayfa konfigürasyonu ve tema ayarları
st.set_page_config(
    page_title="Avuç İçi Okuyucu AI",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Modern CSS stilleri
st.markdown("""
<style>
:root {
    --primary-color: #764ba2;
    --secondary-color: #667eea;
    --bg-light: #f5f5f5;
    --white: #ffffff;
    --shadow-light: rgba(0, 0, 0, 0.1);
}

body {
    font-family: 'Roboto', sans-serif;
    background: var(--bg-light);
    margin: 0;
    padding: 0;
}

.stApp {
    background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
}

/* Üst kısım için dekoratif elementler */
.decorative-pattern {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 200px;
    background: 
        radial-gradient(circle at 20% 30%, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 50%),
        radial-gradient(circle at 80% 70%, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 50%);
    pointer-events: none;
}

.stars-pattern {
    position: absolute;
    top: 20px;
    left: 0;
    right: 0;
    height: 100px;
    background-image: 
        radial-gradient(white 1px, transparent 1px),
        radial-gradient(white 1px, transparent 1px);
    background-size: 50px 50px;
    background-position: 0 0, 25px 25px;
    opacity: 0.1;
    animation: twinkle 3s infinite alternate;
}

@keyframes twinkle {
    from {opacity: 0.05;}
    to {opacity: 0.15;}
}

.main {
    position: relative;
    background: var(--white);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 8px 16px var(--shadow-light);
    max-width: 900px;
    margin: 1rem auto;
    z-index: 1;
}

.title-container {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    padding: 2rem;
    margin: 1rem auto 1.5rem;
    backdrop-filter: blur(10px);
    text-align: center;
    max-width: 800px;
    position: relative;
    z-index: 2;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.title {
    color: var(--white);
    font-size: 3rem;
    font-weight: 700;
    text-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    margin-bottom: 0.5rem;
    letter-spacing: 1px;
}

.subtitle {
    color: var(--white);
    font-size: 1.25rem;
    font-style: italic;
    opacity: 0.9;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.input-container {
    background: var(--white);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 4px 8px var(--shadow-light);
    margin-bottom: 1.5rem;
}

.analyze-button {
    background-color: var(--primary-color);
    color: var(--white);
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 0.75rem 2rem;
    margin-top: 1.5rem;
    cursor: pointer;
    transition: transform 0.2s ease, filter 0.2s ease;
    width: 100%;
}

.analyze-button:hover {
    transform: scale(1.02);
    filter: brightness(90%);
}

.result-container {
    background: var(--white);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 4px 8px var(--shadow-light);
    line-height: 1.6;
    margin-bottom: 1.5rem;
}

.loading-spinner {
    text-align: center;
    margin-top: 20px;
}

.footer {
    color: var(--white);
    text-align: center;
    margin-top: 2rem;
    font-size: 0.875rem;
    opacity: 0.8;
}

b {
    color: var(--primary-color);
    font-weight: bold;
    background: rgba(118, 75, 162, 0.1);
    padding: 2px 6px;
    border-radius: 3px;
    margin: 3px 0;
    display: inline-block;
}

/* Responsive düzenlemeler */
@media (max-width: 768px) {
    .title {
        font-size: 2.5rem;
    }
    .subtitle {
        font-size: 1rem;
    }
    .input-container {
        padding: 1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# Dekoratif elementler
st.markdown('<div class="decorative-pattern"></div>', unsafe_allow_html=True)
st.markdown('<div class="stars-pattern"></div>', unsafe_allow_html=True)

# API anahtarlarını Streamlit secrets'dan al
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def format_reading_dynamically(text):
    formatted_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    formatted_text = re.sub(r"<b>(.*?)</b>", r"<b>\1</b><br>", formatted_text)
    return formatted_text

def compress_image(image_file, max_size=(300, 300), quality=25):
    image_file.seek(0)  # Dosya işaretçisini başa al
    with Image.open(image_file) as img:
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        compressed_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return compressed_data

def generate_palm_reading(image_file, user_name):
    try:
        base64_image = compress_image(image_file)
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"As a friendly and mystical fortune teller, analyze {user_name}'s palm. "
                        f"Focus on the main lines (heart, head, life, fate), hand structure, finger shape, and any special signs. "
                        f"Provide detailed analysis based on the physical characteristics of {user_name}'s hand, such as the thickness of the palm, "
                        f"the length of the fingers, and the overall shape of the hand (e.g., long and thin, short and broad). "
                        f"Use a warm, engaging, and slightly mystical tone to make positive predictions, but if you see something that could be a future challenge, "
                        f"mention it for {user_name} to grow. Create an intimate and personal connection with {user_name}, using phrases like 'dear {user_name}', "
                        f"and always end on a positive and hopeful note. Be sure to mention how the physical features relate to {user_name}'s personality traits and potential future."
                    )
                },
                {
                    "role": "user",
                    "content": f"data:image/jpeg;base64,{base64_image}"
                }
            ],
            temperature=0.85,
            max_tokens=1000,
            top_p=1,
            stream=False
        )
        english_reading = completion.choices[0].message.content
        turkish_reading = translate_to_turkish(english_reading, user_name)
        formatted_reading = format_reading_dynamically(turkish_reading)
        return formatted_reading
    except Exception as e:
        return f"Avuç içi analizi sırasında bir hata oluştu: {str(e)}"

def translate_to_turkish(english_text, user_name):
    try:
        generation_config = {
            "temperature": 0.80,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 1300,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
        )

        chat_session = model.start_chat(history=[])

        prompt = (
            "You are an experienced professional translator fluent in both English and Turkish. "
            "Your task is to translate the given English text into Turkish while preserving cultural nuances "
            "and ensuring a warm, engaging tone. "
            f"Refer to the user by their name ({user_name}) where appropriate. "
            "Make sure the translation reads naturally and fluently in Turkish, avoiding overly formal expressions. "
            "Translate specific terms, such as 'mounts', 'lines', and 'rings' related to palmistry, into culturally "
            "appropriate and contextually accurate Turkish terms. "
            "Ensure that the final translation is grammatically correct, contextually fitting, and conveys the intended message clearly. "
            "End the text with a meaningful, complete, and uplifting conclusion that leaves a positive impression."
        )

        response = chat_session.send_message(
            f"{prompt}\n\nTranslate this text:\n{english_text}"
        )

        return response.text
    except Exception as e:
        return f"Çeviri hatası: {str(e)}"

# Ana içerik bölümü
st.markdown('<div class="title-container">', unsafe_allow_html=True)
st.markdown('<h1 class="title">✨ Avuç İçi Okuyucu AI ✨</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Yapay zeka ile geleceğinizi keşfedin</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Kullanıcı giriş bölümü
st.markdown('<div class="input-container">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown("<h3 style='text-align: center;'>Kişisel Bilgiler</h3>", unsafe_allow_html=True)
    user_name = st.text_input("Adınızı girin:", placeholder="Adınızı buraya yazın...")

with col2:
    st.markdown("<h3 style='text-align: center;'>Avuç İçi Görüntüsü</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Avuç içi resminizi yükleyin:", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, width=200, caption="Yüklenen görüntü")

st.markdown('</div>', unsafe_allow_html=True)

# Analiz butonu
analyze_clicked = st.button("🔮 Avuç İçi Analizi Yap", key="analyze_button", use_container_width=True)

# Sonuç işleme
if analyze_clicked:
    if user_name and uploaded_file:
        with st.spinner("🪄 Avuç içiniz analiz ediliyor... Lütfen bekleyin..."):
            result = generate_palm_reading(uploaded_file, user_name)
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.markdown(result, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("❗ Lütfen hem adınızı girin hem de bir avuç içi resmi yükleyin!")

# Footer
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown('© 2025 Avuç İçi Fal AI | Barış Güleç tarafından geliştirildi', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
