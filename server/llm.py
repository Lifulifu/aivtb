from openai import AsyncOpenAI
from typing import AsyncGenerator, Sequence, Optional
import os
from dotenv import load_dotenv
from emoji import EMOJI_DATA
from typing import List

load_dotenv()
api_key = os.getenv("OPENAI_KEY")
client = AsyncOpenAI(api_key=api_key)

async def get_llm_text_stream(messages: Sequence, temperature: float = 0.7) -> AsyncGenerator:
    res = await client.chat.completions.create(
        model="ft:gpt-3.5-turbo-0613:personal::8OQWuY8G",
        messages=messages,
        temperature=temperature,
        max_tokens=1000,
        stream=True
    )
    async for piece in res:
        yield piece.choices[0].delta.content or ''

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
    targets = ['<instruction>', '<context>']
    for target in targets:
        text = text.replace(target, '')
    return text

def have_prefix(text: str):
    targets = ['<instruction>', '<context>']
    for target in targets:
        if target in text: return True
    return False

def add_punctuation(text: str):
    text = add_target_after_consecutive_group(text, '。', '～')
    text = add_target_after_consecutive_group(text, '。', EMOJI_DATA)
    return text

def construct_message(messages: List, prompt: object):
    return [
        {"role": "system", "content": prompt['system']},
        {"role": "system", "content": prompt['character']},
        *messages
    ]

if __name__ == '__main__':
    pass