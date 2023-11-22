import pyaudio
import wave
from concurrent.futures import ThreadPoolExecutor
import asyncio

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


if __name__ == "__main__":
    list_devices()