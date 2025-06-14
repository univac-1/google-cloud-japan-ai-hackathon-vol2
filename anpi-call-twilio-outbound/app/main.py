import logging.config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.websocket_controller import router as websocket_router
from app.config import LOGGING_CONFIG
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)

app = FastAPI(title="高齢者見守りAIシステム")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket_router)

@app.get("/")
async def root():
    return {"message": "高齢者見守りAIシステムが起動しています"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}