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
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = speech_synthesizer.speak_text_async(text).get()
    return AudioDataStream(result)

def play_speech(stream: AudioDataStream):
    buffer = bytearray()
    buffer_size = 2048 # data chunk size, can be arbitrary
    while stream.can_read_data(buffer_size):
        temp_buffer = bytes(buffer_size)
        filled_size = stream.read_data(temp_buffer)
        buffer.extend(temp_buffer[:filled_size])

    audio_segment = AudioSegment.from_mp3(io.BytesIO(buffer))
    play(audio_segment)