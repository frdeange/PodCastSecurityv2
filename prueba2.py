import os
import openai
from pathlib import Path

# Variables de entorno
endpoint = "https://aoai-podcastdemo.cognitiveservices.azure.com/"  # Ajuste del endpoint para Azure OpenAI
api_key = "bf87a84621fc413e8ed96b59cd8e56c7"  # Asegúrate de almacenar esto en una variable de entorno por seguridad
speech_file_path = "outputaudio.wav"

# Inicialización de OpenAI con las configuraciones de Azure
openai.api_type = "azure"
openai.api_base = endpoint  # El endpoint de Azure OpenAI
openai.api_version = "2024-08-01-preview"  # Versión de la API de Azure
openai.api_key = api_key  # API Key de Azure

# Función principal
def main():
    print("== Text to Speech Sample ==")

    try:
        # Generar archivo de audio con Text-to-Speech en Azure OpenAI
        response = openai.Audio.create(
            model="tts",  # Modelo especificado
            voice="alloy",
            input="the quick brown chicken jumped over the lazy dogs"
        )
        
        # Guardar el archivo de audio generado
        with open(speech_file_path, "wb") as audio_file:
            for chunk in response.iter_bytes():  # Iterar sobre el contenido en bytes
                audio_file.write(chunk)

        print(f"Audio file saved to {speech_file_path}")

    except Exception as e:
        print(f"The sample encountered an error: {e}")

if __name__ == "__main__":
    main()
