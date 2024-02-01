from pydantic import BaseModel
from textgen import to_chunks, add_punctuation, remove_prefix, have_prefix
from audiogen import get_azure_tts_audio
from play import play_audio_data_stream
from utils.pipeline import Pipeline, PipelineStage
from typing import Any, Optional
import config
from utils.util import Timer

TEXT_CHUNK_MIN_LEN = 20

class PublishRequest(BaseModel):
    q: str
    q_voice: Optional[str] = config.voice['q']['voiceName']
    q_device: Optional[int] = config.voice['q']['device']
    a: str
    a_voice: Optional[str] = config.voice['a']['voiceName']
    a_device: Optional[int] = config.voice['a']['device']

class TTSRequest(BaseModel):
    original: str
    processed: str
    voice: str
    device: int = -1

class PlayRequest(BaseModel):
    text: str
    audio: Any # actually AudioDataStream
    device: int = -1

def preprocess_text_stage(req: PublishRequest) -> TTSRequest:

    def preprocess_chunk(chunk: str):
        return add_punctuation(chunk)

    # q
    # speak only if it is player message, not a system message with prefix.
    if len(req.q) > 0 and not have_prefix(req.q):
        original = to_chunks(remove_prefix(req.q), min_len=TEXT_CHUNK_MIN_LEN)
        processed = list(map(preprocess_chunk, original))
        for ori_chunk, proc_chunk in zip(original, processed):
            yield TTSRequest(original=ori_chunk, processed=proc_chunk, device=req.q_device, voice=req.q_voice)

    # a
    original = to_chunks(req.a, min_len=TEXT_CHUNK_MIN_LEN)
    processed = list(map(preprocess_chunk, original))
    for ori_chunk, proc_chunk in zip(original, processed):
        yield TTSRequest(original=ori_chunk, processed=proc_chunk, device=req.a_device, voice=req.a_voice)

def tts_stage(req: TTSRequest):
    with Timer('fetch'):
        audio = get_azure_tts_audio(req.processed, req.voice, rate=1.1)
    return PlayRequest(text=req.original, audio=audio, device=req.device)

def play_stage(req: PlayRequest):
    with Timer('play'):
        play_audio_data_stream(req.audio, req.device)

# input: PublishRequest
# output: None, but play audio
publish_pipeline = Pipeline([
    PipelineStage(run=preprocess_text_stage),
    PipelineStage(run=tts_stage),
    PipelineStage(run=play_stage)
])
publish_pipeline.start()