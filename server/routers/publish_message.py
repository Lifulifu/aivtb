from fastapi import APIRouter
from textgen import have_prefix, to_chunks, add_punctuation, remove_prefix
from publish_pipeline import publish_pipeline, PublishRequest

router = APIRouter()

@router.post('/publish_message')
async def publish_message(req: PublishRequest):
    publish_pipeline.submit(req)