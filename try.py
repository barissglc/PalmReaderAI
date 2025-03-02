import streamlit as st
import base64
import os
import re
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from groq import Groq

# .env dosyasından API anahtarlarını yükle
load_dotenv()

# API anahtarlarını ortam değişkenlerinden al
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

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
        return f"An error occurred during palm reading: {str(e)}"

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
        return f"Translation error: {str(e)}"

# Streamlit arayüzü
st.title("Palm Reader AI")

user_name = st.text_input("Adınızı girin:")
uploaded_file = st.file_uploader("Avuç içi resminizi yükleyin", type=["jpg", "jpeg", "png"])

if st.button("Avuç İçi Analizi Yap") and user_name and uploaded_file:
    with st.spinner("Analiz ediliyor..."):
        result = generate_palm_reading(uploaded_file, user_name)
    st.markdown(result, unsafe_allow_html=True)
elif st.button("Avuç İçi Analizi Yap"):
    st.error("Lütfen hem adınızı girin hem de bir resim yükleyin!")
