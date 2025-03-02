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
    layout="wide",  # Tam genişlik için wide kullanıyoruz
    initial_sidebar_state="collapsed"
)

# Tüm varsayılan stilleri override eden CSS
st.markdown("""
<style>
    /* Tüm varsayılan stilleri sıfırla */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding: 0;
    }

    /* En üst düzey container */
    .main > div:first-child {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* Streamlit'in tüm default container'larını sıfırla */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
    }

    /* Tüm gövdeyi kaplayan arkaplan */
    .body-background {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        z-index: -1;
    }

    /* Üst banner */
    .header-card {
        width: 100%;
        box-sizing: border-box;
        margin: 0 auto;
        padding: 3rem 1rem 1rem 1rem;
        background: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(5px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        overflow: hidden;
        position: relative;
    }

    /* Yıldız animasyonu */
    .stars {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
    }

    /* Ana içerik container */
    .main-content {
        width: 90%;
        max-width: 1200px;
        margin: 2rem auto;
        padding: 0 1rem;
    }

    /* Başlık konteyner stilleri */
    .title-container {
        text-align: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 2rem;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        transform: translateZ(0);
    }

    /* Başlık ve alt başlık */
    .title {
        color: white;
        font-size: 3.5rem;
        font-weight: 700;
        text-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
        margin: 0;
        padding: 0;
        line-height: 1.2;
    }

    .subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.25rem;
        font-style: italic;
        margin-top: 0.5rem;
        text-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
    }

    /* İçerik kartları */
    .content-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(118, 75, 162, 0.1);
    }

    /* Başlıklar */
    .section-header {
        color: #764ba2;
        text-align: center;
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }

    /* Resim yükleme alanı */
    .uploadFile > div > div {
        border: 2px dashed #764ba2 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        background: rgba(118, 75, 162, 0.05) !important;
    }

    /* Analiz butonu */
    div.stButton > button {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        border-radius: 50px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        font-size: 1.1rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3) !important;
    }

    div.stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(118, 75, 162, 0.4) !important;
    }

    div.stButton > button:active {
        transform: translateY(1px) !important;
    }

    /* Sonuç kartı özel stilleri */
    .result-container {
        border-left: 5px solid #764ba2;
        line-height: 1.8;
    }

    b {
        color: #764ba2;
        font-weight: bold;
        background: rgba(118, 75, 162, 0.1);
        padding: 3px 8px;
        border-radius: 4px;
        margin: 2px 0;
        display: inline-block;
    }

    /* Footer stili */
    .footer {
        text-align: center;
        color: white;
        padding: 2rem 0;
        font-size: 0.875rem;
        text-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
        margin-top: 2rem;
        background: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(5px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Spinner stilleri */
    .stSpinner > div {
        border-top-color: #764ba2 !important;
    }

    /* Hata mesajı stilleri */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #764ba2 !important;
        border-color: #764ba2 !important;
    }
    
    /* Responsive stilller */
    @media screen and (max-width: 768px) {
        .title {
            font-size: 2.5rem;
        }
        
        .subtitle {
            font-size: 1rem;
        }
        
        .content-card {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Sayfa arkaplanı - sayfayı tamamen kaplamak için
st.markdown('<div class="body-background"></div>', unsafe_allow_html=True)

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

# Yeni HTML yapısı - tüm içeriği bir container içine alarak
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Üst header bölümü
st.markdown('<header class="header-card">', unsafe_allow_html=True)
st.markdown('<div class="stars"></div>', unsafe_allow_html=True)
st.markdown('<div class="title-container">', unsafe_allow_html=True)
st.markdown('<h1 class="title">✨ Avuç İçi Okuyucu AI ✨</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Yapay zeka ile geleceğinizi keşfedin</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</header>', unsafe_allow_html=True)

# Kullanıcı giriş bölümü
st.markdown('<div class="content-card">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown('<h3 class="section-header">Kişisel Bilgiler</h3>', unsafe_allow_html=True)
    user_name = st.text_input("Adınızı girin:", placeholder="Adınızı buraya yazın...")

with col2:
    st.markdown('<h3 class="section-header">Avuç İçi Görüntüsü</h3>', unsafe_allow_html=True)
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
        st.markdown('<div class="content-card result-container">', unsafe_allow_html=True)
        st.markdown(result, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("❗ Lütfen hem adınızı girin hem de bir avuç içi resmi yükleyin!")

# Ana içerik div'ini kapat
st.markdown('</div>', unsafe_allow_html=True)

# Footer - sayfanın en altında olacak şekilde
st.markdown('<footer class="footer">', unsafe_allow_html=True)
st.markdown('© 2025 Avuç İçi Fal AI | Barış Güleç tarafından geliştirildi', unsafe_allow_html=True)
st.markdown('</footer>', unsafe_allow_html=True)

# Yıldız animasyonu için JavaScript
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Yıldız elementlerini oluştur
    var stars = document.querySelector('.stars');
    if (stars) {
        for (var i = 0; i < 150; i++) {
            var star = document.createElement('div');
            star.style.position = 'absolute';
            star.style.width = (Math.random() * 2 + 1) + 'px';
            star.style.height = (Math.random() * 2 + 1) + 'px';
            star.style.backgroundColor = 'white';
            star.style.borderRadius = '50%';
            star.style.top = Math.random() * 100 + '%';
            star.style.left = Math.random() * 100 + '%';
            star.style.animationDuration = (Math.random() * 3 + 1) + 's';
            star.style.animationDelay = Math.random() + 's';
            star.style.animationTimingFunction = 'ease-in-out';
            star.style.animationIterationCount = 'infinite';
            star.style.animationDirection = 'alternate';
            star.style.animationName = 'twinkle';
            star.style.opacity = Math.random() * 0.7 + 0.3;
            
            stars.appendChild(star);
        }
    }
});

// Twinkle animasyonu tanımla
if (!document.querySelector('#star-animation')) {
    var style = document.createElement('style');
    style.id = 'star-animation';
    style.textContent = `
        @keyframes twinkle {
            0% { opacity: 0.3; transform: scale(0.7); }
            100% { opacity: 1; transform: scale(1.3); }
        }
    `;
    document.head.appendChild(style);
}
</script>
""", unsafe_allow_html=True)
