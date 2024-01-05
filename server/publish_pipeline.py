from pydantic import BaseModel
from textgen import to_chunks, add_punctuation, remove_prefix, have_prefix
from audiogen import get_azure_tts_audio
from play import play_wav
from pipeline import Pipeline, PipelineStage
from typing import Any

TEXT_CHUNK_MIN_LEN = 20

class PublishRequest(BaseModel):
    q: str
    a: str
    device: int = -1

class TTSRequest(BaseModel):
    original: str
    processed: str
    device: int = -1

class PlayRequest(BaseModel):
    audio: Any
    device: int = -1

def preprocess_text_stage(req: PublishRequest) -> TTSRequest:
    original = []
    processed = []

    # speak question only if it is player message
    if not have_prefix(req.q):
        chunks = to_chunks(remove_prefix(req.q), min_len=TEXT_CHUNK_MIN_LEN)
        original.extend(chunks)
        processed.extend(
            list(map(lambda chunk: add_punctuation(chunk), chunks)))

    chunks = to_chunks(req.a, min_len=TEXT_CHUNK_MIN_LEN)
    original.extend(chunks)
    processed.extend(
        list(map(lambda chunk: add_punctuation(chunk), chunks)))

    for ori_chunk, proc_chunk in zip(original, processed):
        yield TTSRequest(original=ori_chunk, processed=proc_chunk, device=req.device)

def tts_stage(req: TTSRequest):
    audio = get_azure_tts_audio(req.processed)
    return PlayRequest(audio=audio, device=req.device)

def play_stage(req: PlayRequest):
    play_wav(req.audio, req.device)

# input: PublishRequest
# output: None, but play audio
publish_pipeline = Pipeline([
    PipelineStage(run=preprocess_text_stage),
    PipelineStage(run=tts_stage),
    PipelineStage(run=play_stage)
])
publish_pipeline.start()