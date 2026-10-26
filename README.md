# MediAI — Medical Agentic Chatbot

A responsive medical education chatbot frontend connected to a FastAPI backend. The application supports text-based medical questions, retrieval from a medical PDF knowledge base, source citations, image uploads, voice input, and text-to-speech where supported by the configured backend and browser.

> **Medical disclaimer:** MediAI is an educational tool, not a substitute for professional medical advice, diagnosis, or treatment. For medical emergencies, contact local emergency services.

## Features

- **AI medical chat** — Ask medical and health-related questions.
- **Knowledge-base retrieval** — Retrieve relevant information from the configured medical PDF knowledge base.
- **Source citations** — Display available PDF page references alongside answers.
- **Image upload** — Select supported medical images for inspection, subject to backend configuration.
- **Voice input** — Record audio and transcribe it when the transcription endpoint is configured.
- **Text-to-speech** — Listen to responses using browser speech synthesis where supported.
- **Responsive interface** — Layout adapts to desktop and mobile screens.
- **API authentication** — Supports an optional bearer token when configured on the backend.

## Project Structure

```text
medical-agentic-chatbot/
├── app/
│   ├── main.py              # FastAPI application and API endpoints
│   ├── agent.py             # AI agent and knowledge retrieval
│   └── config.py            # Application configuration
├── data/
│   └── medical_book.pdf     # Medical reference PDF
├── static/
│   ├── index.html           # Frontend page
│   ├── style.css            # Responsive styling
│   └── app.js               # Chat and frontend interactions
├── .env                     # Local environment variables (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

The exact project structure may vary depending on your current implementation.

## Requirements

- Python 3.12 recommended
- A configured Gemini API key
- A configured Pinecone API key and index for knowledge retrieval
- A modern browser
- Additional provider credentials only for features that explicitly require them

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Yash-Tailor1/medical-agentic-chatbot.git
cd medical-agentic-chatbot
```

### 2. Create and activate a virtual environment

On macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

If the virtual environment already exists, activate it instead of creating another one.

### 3. Configure environment variables

Create a local `.env` file in the project root. Add the credentials required by your backend implementation:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
TAVILY_API_KEY=your_tavily_api_key

PINECONE_INDEX=medical-agent-demo
API_TOKEN=
```

Use the actual variable names expected by your `app/config.py` and backend endpoints. Optional variables may be omitted if the corresponding functionality is not used.

**Security:**
- Never commit `.env` or real API keys to GitHub.
- Keep `.env` in `.gitignore`.
- Use `.env.example` with placeholder values to document configuration.
- Rotate any API key accidentally exposed in a commit or log.
- Do not put production API keys in frontend JavaScript.

## Run the Application

### Option A: Serve the frontend through FastAPI

From the project root:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open:

- Frontend: `http://127.0.0.1:8000/` — if your FastAPI application serves `static/index.html` at `/`.
- API health: `http://127.0.0.1:8000/api/health`
- API documentation: `http://127.0.0.1:8000/docs`

The frontend route must be configured in FastAPI for the first URL to work.

### Option B: Run the frontend separately

If the frontend is a standalone bundle with `index.html`, `styles.css`, and `script.js`, open a second terminal in the folder containing those files:

```bash
python3 -m http.server 5500
```

Open `http://127.0.0.1:5500`.

Configure the frontend API base URL to:

```javascript
const API_BASE = "http://127.0.0.1:8000";
```

When serving the frontend and backend on different ports, configure FastAPI CORS to allow `http://127.0.0.1:5500`. Do not use `*` as the production CORS policy.

**Important:** Choose the setup that matches your actual frontend files. The current project structure above uses `static/style.css` and `static/app.js`; a separate bundle may use different filenames.

## API Endpoints

The frontend depends on the endpoints implemented by the backend.

| Endpoint | Purpose |
|---|---|
| `GET /` | Application homepage, if configured |
| `GET /api/health` | Check backend availability and configuration status |
| `POST /api/chat` | Submit a message and receive an AI response |
| `POST /api/inspect-image` | Inspect an image, if implemented and configured |
| `POST /api/transcribe` | Transcribe an uploaded audio recording, if configured |
| `POST /api/speak` | Generate speech audio, if implemented and configured |

Endpoint names, request formats, authentication requirements, and availability depend on the current backend implementation. Check `/docs` for the authoritative API schema.

## Configuration and Compatibility

### API authentication

If the backend uses `API_TOKEN`, send the matching token as a bearer authorization header:

```http
Authorization: Bearer YOUR_API_TOKEN
```

For local testing, keep the token out of committed frontend files. Prefer a local development configuration or another suitable secure mechanism.

### Image inspection

The frontend may accept JPEG, PNG, and WebP images up to 5 MB. The backend must independently validate file types and file sizes.

Image inspection may require a configured vision model and provider credentials. A successful upload does not guarantee that image analysis is enabled.

### Voice input

Microphone access requires browser permission and generally requires HTTPS or a trusted local origin such as `localhost`.

The transcription endpoint must accept the audio format produced by the browser. If transcription uses OpenAI, configure `OPENAI_API_KEY` on the server. If the backend uses another provider, configure the credentials required by that implementation instead.

### Text-to-speech

Browser speech synthesis can work without a provider API key when supported by the browser and operating system. Server-generated speech requires the corresponding backend endpoint and provider configuration.

### Markdown rendering

If the frontend uses the `marked` and `DOMPurify` CDN libraries, an internet connection may be required to load them. Without these libraries, the frontend should fall back to safe plain-text rendering.

Never render untrusted model output as unsanitized HTML.

### Conversation history

Conversation history held only in JavaScript memory is cleared when the page reloads. Persistent conversation history requires a separate storage implementation.

## Troubleshooting

**Frontend cannot connect to the API**
- Confirm FastAPI is running on port `8000`.
- Check the API base URL.
- Open `/api/health` and review the server logs.
- Check CORS configuration if the frontend runs on port `5500`.

**Chat returns an error**
- Check the Gemini API key and provider quota.
- Confirm Pinecone configuration if knowledge retrieval is enabled.
- Review the FastAPI terminal output and `/docs`.

**Image inspection fails**
- Verify that the image endpoint exists.
- Check supported formats and size limits.
- Confirm the required vision provider is configured.

**Voice transcription fails**
- Check the transcription endpoint and its provider credentials.
- Confirm that the uploaded audio MIME type is supported.
- Grant microphone access in the browser.

**GitHub blocks a push**
- Check for secrets in the current files and previous commits.
- Remove exposed credentials from Git history as necessary.
- Rotate any exposed keys before continuing.

## Development

Run the backend with automatic reload:

```bash
uvicorn app.main:app --reload
```

Before committing changes, review the files being staged:

```bash
git status
git diff --cached
```

Then commit and push:

```bash
git add README.md static/
git commit -m "Update MediAI frontend and documentation"
git push origin main
```

Only stage the files you intend to publish. Never stage `.env` or other files containing secrets.

## Disclaimer

MediAI is intended for medical education and informational purposes only. Its responses may be incomplete or incorrect. Verify important information with qualified healthcare professionals and reliable medical sources. Do not use the application as the sole basis for medical decisions.
