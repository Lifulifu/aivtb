from openai import AsyncOpenAI
from typing import AsyncGenerator, Sequence, Optional
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_KEY")
client = AsyncOpenAI(api_key=api_key)

async def get_llm_text_stream(messages: Sequence) -> AsyncGenerator:
    res = await client.chat.completions.create(
        model="ft:gpt-3.5-turbo-1106:personal::8LF3ausT",
        # model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.6,
        max_tokens=500,
        stream=True
    )
    async for piece in res:
        yield piece.choices[0].delta.content or ''

class ChunkCollector():
    def __init__(self, min_len: int = 0, separator: str | Sequence[str] = ('，', '。', ',', '.', '\n')):
        self.separator = (separator,) if isinstance(separator, str) else separator
        self.min_len = min_len
        self.chunk = ''

    def collect(self, piece: str):
        for char in piece:
            self.chunk += char
            if char in self.separator:
                if len(self.chunk) >= self.min_len:
                    chunk = self.chunk
                    self.chunk = ''
                    return chunk
        return None

    def remain_chunk(self):
        return len(self.chunk) > 0

def to_chunks(text: str, min_len: int = 0, separator: str | Sequence[str] = ('，', '。', ',', '.', '\n')):
    chunks = []
    chunk = ''
    for char in text:
        chunk += char
        if char in separator:
            if len(chunk) < min_len: continue
            chunks.append(chunk)
            chunk = ''
    if len(chunk) > 0:
        chunks.append(chunk)



