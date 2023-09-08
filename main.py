from llm import get_llm_text_stream, to_chunks
from tts import get_tts_audio_stream, play_speech
from pipeline import Pipeline

def main():
    text_stream = get_llm_text_stream("請寫出一段廣告詞推銷Metaverse，盡可能用誇張的語氣和形容詞，並加上emoji。")
    text_chunked = to_chunks(text_stream, min_len=50)

    def logger(text: str):
        print(text)
        return text

    pipeline = Pipeline(
        input_generator=text_chunked,
        stages=[logger, get_tts_audio_stream, play_speech]
    )
    pipeline.run()

main()