from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ''
    MERCHANT_UPI_ID: str = 'forvyn-ai@upi'
    MERCHANT_NAME: str = 'Forvyn AI Billing'
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env', env_file_encoding='utf-8')
settings = Settings()