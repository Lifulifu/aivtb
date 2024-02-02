import pyaudio
from azure.cognitiveservices.speech import AudioDataStream
import wave
import tempfile
import os

def get_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    result = []
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
            result.append({
                'id': i,
                'name': p.get_device_info_by_host_api_device_index(0, i).get('name')
            })
    p.terminate()
    return result

def get_device_name(id: int):
    p = pyaudio.PyAudio()
    if (p.get_device_info_by_host_api_device_index(0, id).get('maxOutputChannels')) > 0:
        return p.get_device_info_by_host_api_device_index(0, id).get('name')
    return None

def play_audio_data_stream(stream: AudioDataStream, device_index: int):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    stream.save_to_wav_file(temp_file.name)

    # Open the temporary file as a .wav file
    wf = wave.open(temp_file, 'rb')
    p = pyaudio.PyAudio()
    pyaudio_stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True,
        output_device_index=device_index)

    # Read and play the .wav file
    data = wf.readframes(1024)
    while data:
        pyaudio_stream.write(data)
        data = wf.readframes(1024)

    temp_file.close()
    os.remove(temp_file.name)

    pyaudio_stream.stop_stream()
    pyaudio_stream.close()
    p.terminate()


if __name__ == "__main__":
    print(get_devices())