import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream
from pydub import AudioSegment
from pydub.playback import play
import io
import os
from dotenv import load_dotenv

load_dotenv()
speech_key = os.getenv("SPEECH_KEY")
service_region = os.getenv("SPEECH_REGION")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"

def get_tts_audio_stream(text: str):
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = speech_synthesizer.speak_text_async(text).get()
    return AudioDataStream(result)

def play_speech(stream: AudioDataStream):
    temp_dir = '.temp/'
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, '_speech.wav')
    stream.save_to_wav_file(temp_file_path)
    audio_segment = AudioSegment.from_wav(temp_file_path)
    play(audio_segment)