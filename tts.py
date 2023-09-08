import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
load_dotenv()

speech_key = os.getenv("SPEECH_KEY")
service_region = os.getenv("SPEECH_REGION")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"

def run_tts(text: str):
    # use default speaker as audio output.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = speech_synthesizer.speak_text_async(text).get()
    return result