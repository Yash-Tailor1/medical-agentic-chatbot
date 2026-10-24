
import base64
import io
import os
import secrets
from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from openai import OpenAI

from app.config import settings
from app.agent import graph


# --------------------------------------------------
# Application setup
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"

STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Medical Agent Educational API",
    version="1.0.0",
    description="Medical education chatbot with image and voice support.",
)

allowed_origins = getattr(settings, "allowed_origins", "*")
if isinstance(allowed_origins, str):
    allowed_origins = [
        origin.strip()
        for origin in allowed_origins.split(",")
        if origin.strip()
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


# --------------------------------------------------
# OpenAI client and model configuration
# --------------------------------------------------

OPENAI_API_KEY = getattr(settings, "openai_api_key", None)

client = (
    OpenAI(api_key=OPENAI_API_KEY, timeout=45)
    if OPENAI_API_KEY
    else None
)

VISION_MODEL = (
    getattr(settings, "openai_vision_model", None)
    or os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
)

TRANSCRIPTION_MODEL = os.getenv(
    "OPENAI_TRANSCRIPTION_MODEL",
    "gpt-4o-mini-transcribe",
)

SPEECH_MODEL = os.getenv(
    "OPENAI_SPEECH_MODEL",
    "gpt-4o-mini-tts",
)

SPEECH_VOICE = os.getenv("OPENAI_SPEECH_VOICE", "alloy")

API_TOKEN = getattr(settings, "api_token", None)


# --------------------------------------------------
# Request models
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[dict[str, str]] = Field(
        default_factory=list,
        max_length=10,
    )
    image_data: str | None = None


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    voice: str | None = None


class ImageRequest(BaseModel):
    image_data: str = Field(min_length=1)
    question: str = Field(
        default="Describe this image and identify any visible medical information.",
        max_length=2000,
    )


# --------------------------------------------------
# Authentication
# --------------------------------------------------

def check_auth(authorization: str | None) -> None:
    if not API_TOKEN:
        return

    expected = f"Bearer {API_TOKEN}"

    if not secrets.compare_digest(authorization or "", expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid API token",
        )


def require_openai() -> OpenAI:
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key is not configured.",
        )
    return client


# --------------------------------------------------
# Image validation
# --------------------------------------------------

def inspect_image_data(data: str) -> tuple[str, bytes]:
    try:
        header, payload = data.split(",", 1)
        mime = header.split(";")[0].split(":", 1)[1]
        raw = base64.b64decode(payload, validate=True)

        if mime not in (
            "image/jpeg",
            "image/png",
            "image/webp",
        ):
            raise ValueError("Only JPEG, PNG, and WebP are supported.")

        if not raw or len(raw) > 5_000_000:
            raise ValueError("Image must be under 5 MB.")

        return mime, raw

    except (ValueError, IndexError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image: {exc}",
        ) from exc


# --------------------------------------------------
# Frontend
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    candidates = [
        TEMPLATES_DIR / "index.html",
        ROOT / "index.html",
        ROOT / "Templates" / "index.html",
    ]

    for html_file in candidates:
        if html_file.is_file():
            return HTMLResponse(
                html_file.read_text(encoding="utf-8")
            )

    raise HTTPException(
        status_code=404,
        detail="index.html was not found. Add it to templates/ or the project root.",
    )


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "openai_configured": bool(OPENAI_API_KEY),
        "agent_loaded": graph is not None,
    }


# --------------------------------------------------
# Chat with LangGraph
# --------------------------------------------------

@app.post("/api/chat")
def chat(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
):
    check_auth(authorization)

    try:
        # Assumes your LangGraph uses a messages-based state.
        from langchain_core.messages import HumanMessage, AIMessage

        messages = []

        # Only accept user and assistant messages from supplied history.
        for item in request.history[-10:]:
            role = item.get("role", "")
            content = item.get("content", "")

            if not isinstance(content, str) or not content.strip():
                continue

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        if request.image_data:
            mime, _ = inspect_image_data(request.image_data)
            image_url = request.image_data

            messages.append(
                HumanMessage(
                    content=[
                        {"type": "text", "text": request.message},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ]
                )
            )
        else:
            messages.append(HumanMessage(content=request.message))

        result = graph.invoke({"messages": messages})

        answer = ""

        if isinstance(result, dict):
            result_messages = result.get("messages", [])

            if result_messages:
                last_message = result_messages[-1]
                answer = getattr(last_message, "content", "")

                if not isinstance(answer, str):
                    answer = str(answer)

            if not answer:
                answer = str(
                    result.get("answer")
                    or result.get("response")
                    or result.get("output")
                    or ""
                )

        if not answer:
            raise ValueError(
                "The agent returned no answer. Check the graph's state schema."
            )

        return {"answer": answer}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(exc)}",
        ) from exc


# --------------------------------------------------
# Speech-to-text
# POST /api/transcribe
# --------------------------------------------------

@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    check_auth(authorization)
    openai_client = require_openai()

    allowed_types = {
        "audio/webm",
        "audio/ogg",
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp4",
        "audio/mp3",
        "audio/m4a",
        "video/webm",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio type: {file.content_type}",
        )

    audio_bytes = await file.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    if len(audio_bytes) > 20_000_000:
        raise HTTPException(
            status_code=413,
            detail="Audio file must be under 20 MB.",
        )

    filename = Path(file.filename or "recording.webm").name

    try:
        result = openai_client.audio.transcriptions.create(
            model=TRANSCRIPTION_MODEL,
            file=(
                filename,
                io.BytesIO(audio_bytes),
                file.content_type,
            ),
        )

        return {"text": result.text}

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Transcription failed: {str(exc)}",
        ) from exc

    finally:
        await file.close()


# --------------------------------------------------
# Text-to-speech
# POST /api/speak
# --------------------------------------------------

@app.post("/api/speak")
def speak(
    request: SpeakRequest,
    authorization: str | None = Header(default=None),
):
    check_auth(authorization)
    openai_client = require_openai()

    voice = request.voice or SPEECH_VOICE

    # Restrict voices to known supported choices.
    if voice not in {
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "fable",
        "nova",
        "onyx",
        "sage",
        "shimmer",
        "verse",
    }:
        raise HTTPException(status_code=400, detail="Unsupported voice.")

    try:
        audio = openai_client.audio.speech.create(
            model=SPEECH_MODEL,
            voice=voice,
            input=request.text,
            response_format="mp3",
        )

        return Response(
            content=audio.content,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="speech.mp3"'
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Speech generation failed: {str(exc)}",
        ) from exc


# --------------------------------------------------
# Image analysis
# POST /api/inspect-image
# --------------------------------------------------

@app.post("/api/inspect-image")
def inspect_image(
    request: ImageRequest,
    authorization: str | None = Header(default=None),
):
    check_auth(authorization)
    openai_client = require_openai()

    mime, _ = inspect_image_data(request.image_data)

    try:
        result = openai_client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": request.question,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": request.image_data,
                            },
                        },
                    ],
                }
            ],
        )

        answer = result.choices[0].message.content or ""

        return {"answer": answer}

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Image analysis failed: {str(exc)}",
        ) from exc
 