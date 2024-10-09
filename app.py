import os
import openai
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
from PyPDF2 import PdfReader
import xml.etree.ElementTree as ET
import datetime
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from flask import Flask, render_template, request, jsonify
from pathlib import Path

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Azure OpenAI Config from environment variables
AZURE_OPENAI_TYPE = os.getenv('AZURE_OPENAI_TYPE')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_ENGINE = os.getenv('AZURE_OPENAI_ENGINE')

# Azure Form Recognizer config from environment variables
AZURE_FORM_RECOGNIZER_KEY = os.getenv('AZURE_FORM_RECOGNIZER_KEY')
AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')

# Azure Speech Services config from environment variables
AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')

# Azure Blob Storage config from environment variables
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME')
container_client = blob_service_client.get_container_client(container_name)

# OpenAI configuration for Azure
openai.api_type = AZURE_OPENAI_TYPE
openai.api_key = AZURE_OPENAI_KEY
openai.api_base = AZURE_OPENAI_ENDPOINT  # Make sure it ends with "/"
openai.api_version = AZURE_OPENAI_API_VERSION  # Ensure it's compatible with your deployment

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract_text_from_pdf', methods=['POST'])
def extract_text_from_pdf():
    file = request.files['pdf-file']
    use_azure = request.form.get('azure')

    if use_azure == 'on':
        # Logic to extract text using Azure Form Recognizer
        client = DocumentAnalysisClient(
            endpoint=AZURE_FORM_RECOGNIZER_ENDPOINT,
            credential=AzureKeyCredential(AZURE_FORM_RECOGNIZER_KEY)
        )
        poller = client.begin_analyze_document("prebuilt-document", file)
        result = poller.result()
        text = " ".join([line.content for page in result.pages for line in page.lines])
    else:
        # Alternative logic to extract text from PDF using PyPDF2
        reader = PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return jsonify({'text': text})

@app.route('/extract_text_from_website', methods=['POST'])
def extract_text_from_website():
    url = request.form['website-url']
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Remove scripts and styles
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        text = ' '.join(soup.stripped_strings)
    except Exception as e:
        text = f"Error extracting text from the website: {e}"
    return jsonify({'text': text})

@app.route('/generate_outline', methods=['POST'])
def generate_outline():
    content = request.form['content']
    try:
        response = openai.chat.completions.create(
            model=AZURE_OPENAI_ENGINE,
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that generates podcast conversations in SSML format with voice placeholders."
                },
                {
                    "role": "user",
                    "content": f"""Generate a podcast conversation between two speakers discussing the following content: {content}

The podcast should be brief and start with a quick introduction to the topic.
Then, the two speakers should have a lively discussion covering the most important points.
The two speakers should have different speaking styles.

Provide the conversation in valid SSML format, including the <speak> tag at the beginning and end of the document.
Set the xml:lang attribute in the <speak> tag to "en-US".
Use placeholders {{Speaker1_Voice}} and {{Speaker2_Voice}} for the voice names in the <voice> tags.
For example:

<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice name="{{Speaker1_Voice}}">Speaker 1's dialogue</voice>
  <voice name="{{Speaker2_Voice}}">Speaker 2's dialogue</voice>
</speak>

Ensure that the SSML is well-formed and can be interpreted by Azure Speech Services. Add Prosody and Emphasis tags to make the conversation more engaging, but do not use fast prosody never.

Do not include any text outside of the SSML tags."""
                }
            ],
        )
        outline = response.choices[0].message.content.strip()
    except Exception as e:
        outline = f"Error generating the outline: {e}"
    return jsonify({'outline': outline})

def is_valid_ssml(ssml_content):
    try:
        ET.fromstring(ssml_content)
        return True
    except ET.ParseError as e:
        print(f"Invalid SSML: {e}")
        return False

@app.route('/generate_audio', methods=['POST'])
def generate_audio():
    ssml_outline = request.form['outline']
    speaker1 = request.form['speaker1']
    speaker2 = request.form['speaker2']

    # Replace placeholders with voices selected by the user
    ssml_outline = ssml_outline.replace('{Speaker1_Voice}', speaker1)
    ssml_outline = ssml_outline.replace('{Speaker2_Voice}', speaker2)

    if not is_valid_ssml(ssml_outline):
        return jsonify({'error': 'The SSML content is not valid.'}), 400

    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)

    # Create a unique identifier for the audio file
    unique_id = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f'output_{unique_id}.wav'
    file_path = f'/tmp/{file_name}'  # Use a temporary directory

    # Generate speech and save locally first
    if not generate_speech(ssml_outline, file_path, speech_config):
        return jsonify({'error': 'Error generating the audio.'}), 500

    # Verify the file exists before uploading
    if not os.path.exists(file_path):
        print(f"Error: The file at {file_path} does not exist.")
        return jsonify({'error': f'The file at {file_path} does not exist.'}), 500

    # Upload the file to Azure Blob Storage
    try:
        blob_url = upload_to_blob_storage(file_name, file_path)
        # print(f"File successfully uploaded to: {blob_url}")
    except Exception as e:
        return jsonify({'error': f'Error uploading audio to Azure Blob Storage: {e}'}), 500

    return jsonify({'audio_file': blob_url})

def generate_speech(ssml_content, file_path, speech_config):
    audio_config = AudioConfig(filename=file_path)
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    try:
        result = synthesizer.speak_ssml_async(ssml_content).get()
        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.error_details:
                print(f"Error details: {cancellation_details.error_details}")
            return False
        return True
    except Exception as e:
        print(f"Error synthesizing speech: {e}")
        return False

def upload_to_blob_storage(blob_name, file_path):
    try:
        # Create the blobn client
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload the file to the blob
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        # Generate a SAS token for the blob
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)  # Valid for 1 hour
        )
        
        # Generate the blob URL
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        
        print(f"File uploaded to: {blob_url}")
        return blob_url
    except Exception as e:
        print(f"Error uploading to Blob Storage: {e}")
        raise

def is_valid_ssml(ssml_content):
    try:
        ET.fromstring(ssml_content)
        return True
    except ET.ParseError as e:
        print(f"Invalid SSML: {e}")
        return False

if __name__ == '__main__':
    if not os.path.exists('audio_output'):
        os.makedirs('audio_output')
    app.run(debug=True)