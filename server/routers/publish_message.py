from fastapi import APIRouter
from pydantic import BaseModel
from publish_pipeline import publish_pipeline, PublishRequest
from play import get_devices

router = APIRouter()

@router.post('/publish_message')
def publish_message(req: PublishRequest):
    print(req.dict())
    publish_pipeline.submit(req)

@router.get('/publish_abort')
def publish_abort():
    publish_pipeline.abort()

class AudioDevice(BaseModel):
    id: int
    name: str

@router.get('/audio_devices')
def audio_devices() -> list[AudioDevice]:
    return get_devices()