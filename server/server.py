from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import send_message, preview_message

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print('server shutdown')