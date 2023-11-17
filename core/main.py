from llm import get_llm_text_stream, to_chunks
# from tts import get_tts_audio_stream, play_speech
from pipeline import Pipeline
from functools import partial
from typing import List
import yaml


def logger(text: str):
    print(text)
    return text

def construct_message(message: str, prompt: object):
    return [
        {"role": "system", "content": prompt['system']},
        {"role": "user", "content": prompt['character']},
        {"role": "assistant", "content": "Confirmed."},
        {"role": "user", "content": message}
    ]

def run_pipeline(message: str, config: object):
    text_stream = get_llm_text_stream(construct_message(message, prompt=config['prompt']))
    text_chunked = to_chunks(text_stream, min_len=50)

    pipeline = Pipeline(
        input_generator=text_chunked,
        stages=[logger, get_tts_audio_stream, play_speech]
    )
    return pipeline.run()

def test_tts(text: str):
    audio = get_tts_audio_stream(text)
    play_speech(audio)

if __name__ == '__main__':
    def logger(text, context):
        print(text, context)
    pipeline = Pipeline([logger])

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    message = '<instruction>雜談'
    text_stream = get_llm_text_stream(construct_message(message, prompt=config['prompt']))
    chunks = to_chunks(text_stream, min_len=50)
    pipeline.run(chunks, context={"message": message})