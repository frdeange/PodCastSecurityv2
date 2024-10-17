'''
  For more samples please visit https://github.com/Azure-Samples/cognitive-services-speech-sdk 
'''

import azure.cognitiveservices.speech as speechsdk

# Creates an instance of a speech config with specified subscription key and service region.
speech_key = "956db3b440d94446b496b7a99ec2e6db"
service_region = "swedencentral"

Speaker1_Voice = "es-ES-TristanMultilingualNeural"
Speaker2_Voice = "es-ES-XimenaMultilingualNeural" 

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
# Note: the voice setting will not overwrite the voice element in input SSML.
speech_config.speech_synthesis_voice_name = "de-DE-FlorianMultilingualNeural"

text = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-ES">
<voice name="es-ES-EliasNeural">
    <prosody rate="medium">Bienvenidos a nuestro Podcast. Vamos a explorar el apasionante mundo de los incentivos de Microsoft. Hoy, tenemos a un invitado especial.</prosody>
  </voice>
  <voice name="en-US-JennyMultilingualNeural">
    <prosody pitch="high" rate="medium">Está todo súper revuelto fuera con este tema eh?</prosody>
  </voice>
  <voice name="en-US-AndrewMultilingualNeural">
    <prosody rate="medium">Eso es, así que estás preparado para conocer más de este mundo de los incentivos</prosody>
  </voice>
  <voice name="en-US-JennyMultilingualNeural">
    <prosody rate="medium">Si, es apasionante porque es mucho más que sólo un tema de reconocimiento</prosody>
  </voice>  
</speak>
"""

# use the default speaker as audio output.
audio_config = speechsdk.audio.AudioOutputConfig(filename="output.wav")
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)




result = speech_synthesizer.speak_ssml_async(text).get()
# Check result
if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("Speech synthesized for text [{}]".format(text))
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = result.cancellation_details
    print("Speech synthesis canceled: {}".format(cancellation_details.reason))
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        print("Error details: {}".format(cancellation_details.error_details))

