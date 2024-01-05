import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream
from play import get_device_name
import wave
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
    audio = AudioDataStream(result)
    temp_file_path = os.path.join(temp_dir, '_speech.wav')
    audio.save_to_wav_file(temp_file_path)
    return wave.open(temp_file_path, 'rb')

# openai_api_key = os.getenv("OPENAI_KEY")
# client = AsyncOpenAI(api_key=openai_api_key)

# async def get_openai_tts_audio(text: str):
#     response = await client.audio.speech.create(
#         model="tts-1",
#         voice="alloy",
#         input=text,
#     )
#     return response

# async def play_openai_speech(audio, device_id: int):
#     temp_file_path = os.path.join(temp_dir, '_speech.mp3')
#     await audio.astream_to_file(temp_file_path)
#     device_id = default_playback_device_id if device_id == -1 else int(device_id)
#     await play_mp3(temp_file_path, device_id)