# Podcast Generator

Podcast Generator is a web application that allows users to extract text from a document in PDF or website, generate a podcast conversation outline using Azure OpenAI's GPT-4o (current model), and convert the outline into an audio file using Azure Cognitive Services.

## Features

- Extract text from a given PDF or Website
- Generate a podcast conversation outline between two speakers discussing the extracted content.
- Allow users to edit the generated outline before converting it to audio.
- Convert the edited outline to an audio file using Azure Speech Service
- Save the generated audio file with a unique timestamp and allow user to download it

## Requirements

- Python 3.9 or higher
- Flask
- Requests
- BeautifulSoup4
- OpenAI Python client
- Azure Cognitive Services Speech SDK

Also, your running machine needs to have installed ffmpeg, so to avoid problems, is recommended to run in DevContainers


## USE DEV CONTAINER

This repo contains the devContainer config to run it correctly without any inconvenience, as

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/frdeange/PodCastSecurityv2.git
    cd PodCastSecurityv2
    ```

2. Create a virtual environment and activate it:

    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required packages:

    ```sh
    pip install -r requirements.txt
    ```

4. Set up your environment variables for OpenAI and Azure Cognitive Services:

Its recommended to create a .env files on your project root that contains at least the following fields:

AZURE_OPENAI_TYPE="azure"
AZURE_OPENAI_KEY="YOUR KEY"
AZURE_OPENAI_ENDPOINT="YOUR ENDPOINT FINISHING WITH /"
AZURE_OPENAI_API_VERSION="YOUR API VERSION"
AZURE_OPENAI_ENGINE="THE NAME OF YOUR IMPLEMENTATION"
AZURE_FORM_RECOGNIZER_KEY="THE FORM RECOGNIZER KEY"
AZURE_FORM_RECOGNIZER_ENDPOINT="YOUR FORM RECOGNIZER ENDPOINT"
AZURE_SPEECH_KEY="YOUR SPEECH SERVICE KEY"  
AZURE_SPEECH_REGION="YOUR SPEECH SERVICE REGIO"

## Usage

1. Run the Flask application:

    ```sh
    python app.py
    ```

2. Open your web browser and go to `http://127.0.0.1:5000`.

3. Use the web interface to:
    - Extract text from a website by providing the URL or uploading a .pdf file
    - Generate a podcast conversation outline.
    - Edit the generated outline if necessary.
    - Convert the outline to an audio file.


## API Endpoints

- `POST /extract_text_from_website`: Extract text from a given website URL.
    - Request: `website-url` (form data)
    - Response: JSON with extracted text

- `POST /generate_outline`: Generate a podcast conversation outline.
    - Request: `content` (form data)
    - Response: JSON with generated outline

- `POST /generate_audio`: Convert the edited outline to an audio file.
    - Request: `ssml_content` (form data)
    - Response: JSON with the path to the generated audio file

- `GET /audio/<filename>`: Retrieve the generated audio file.
    - Request: `filename` (URL parameter)
    - Response: Audio file

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
