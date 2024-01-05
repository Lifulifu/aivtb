from fastapi import APIRouter
from publish_pipeline import publish_pipeline, PublishRequest

router = APIRouter()

@router.post('/publish_message')
def publish_message(req: PublishRequest):
    publish_pipeline.submit(req)