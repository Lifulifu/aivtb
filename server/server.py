from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import send_message, preview_message, publish_message, subtitle, yt_comments

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(send_message.router)
app.include_router(preview_message.router)
app.include_router(publish_message.router)
app.include_router(subtitle.router)
app.include_router(yt_comments.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print('server shutdown')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", port=8000, host="0.0.0.0", log_level="info", lifespan="on")