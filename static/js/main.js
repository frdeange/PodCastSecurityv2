// Show loading indicator when a form is submitted
function showLoadingIndicator() {
    document.getElementById('loading-indicator').style.display = 'block';
}

// Hide loading indicator when the form submission is complete
function hideLoadingIndicator() {
    document.getElementById('loading-indicator').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('.btn').addEventListener('click', extractTextFromPdf);
});

function extractTextFromPdf() {
    var files = document.getElementById('pdf-files').files;
    if (files.length === 0) {
        alert('Please select at least one PDF file.');
        return;
    }

    var formData = new FormData();
    for (var i = 0; i < files.length; i++) {
        formData.append('pdf-files', files[i]);
    }

    showLoadingIndicator();
    fetch('/extract_text_from_pdf', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingIndicator();
        if (data.text) {
            document.getElementById('podcast-content').value = data.text;
        } else {
            alert('Error Extracting text from PDF.');
        }
    })
    .catch(error => {
        hideLoadingIndicator();
        alert('Error Extracting text from PDF. ' + error);
    });
}

function extractTextFromWebsite() {
    var websiteUrl = document.getElementById('website-url').value;
    if (!websiteUrl) {
        alert('Please, insert a correct url, including http:// or https://');
        return;
    }
    showLoadingIndicator();
    fetch('/extract_text_from_website', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'website-url=' + encodeURIComponent(websiteUrl)
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingIndicator();
        if (data.text) {
            document.getElementById('podcast-content').value = data.text;
        } else {
            alert('Error extracting text from URL.');
        }
    })
    .catch(error => {
        hideLoadingIndicator();
        alert('Error extracting text from URL: ' + error);
    });
}

function generateOutline() {
    var content = document.getElementById('podcast-content').value;
    var language = document.getElementById('language').value;

    if (!content) {
        alert('Please provide a content to generate the podcast script.');
        return;
    }
    showLoadingIndicator();
    fetch('/generate_outline', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'content=' + encodeURIComponent(content) + '&language=' + encodeURIComponent(language)
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingIndicator();
        if (data.outline) {
            document.getElementById('conversation-outline').value = data.outline;
        } else {
            alert('Error Creating the schema.');
        }
    })
    .catch(error => {
        hideLoadingIndicator();
        alert('Fail creating schema: ' + error);
    });
}

function generateAudio() {
    var outline = document.getElementById('conversation-outline').value;
    var speaker1 = document.getElementById('speaker1').value;
    var speaker2 = document.getElementById('speaker2').value;

    if (!outline) {
        alert('Please provide the XML script to create the audio.');
        return;
    }

    if (!speaker1 || !speaker2) {
        alert('Please, you have to choose the speakers voices for the podcast.');
        return;
    }

    showLoadingIndicator();
    fetch('/generate_audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'outline=' + encodeURIComponent(outline) + '&speaker1=' + encodeURIComponent(speaker1) + '&speaker2=' + encodeURIComponent(speaker2)
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingIndicator();
        if (data.error) {
            alert('Error Creating the audio: ' + data.error);
        } else if (data.audio_file) {
            var audioUrl = data.audio_file;
            var audioElement = document.createElement('audio');
            audioElement.controls = true;
            audioElement.src = audioUrl;
            var audioPlayerDiv = document.getElementById('audio-player');
            audioPlayerDiv.innerHTML = ''; // Clean Previous Audio
            audioPlayerDiv.appendChild(audioElement);
        } else {
            alert('Unknown error creating the audio.');
        }
    })
    .catch(error => {
        hideLoadingIndicator();
        alert('Error creating the audio: ' + error);
    });
}
