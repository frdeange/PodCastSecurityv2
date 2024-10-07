function extractTextFromPdf() {  
    var formData = new FormData(document.getElementById('pdf-form'));  
    fetch('/extract_text_from_pdf', {  
        method: 'POST',  
        body: formData  
    })  
    .then(response => response.json())  
    .then(data => {  
        document.getElementById('podcast-content').value = data.text;  
    });  
}  
  
function extractTextFromWebsite() {  
    var formData = new FormData(document.getElementById('website-form'));  
    fetch('/extract_text_from_website', {  
        method: 'POST',  
        body: formData  
    })  
    .then(response => response.json())  
    .then(data => {  
        document.getElementById('podcast-content').value = data.text;  
    });  
}  
  
function generateOutline() {  
    var content = document.getElementById('podcast-content').value;  
    fetch('/generate_outline', {  
        method: 'POST',  
        headers: {  
            'Content-Type': 'application/x-www-form-urlencoded',  
        },  
        body: 'content=' + encodeURIComponent(content)  
    })  
    .then(response => response.json())  
    .then(data => {  
        document.getElementById('conversation-outline').value = data.outline;  
    });  
}  
  
function generateAudio() {  
    var outline = document.getElementById('conversation-outline').value;  
    var speaker1 = document.getElementById('speaker1').value;  
    var speaker2 = document.getElementById('speaker2').value;  
    fetch('/generate_audio', {  
        method: 'POST',  
        headers: {  
            'Content-Type': 'application/x-www-form-urlencoded',  
        },  
        body: 'outline=' + encodeURIComponent(outline) + '&speaker1=' + encodeURIComponent(speaker1) + '&speaker2=' + encodeURIComponent(speaker2)  
    })  
    .then(response => response.json())  
    .then(data => {  
        window.location.href = data.audio_file;  
    });  
}  
