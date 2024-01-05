from pipeline import Pipeline, PipelineStage
from textgen import get_llm_text_stream, construct_message
import config
from pydantic import BaseModel

class TextgenRequest(BaseModel):
    messages: list[dict[str, str]]
    temperature: float

def textgen_stage(req: TextgenRequest):
    text_stream = get_llm_text_stream(
        construct_message(req.messages, prompt=config.prompt),
        temperature=req.temperature)
    accum = ''
    for piece in text_stream:
        accum += piece
        yield [ *req.messages, {"role": "assistant", "content": accum} ]

# input: messages and temperature
# output: messages with incremental text
textgen_pipeline = Pipeline([
    PipelineStage(run=textgen_stage),
])
textgen_pipeline.start()