import openai
from typing import Generator, Sequence, Optional
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_KEY")
openai.api_key = api_key

def get_llm_text_stream(text: str) -> str:
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": text}
        ],
        stream=True
    )
    return res

def to_chunks(gen: Generator, min_len: int = 0, separator: str | Sequence[str] = ('，', '。', ',', '.', '\n')):
    if isinstance(separator, str): separator = (separator,)
    chunk = ''
    for piece in gen:
        try:
            piece = piece['choices'][0]['delta']['content']
        except:
            piece = ''

        for char in piece:
            chunk += char
            if char in separator:
                if len(chunk) < min_len: continue
                yield chunk
                chunk = ''
    if len(chunk) > 0: yield chunk
    return



