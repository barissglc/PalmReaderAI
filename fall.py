from flask import Flask, request, render_template 
from groq import Groq
import base64
import os
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import re
from dotenv import load_dotenv

# .env dosyasındaki API anahtarlarını yükle
load_dotenv()

# API anahtarlarını ortam değişkenlerinden al
client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # APIKEY
genai.configure(api_key=os.getenv("GENAI_API_KEY"))  # APIKEY

app = Flask(__name__)

def format_reading_dynamically(text):
    formatted_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    formatted_text = re.sub(r"<b>(.*?)</b>", r"<b>\1</b><br>", formatted_text)
    return formatted_text

def compress_image(image_path, max_size=(300, 300), quality=25):
    with Image.open(image_path) as img:
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        compressed_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return compressed_data

def generate_palm_reading(image_path, user_name):
    try:
        base64_image = compress_image(image_path)
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"As a friendly and mystical fortune teller, analyze {user_name}'s palm. "
                        f"Focus on the main lines (heart, head, life, fate), hand structure, finger shape, and any special signs. "
                        f"Provide detailed analysis based on the physical characteristics of {user_name}'s hand, such as the thickness of the palm, "
                        f"the length of the fingers, and the overall shape of the hand (e.g., long and thin, short and broad)."
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

# def translate_to_turkish(english_text, user_name):
#     """
#     Translates given English text to Turkish using Llama-3 translation model with a persona for better context.
#     """
#     try:
#         # Translate the text using Groq API
#         translation_completion = client.chat.completions.create(
#             model="llama3-groq-70b-8192-tool-use-preview",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are an experienced professional translator fluent in both English and Turkish. "
#                         "Translate the following text with cultural appropriateness. "
#                         "Use a warm and engaging tone, and refer to the user by their name ({user_name}) where appropriate. "
#                         "Make sure the translation reads naturally and fluently in Turkish. "
#                         "Avoid overly formal expressions, and ensure that the final translation is grammatically correct and contextually fitting. "
#                         "Make sure to correctly translate specific terms related to palmistry, such as 'mounts', 'lines', and 'rings', ensuring that they are culturally and contextually appropriate in Turkish."
#                     )
#                 },
#                 {
#                     "role": "user",
#                     "content": english_text
#                 }
#             ],
#             temperature=0.75,
#             max_tokens=1000,
#             top_p=1,
#             stream=False
#         )
        
#         return translation_completion.choices[0].message.content

#     except Exception as e:
#         return f"Translation error: {str(e)}"

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
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
        )

        chat_session = model.start_chat(history=[])

        prompt = (
            "You are an experienced professional translator fluent in both English and Turkish. "
            "Your task is to translate the given English text into Turkish while preserving cultural nuances "
            "and ensuring a warm, engaging tone. "
            "Refer to the user by their name ({user_name}) where appropriate. "
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    user_name = request.form['name']
    image = request.files['palm_image']
    if not image:
        return "Lütfen bir resim seçin!"
    image_path = "temp_image.jpg"
    image.save(image_path)
    result = generate_palm_reading(image_path, user_name)
    if os.path.exists(image_path):
        os.remove(image_path)
    return render_template('result.html', name=user_name, result=result)

if __name__ == '__main__':
    app.run(debug=False)
