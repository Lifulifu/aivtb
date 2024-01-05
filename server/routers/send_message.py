from fastapi import APIRouter
from aivtb_pipelines import textgen_pipeline, TextgenRequest

router = APIRouter()

@router.post('/send_message')
def send_message(req: TextgenRequest):
    textgen_pipeline.submit(req)
