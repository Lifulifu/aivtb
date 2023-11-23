from openai import AsyncOpenAI
from typing import AsyncGenerator, Sequence, Optional
import os
from dotenv import load_dotenv
from emoji import EMOJI_DATA

load_dotenv()
api_key = os.getenv("OPENAI_KEY")
client = AsyncOpenAI(api_key=api_key)

async def get_llm_text_stream(messages: Sequence, temperature: float = 0.7) -> AsyncGenerator:
    res = await client.chat.completions.create(
        model="ft:gpt-3.5-turbo-1106:personal::8Lp6MxIS",
        messages=messages,
        temperature=temperature,
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

def to_chunks(text: str, min_len: int = 0, separator: str | Sequence[str] = ('。', '，', '！', '～', '\n')):
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
    return chunks

def add_target_after_consecutive_group(inp: str, target: str, group: Sequence):
    if inp == '': return ''
    result = ''
    for i in range(len(inp)):
        result += inp[i]
        if inp[i] in group and (i == len(inp)-1 or inp[i+1] not in group):
            result += target
    return result

def remove_prefix(text: str):
    targets = ['<instruction>', '<player>']
    for target in targets:
        text = text.replace(target, '')
    return text

def add_punctuation(text: str):
    text = add_target_after_consecutive_group(text, '。', '～')
    text = add_target_after_consecutive_group(text, '。', EMOJI_DATA)
    return text

def construct_message(message: str, prompt: object):
    return [
        {"role": "system", "content": prompt['system']},
        {"role": "user", "content": prompt['character']},
        {"role": "assistant", "content": "Confirmed."},
        {"role": "user", "content": message}
    ]

if __name__ == '__main__':
    pass