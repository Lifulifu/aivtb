import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream
import os
import xml.sax.saxutils as saxutils
from dotenv import load_dotenv
from play import play_audio_data_stream

load_dotenv()
speech_key = os.getenv("SPEECH_KEY")
service_region = os.getenv("SPEECH_REGION")
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

def get_azure_tts_audio(text: str, voice: str, rate: float = 1, pitch: str = 'medium'):
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    ssml = to_ssml(text, voice, rate, pitch)
    result = speech_synthesizer.speak_ssml_async(ssml).get()
    return AudioDataStream(result)

def to_ssml(text: str, voice: str, rate: float = 1, pitch: str = 'medium'):
    return f'''
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-TW">
    <voice name="{voice}">
        <prosody rate="{rate}" pitch="{pitch}">
            {saxutils.escape(text)}
        </prosody>
    </voice>
</speak>
'''

if __name__ == "__main__":
    text = '''這個男人太狠了'''
    audio = get_azure_tts_audio(text, voice="zh-TW-YunJheNeural", rate=1, pitch='+0%')
    # audio.save_to_wav_file("test.wav")
    play_audio_data_stream(audio, 1)