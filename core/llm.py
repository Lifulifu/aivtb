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

async def to_chunks(gen: AsyncGenerator, min_len: int = 0, separator: str | Sequence[str] = ('，', '。', ',', '.', '\n')):
    if isinstance(separator, str): separator = (separator,)
    chunk = ''
    async for piece in gen:
        for char in piece:
            chunk += char
            if char in separator:
                if len(chunk) < min_len: continue
                yield chunk
                chunk = ''
    if len(chunk) > 0: yield chunk
    return



