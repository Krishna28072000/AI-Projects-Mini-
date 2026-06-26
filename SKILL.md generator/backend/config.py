import os 
from pathlib import Path 
from dotenv import load_dotenv 

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR/'.env'

load_dotenv(dotenv_path = ENV_PATH,override = True)

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")

settings = Settings()

if not settings.OPENAI_API_KEY:
    raise ValueError("[.ENV ERROR] OPENAI_API_KEY is missing, kindly check it")
