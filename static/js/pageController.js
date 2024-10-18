// Update the available voices based on the selected language
function updateVoiceOptions() {
    const language = document.getElementById('language').value;
    const speaker1 = document.getElementById('speaker1');
    const speaker2 = document.getElementById('speaker2');
    let options = '';

    switch (language) {
        case 'en-US':
            options = `
                <option value="en-US-AvaMultilingualNeural">Ava</option>
                <option value="en-US-AndrewMultilingualNeural">Andrew</option>
                <option value="en-US-EmmaMultilingualNeural">Emma</option>
                <option value="en-US-BrianMultilingualNeural">Brian</option>
            `;
            break;
        case 'de-DE':
            options = `
                <option value="de-DE-FlorianMultilingualNeural">Florian</option>
                <option value="de-DE-SeraphinaMultilingualNeural">Seraphina</option>
            `;
            break;
        case 'fr-FR':
            options = `
                <option value="fr-FR-RemyMultilingualNeural">Remy</option>
                <option value="fr-FR-VivienneMultilingualNeural">Vivienne</option>
            `;
            break;
        case 'it-IT':
            options = `
                <option value="it-IT-ElsaNeural">Elsa</option>
                <option value="it-IT-DiegoNeural">Diego</option>
            `;
            break;
        case 'pt-BR':
            options = `
                <option value="pt-BR-FranciscaNeural">Francisca</option>
                <option value="pt-BR-AntonioNeural">Antonio</option>
            `;
            break;
        case 'es-ES':
            options = `
                <option value="en-US-AvaMultilingualNeural">Ava</option>
                <option value="es-ES-AlvaroNeural">Alvaro</option>
            `;
            break;
        default:
            options = '';
    }

    speaker1.innerHTML = options;
    speaker2.innerHTML = options;

    // Select different default options for speaker1 and speaker2
    if (speaker1.options.length > 0) {
        speaker1.selectedIndex = 0;  // Set speaker1 to the first option
        if (speaker2.options.length > 1) {
            speaker2.selectedIndex = 1;  // Set speaker2 to a different option (second one)
        }
    }

    // Update the voice selection to prevent duplicates
    updateVoiceSelection();
}

// Prevent selecting the same voice for both speakers
function updateVoiceSelection() {
    const speaker1 = document.getElementById('speaker1');
    const speaker2 = document.getElementById('speaker2');

    // Enable all options initially
    Array.from(speaker1.options).forEach(option => option.disabled = false);
    Array.from(speaker2.options).forEach(option => option.disabled = false);

    // Disable the selected option from the other selector
    if (speaker1.value) {
        const selectedValue = speaker1.value;
        Array.from(speaker2.options).forEach(option => {
            if (option.value === selectedValue) {
                option.disabled = true;
            }
        });
    }

    if (speaker2.value) {
        const selectedValue = speaker2.value;
        Array.from(speaker1.options).forEach(option => {
            if (option.value === selectedValue) {
                option.disabled = true;
            }
        });
    }
}

// Initialize voice options on page load
document.addEventListener('DOMContentLoaded', function() {
    updateVoiceOptions();

    // Add event listeners for change in speaker selections
    document.getElementById('speaker1').addEventListener('change', updateVoiceSelection);
    document.getElementById('speaker2').addEventListener('change', updateVoiceSelection);
});
