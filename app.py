import os
import openai
import requests
import xml.etree.ElementTree as ET
import datetime
import azure.cognitiveservices.speech as speechsdk
import re
import tempfile
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from flask import Flask, render_template, request, jsonify
from pathlib import Path
from pydub import AudioSegment

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
    files = request.files.getlist('pdf-files')
    use_azure = request.form.get('azure')
    all_text = ""

    for file in files:
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

        all_text += text + "\n\n"  # Concatenate text from each file with a separator

    return jsonify({'text': all_text})

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
    language = request.form['language']

    try:
        response = openai.chat.completions.create(
            model=AZURE_OPENAI_ENGINE,
            messages=[
                {
                    "role": "system",
                    "content": f"You are an assistant that generates podcast conversations in SSML format with voice placeholders. Language: {language}."
                },
                {
                    "role": "user",
                    "content": f"""Generate a brief podcast conversation between two speakers discussing the following content: {content}

- Start with a quick introduction to the topic.
- Create a lively discussion covering key points.
- Use different speaking styles for each speaker.
- Output in valid SSML with <speak> tags.
- Do not add any content before or after the XML structure.
- Set xml:lang="{language}" in the <speak> tag and generates the content in the same language of the tag adjusting the text to be correct into the language.
- Use placeholders {{Speaker1_Voice}} and {{Speaker2_Voice}} for voice names.
- Encapsulate each speaker's dialogue within <voice> and <prosody> tags.
- Apply consistent prosody attributes (e.g., rate="medium"). Do not use rate="fast".
- Add <emphasis> tags where appropriate.
- Ensure all XML tags are properly closed.
- If input is a script, convert it directly to SSML without altering dialogue.

**Example:**

<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">
  <voice name="{{Speaker1_Voice}}">
    <prosody rate="medium">Welcome to our podcast! Today, we're diving into Microsoft partnerships.</prosody>
  </voice>
  <voice name="{{Speaker2_Voice}}">
    <prosody pitch="high" rate="medium">It's a jungle out there!</prosody>
  </voice>
  <!-- Continue with similar structure -->
</speak>."""
                }
            ],
        )
        outline = response.choices[0].message.content.strip()
    except Exception as e:
        outline = f"Error generating the outline: {e}"
    return jsonify({'outline': outline})

def split_ssml(ssml_content, max_voice_elements=50):
    """
    Splits SSML content into multiple chunks, each with up to max_voice_elements <voice> tags.
    Returns a list of SSML strings.
    """
    print(f"SSML content before parsing: {ssml_content}")  # Debug print to see SSML content before parsing
    try:
        root = ET.fromstring(ssml_content)
    except ET.ParseError as e:
        print(f"Error parsing SSML: {e}")
        return []

    # Define namespace and use it to find <voice> elements
    ns = {'synthesis': 'http://www.w3.org/2001/10/synthesis'}
    voices = root.findall('.//synthesis:voice', namespaces=ns)

    if not voices:
        print("No <voice> elements found in the SSML. Make sure the SSML content has properly formatted <voice> tags.")
        return []

    chunks = []
    current_chunk = ET.Element('speak', {
        'version': '1.0',
        'xmlns': 'http://www.w3.org/2001/10/synthesis',
        'xml:lang': 'en-US'
    })

    count = 0
    for voice in voices:
        if count >= max_voice_elements:
            chunks.append(ET.tostring(current_chunk, encoding='unicode'))
            current_chunk = ET.Element('speak', {
                'version': '1.0',
                'xmlns': 'http://www.w3.org/2001/10/synthesis',
                'xml:lang': 'en-US'
            })
            count = 0
        current_chunk.append(voice)
        count += 1

    if count > 0:
        chunks.append(ET.tostring(current_chunk, encoding='unicode'))

    print(f"Total chunks created: {len(chunks)}")
    return chunks

def combine_audio_files(audio_files, output_path):
    """
    Combines multiple audio files into a single file using pydub.
    """
    try:
        combined = AudioSegment.empty()
        for file in audio_files:
            audio = AudioSegment.from_wav(file)
            combined += audio
        combined.export(output_path, format="wav")
        print(f"Combined audio file created at: {output_path}")
    except Exception as e:
        print(f"Error combining audio files: {e}")
        raise

def generate_speech(ssml_content, file_path, speech_config):
    """
    Generates an audio file from SSML content using Azure Speech Services.
    """
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
    """
    Uploads a file to Azure Blob Storage and generates a SAS URL valid for 1 hour.
    """
    try:
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
        
        # Generate the blob URL with the SAS token
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        
        print(f"File uploaded to: {blob_url}")
        return blob_url
    except Exception as e:
        print(f"Error uploading to Blob Storage: {e}")
        raise

def is_valid_ssml(ssml_content):
    """
    Checks if the SSML content is valid.
    """
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

    # Replace placeholders with the selected voices
    ssml_outline = ssml_outline.replace('{Speaker1_Voice}', speaker1)
    ssml_outline = ssml_outline.replace('{Speaker2_Voice}', speaker2)

    if not is_valid_ssml(ssml_outline):
        return jsonify({'error': 'The SSML content is not valid.'}), 400

    # Count the number of <voice> elements
    voice_count = len(re.findall(r'<voice name=".*?">', ssml_outline))
    print("Number of Voices:", voice_count)
    if voice_count > 50:
        ssml_chunks = split_ssml(ssml_outline, max_voice_elements=50)
        print(f"Chunks created: {len(ssml_chunks)}")
    else:
        ssml_chunks = [ssml_outline]

    if not ssml_chunks:
        return jsonify({'error': 'Failed to create SSML chunks.'}), 500

    audio_files = []
    unique_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    blob_url = None  # Initialize 'blob_url'

    # Speech configuration
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)

    for idx, ssml_chunk in enumerate(ssml_chunks):
        file_name = f'output_{unique_id}_{idx}.wav'
        file_path = f'/tmp/{file_name}'  # Temporary directory

        # Generate audio for each SSML chunk
        if not generate_speech(ssml_chunk, file_path, speech_config):
            return jsonify({'error': f'Error generating the audio for chunk {idx+1}.'}), 500

        # Verify that the file exists
        if not os.path.exists(file_path):
            print(f"Error: The file at {file_path} does not exist.")
            return jsonify({'error': f'The file at {file_path} does not exist.'}), 500

        # Upload the file to Azure Blob Storage
        try:
            blob_url = upload_to_blob_storage(file_name, file_path)
            audio_files.append(file_path)  # Keep local paths for combining
        except Exception as e:
            return jsonify({'error': f'Error uploading audio to Azure Blob Storage: {e}'}), 500

    # Combine audio files if there are multiple chunks
    if len(audio_files) > 1:
        combined_file_name = f'combined_output_{unique_id}.wav'
        combined_file_path = f'/tmp/{combined_file_name}'
        try:
            combine_audio_files(audio_files, combined_file_path)
            combined_blob_url = upload_to_blob_storage(combined_file_name, combined_file_path)
        except Exception as e:
            return jsonify({'error': f'Error uploading combined audio to Azure Blob Storage: {e}'}), 500

        # Clean up temporary files
        for file in audio_files:
            os.remove(file)
        os.remove(combined_file_path)

        return jsonify({'audio_file': combined_blob_url})
    else:
        if blob_url:
            return jsonify({'audio_file': blob_url})
        else:
            return jsonify({'error': 'No audio was generated.'}), 500

if __name__ == '__main__':
    if not os.path.exists('audio_output'):
        os.makedirs('audio_output')
    app.run(debug=True)