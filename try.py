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

# Streamlit varsayılan CSS değerlerini override eden ve üst boşluğu tamamen kaldıran stil
st.markdown("""
<style>
    /* Streamlit varsayılan container stillerini override etme */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 1rem !important;
        margin-top: 0 !important;
    }
    
    /* Header alanını tamamen kaplayan banner */
    .header-banner {
        position: relative;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        width: 100%;
        padding: 2rem 0;
        margin-bottom: 2rem;
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    
    /* Yıldız animasyonu */
    .stars {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 0;
        overflow: hidden;
    }
    
    .star {
        position: absolute;
        width: 2px;
        height: 2px;
        background: white;
        border-radius: 50%;
        animation: twinkle 2s infinite alternate;
        opacity: 0.7;
    }
    
    @keyframes twinkle {
        0% {opacity: 0.3; transform: scale(0.8);}
        100% {opacity: 1; transform: scale(1.2);}
    }
    
    /* Başlık konteyner stilleri */
    .title-wrapper {
        position: relative;
        z-index: 1;
        text-align: center;
        padding: 0 1rem;
    }
    
    .title-container {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 2rem;
        backdrop-filter: blur(5px);
        max-width: 800px;
        margin: 0 auto;
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        z-index: 10;
    }
    
    .title {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.4);
        margin-bottom: 0.5rem;
        letter-spacing: 1px;
        line-height: 1.2;
    }
    
    .subtitle {
        color: white;
        font-size: 1.25rem;
        font-style: italic;
        opacity: 0.9;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.3);
    }
    
    /* İçerik container stilleri */
    .input-container {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(118, 75, 162, 0.1);
    }
    
    .result-container {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        line-height: 1.6;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(118, 75, 162, 0.1);
    }
    
    /* Footer stili */
    .footer {
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        margin-top: 2rem;
        font-size: 0.875rem;
        padding: 1rem 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    /* Diğer stil ayarları */
    b {
        color: #764ba2;
        font-weight: bold;
        background: rgba(118, 75, 162, 0.1);
        padding: 2px 6px;
        border-radius: 3px;
        margin: 3px 0;
        display: inline-block;
    }
    
    /* Responsive ayarlar */
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
    
    /* Streamlit spinner ve button stilleri */
    .stSpinner {
        text-align: center;
    }
    
    .stSpinner > div {
        border-top-color: #764ba2 !important;
    }
    
    div.stButton > button {
        background-color: #764ba2;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        background-color: #6a3d96;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(118, 75, 162, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# JavaScript ile dinamik yıldız oluşturma
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    const stars = document.querySelector('.stars');
    if (stars) {
        for (let i = 0; i < 100; i++) {
            const star = document.createElement('div');
            star.classList.add('star');
            star.style.top = `${Math.random() * 100}%`;
            star.style.left = `${Math.random() * 100}%`;
            star.style.animationDelay = `${Math.random() * 2}s`;
            stars.appendChild(star);
        }
    }
});
</script>
""", unsafe_allow_html=True)

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

# Tam sayfa boyunca uzanan banner header
st.markdown('<div class="header-banner">', unsafe_allow_html=True)
st.markdown('<div class="stars"></div>', unsafe_allow_html=True)
st.markdown('<div class="title-wrapper">', unsafe_allow_html=True)
st.markdown('<div class="title-container">', unsafe_allow_html=True)
st.markdown('<h1 class="title">✨ Avuç İçi Okuyucu AI ✨</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Yapay zeka ile geleceğinizi keşfedin</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
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
