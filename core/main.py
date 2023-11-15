from llm import get_llm_text_stream, to_chunks
from tts import get_tts_audio_stream, play_speech
from pipeline import Pipeline
import yaml

with open('data/lumi_v0/prompt.yaml', 'r') as f:
    prompt = yaml.safe_load(f)

def logger(text: str):
    print(text)
    return text

def construct_message(message: str):
    return [
        {"role": "system", "content": prompt['system']},
        {"role": "user", "content": prompt['character']},
        {"role": "assistant", "content": "Confirmed."},
        {"role": "user", "content": message}
    ]

def run_pipeline(message: str):
    text_stream = get_llm_text_stream(construct_message(message))
    text_chunked = to_chunks(text_stream, min_len=50)

    pipeline = Pipeline(
        input_generator=text_chunked,
        stages=[logger, get_tts_audio_stream, play_speech]
    )
    pipeline.run()

def test_llm(message: str):
    text_stream = get_llm_text_stream(construct_message(message))
    text_chunked = to_chunks(text_stream, min_len=50)

    pipeline = Pipeline(
        input_generator=text_chunked,
        stages=[logger]
    )
    pipeline.run()


def test_tts(text: str):
    audio = get_tts_audio_stream(text)
    play_speech(audio)

if __name__ == '__main__':
    test_llm('你是誰')