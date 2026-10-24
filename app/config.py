
import os
import certifi
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

ssl_cert = os.environ.get("SSL_CERT_FILE")
if not ssl_cert or not os.path.exists(ssl_cert):
    os.environ["SSL_CERT_FILE"] = certifi.where()


class Settings(BaseSettings):
    openai_api_key: str = ""
    pinecone_api_key: str = ""
    gemini_api_key: str = ""
    tavily_api_key: str = ""
    pinecone_index: str = "medical-agent-demo"
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embed_model: str = "text-embedding-3-small"
    openai_vision_model: str = "gpt-4.1-mini"
    api_token: str = ""
    allowed_origins: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
