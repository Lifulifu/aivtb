import pyaudio
import wave
from concurrent.futures import ThreadPoolExecutor
import asyncio
from pydub import AudioSegment
from io import BytesIO

def list_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
            print(i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
    p.terminate()

def get_device_name(id: int):
    p = pyaudio.PyAudio()
    if (p.get_device_info_by_host_api_device_index(0, id).get('maxOutputChannels')) > 0:
        return p.get_device_info_by_host_api_device_index(0, id).get('name')
    return None

executor = ThreadPoolExecutor(max_workers=1)

def play_wav_blocking(stream, wf):
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

async def play_wav(filename, device_index):
    wf = wave.open(filename, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=device_index)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, play_wav_blocking, stream, wf)

    stream.stop_stream()
    stream.close()
    p.terminate()

def play_audio_blocking(stream, audio_segment):
    pcm_data = audio_segment.raw_data
    buffer = BytesIO(pcm_data)
    data = buffer.read(1024)

    while data:
        stream.write(data)
        data = buffer.read(1024)

async def play_mp3(filename, device_index):
    audio_segment = AudioSegment.from_mp3(filename)
    audio_segment = audio_segment.set_frame_rate(44100).set_channels(1).set_sample_width(2)

    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(audio_segment.sample_width),
                    channels=audio_segment.channels,
                    rate=audio_segment.frame_rate,
                    output=True,
                    output_device_index=device_index)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, play_audio_blocking, stream, audio_segment)

    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == "__main__":
    list_devices()