from pydantic import BaseModel
from textgen import to_chunks, add_punctuation, remove_prefix, have_prefix
from audiogen import get_azure_tts_audio
from play import play_audio_data_stream
from utils.pipeline import Pipeline, PipelineStage
from typing import Any, Optional
import config
from utils.util import Timer
import time

TEXT_CHUNK_MIN_LEN = 20
QA_TIMEOUT_S = 5


class PublishRequest(BaseModel):
    text: str
    role: str
    device: Optional[int] = config.voice["device"]
    voice: Optional[str] = config.voice["name"]
    rate: float = config.voice["rate"]


class TTSRequest(BaseModel):
    role: str
    original: str
    processed: str
    voice: str
    device: int = -1
    rate: float = 1.0
    is_last: bool = True


class PlayRequest(BaseModel):
    role: str
    text: str
    audio: Any  # actually AudioDataStream
    device: int = -1
    is_last: bool = True


def preprocess_text_stage(req: PublishRequest) -> TTSRequest:

    def preprocess_chunk(chunk: str):
        return add_punctuation(chunk)

    # Abort if text is empty or has prefix
    if len(req.text) == 0 or have_prefix(req.text):
        return None
    original = to_chunks(req.text, min_len=TEXT_CHUNK_MIN_LEN)
    processed = list(map(preprocess_chunk, original))
    for i, (ori_chunk, proc_chunk) in enumerate(zip(original, processed)):
        is_last = i == len(original) - 1
        yield TTSRequest(
            original=ori_chunk,
            processed=proc_chunk,
            is_last=is_last,
            role=req.role,
            device=req.device,
            voice=req.voice,
            rate=req.rate,
        )


def tts_stage(req: TTSRequest):
    with Timer("fetch"):
        audio = get_azure_tts_audio(req.processed, req.voice, rate=req.rate)
    return PlayRequest(
        audio=audio,
        text=req.original,
        role=req.role,
        device=req.device,
        is_last=req.is_last,
    )


def play_stage(req: PlayRequest):
    with Timer("play"):
        play_audio_data_stream(req.audio, req.device)
    if req.role == "assistant" and req.is_last:
        time.sleep(QA_TIMEOUT_S)
    return "done"  # Must return something other than None to send the on:end event


# input: PublishRequest
# output: None, but play audio
publish_pipeline = Pipeline(
    [
        PipelineStage(run=preprocess_text_stage),
        PipelineStage(run=tts_stage),
        PipelineStage(run=play_stage),
    ]
)
publish_pipeline.start()
