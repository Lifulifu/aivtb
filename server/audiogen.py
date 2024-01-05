import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream
from play import get_device_name
import os
from dotenv import load_dotenv

load_dotenv()
speech_key = os.getenv("SPEECH_KEY")
service_region = os.getenv("SPEECH_REGION")
temp_dir = '.temp/'
os.makedirs(temp_dir, exist_ok=True)

default_playback_device_id = int(os.getenv("DEFAULT_PLAYBACK_DEVICE_ID"))
print('default playback device is "', get_device_name(default_playback_device_id), '"')

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"

def get_azure_tts_audio(text: str):
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = speech_synthesizer.speak_text_async(text).get()
    return AudioDataStream(result)