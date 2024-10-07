// Función para mostrar el indicador de carga
function showLoadingIndicator() {
    document.getElementById('loading-indicator').style.display = 'block';
}

// Función para ocultar el indicador de carga
function hideLoadingIndicator() {
    document.getElementById('loading-indicator').style.display = 'none';
}

function extractTextFromPdf() {
    var formData = new FormData(document.getElementById('pdf-form'));
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
            alert('Error al extraer texto del PDF.');
        }
    })
    .catch(error => {
        hideLoadingIndicator();
        alert('Error al extraer texto del PDF: ' + error);
    });
}

function extractTextFromWebsite() {
    var websiteUrl = document.getElementById('website-url').value;
    if (!websiteUrl) {
        alert('Por favor, ingresa una URL válida.');
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
            alert('Error al extraer texto del sitio web.');
        }
    })
    .catch(error => {
        hideLoadingIndicator();
        alert('Error al extraer texto del sitio web: ' + error);
    });
}

function generateOutline() {
    var content = document.getElementById('podcast-content').value;
    if (!content) {
        alert('Por favor, proporciona contenido para generar el esquema.');
        return;
    }
    showLoadingIndicator();
    fetch('/generate_outline', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'content=' + encodeURIComponent(content)
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingIndicator();
        if (data.outline) {
            document.getElementById('conversation-outline').value = data.outline;
        } else {
            alert('Error al generar el esquema.');
        }
    })
    .catch(error => {
        hideLoadingIndicator();
        alert('Error al generar el esquema: ' + error);
    });
}

function generateAudio() {
    var outline = document.getElementById('conversation-outline').value;
    var speaker1 = document.getElementById('speaker1').value;
    var speaker2 = document.getElementById('speaker2').value;

    if (!outline) {
        alert('Por favor, proporciona el esquema de conversación para generar el audio.');
        return;
    }

    if (!speaker1 || !speaker2) {
        alert('Por favor, selecciona las voces para ambos oradores.');
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
            alert('Error al generar el audio: ' + data.error);
        } else if (data.audio_file) {
            var audioUrl = data.audio_file;
            var audioElement = document.createElement('audio');
            audioElement.controls = true;
            audioElement.src = audioUrl;
            var audioPlayerDiv = document.getElementById('audio-player');
            audioPlayerDiv.innerHTML = ''; // Limpiar reproductores anteriores
            audioPlayerDiv.appendChild(audioElement);
        } else {
            alert('Error desconocido al generar el audio.');
        }
    })
    .catch(error => {
        hideLoadingIndicator();
        alert('Error al generar el audio: ' + error);
    });
}
