# PalmReaderAI - Created for GDG Kütahya by Barış Güleç

**PalmReaderAI** is a Flask-based web application designed to generate personalized palm readings from uploaded hand images. This project leverages cutting-edge AI models like Groq (llama-3.2-90b-vision-preview) and Gemini to create meaningful and engaging palm reading results, translated beautifully into Turkish.

---

## Features

- **AI-Powered Palm Analysis**: Utilizes the `Llama` AI model to analyze hand lines, finger length, and palm structure.
- **Dynamic Formatting**: Enhances readability with bold highlights for key insights.
- **Image Compression**: Optimizes uploaded images for efficient processing.
- **Turkish Language Support**: Translates results into Turkish with cultural nuances.
- **Secure and Scalable**: Protects sensitive data and API keys with environment variables.

---

## Technologies Used

- **Python**
- **Flask**
- **Pillow** (Image Processing)
- **Groq and Gemini AI Models**
- **dotenv** (Environment Variable Management)

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/PalmReaderAI.git
   cd PalmReaderAI
