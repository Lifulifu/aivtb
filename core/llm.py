from openai import OpenAI
from typing import Generator, Sequence, Optional
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=api_key)

def get_llm_text_stream(messages: Sequence) -> str:
    res = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-1106:personal::8KTEQksW",
        # model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.6,
        max_tokens=500,
        stream=True
    )
    return res

def to_chunks(gen: Generator, min_len: int = 0, separator: str | Sequence[str] = ('，', '。', ',', '.', '\n')):
    if isinstance(separator, str): separator = (separator,)
    chunk = ''
    for piece in gen:
        piece = piece.choices[0].delta.content or ''

        for char in piece:
            chunk += char
            if char in separator:
                if len(chunk) < min_len: continue
                yield chunk
                chunk = ''
    if len(chunk) > 0: yield chunk
    return



