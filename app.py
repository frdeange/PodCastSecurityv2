from flask import Flask, render_template, request, jsonify  
import os  
import openai  
from azure.ai.formrecognizer import DocumentAnalysisClient  
from azure.core.credentials import AzureKeyCredential  
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig  
import ffmpeg  
from dotenv import load_dotenv  
  
# Cargar variables de entorno desde .env  
load_dotenv()  
  
app = Flask(__name__)  
  
# Configuraciones de Azure desde variables de entorno  
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')  
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')  
AZURE_FORM_RECOGNIZER_KEY = os.getenv('AZURE_FORM_RECOGNIZER_KEY')  
AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')  
AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')  
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')  
  
# Configuración de OpenAI  
openai.api_key = AZURE_OPENAI_KEY  
openai.api_base = AZURE_OPENAI_ENDPOINT  
openai.api_type = 'azure'  
openai.api_version = '2022-12-01'  # Ajusta la versión según tu configuración  
  
@app.route('/')  
def index():  
    return render_template('index.html')  
  
@app.route('/extract_text_from_pdf', methods=['POST'])  
def extract_text_from_pdf():  
    file = request.files['pdf-file']  
    use_azure = request.form.get('azure')  
  
    if use_azure:  
        # Lógica para extraer texto usando Azure Form Recognizer  
        client = DocumentAnalysisClient(  
            endpoint=AZURE_FORM_RECOGNIZER_ENDPOINT,   
            credential=AzureKeyCredential(AZURE_FORM_RECOGNIZER_KEY)  
        )  
        poller = client.begin_analyze_document("prebuilt-document", file)  
        result = poller.result()  
        text = " ".join([line.content for page in result.pages for line in page.lines])  
    else:  
        # Lógica alternativa para extraer texto de PDF  
        text = "Texto extraído del PDF"  
  
    return jsonify({'text': text})  
  
@app.route('/extract_text_from_website', methods=['POST'])  
def extract_text_from_website():  
    url = request.form['website-url']  
    # Lógica para extraer texto de una URL (puedes usar BeautifulSoup o una solución similar)  
    text = "Texto extraído del sitio web"  
    return jsonify({'text': text})  
  
@app.route('/generate_outline', methods=['POST'])  
def generate_outline():  
    content = request.form['content']  
    response = openai.Completion.create(  
        engine="gpt-4",  # Usar el modelo GPT-4  
        prompt=f"Resumen del contenido: {content}",  
        max_tokens=150  
    )  
    outline = response.choices[0].text.strip()  
    return jsonify({'outline': outline})  
  
@app.route('/generate_audio', methods=['POST'])  
def generate_audio():  
    outline = request.form['outline']  
    speaker1 = request.form['speaker1']  
    speaker2 = request.form['speaker2']  
  
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)  
  
    def generate_speech(text, speaker):  
        audio_config = AudioConfig(filename=f"{speaker}.wav")  
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)  
        synthesizer.speak_text_async(text).get()  
  
    # Dividir el outline en dos partes y asignar a cada speaker  
    parts = outline.split("\n")  
    generate_speech(parts[0], speaker1)  
    generate_speech(parts[1], speaker2)  
  
    # Combinar audios con ffmpeg  
    os.system(f"ffmpeg -i concat:{speaker1}.wav|{speaker2}.wav -acodec copy output.wav")  
  
    return jsonify({'audio_file': 'output.wav'})  
  
if __name__ == '__main__':  
    app.run(debug=True)  
