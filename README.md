# Medical Agentic Chatbot

An AI-powered medical education chatbot built with **FastAPI, Google Gemini, and Pinecone**. The application uses retrieval-augmented generation (RAG) to retrieve relevant information from a medical reference book and generate context-aware answers to medical questions.

## Features

- **AI-powered Q&A:** Generate responses to medical education questions using Google Gemini.
- **Retrieval-Augmented Generation (RAG):** Ground responses in relevant passages retrieved from a medical knowledge base.
- **PDF ingestion:** Extract, chunk, and index medical reference material.
- **Semantic search:** Retrieve relevant text using Pinecone vector search.
- **FastAPI backend:** Expose chatbot and health-check endpoints.
- **Web frontend:** Interact with the chatbot through a browser.
- **Image and voice support:** Intended for multimodal interactions where implemented in the application.

## Live Demo

- **Application:** https://medical-agentic-chatbot-3ohb.onrender.com
- **API health check:** https://medical-agentic-chatbot-3ohb.onrender.com/api/health
- **API documentation:** https://medical-agentic-chatbot-3ohb.onrender.com/docs

*Note: The application is hosted on Render. On free instances, the service may take some time to respond after inactivity.*

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| FastAPI | Backend API |
| Google Gemini | AI-generated responses |
| Gemini Embeddings | Text embeddings |
| Pinecone | Vector storage and semantic retrieval |
| PyMuPDF | PDF text extraction |
| python-dotenv | Environment configuration |
| HTML, CSS, JavaScript | Web interface |
| Render | Application hosting |

## How It Works

1. Extract text from the medical reference PDF.
2. Split the extracted text into overlapping chunks.
3. Generate embeddings for the text chunks.
4. Store the embeddings and metadata in Pinecone.
5. Retrieve relevant passages when a user asks a question.
6. Send the question and retrieved context to Gemini to generate a response.

```text
User
 |
 v
Web Frontend
 |
 v
FastAPI Backend
 |
 v
Pinecone Vector Search
 |
 v
Relevant Medical Context
 |
 v
Google Gemini
 |
 v
Response to User
```

## Knowledge Base

The current project configuration uses:

- **Source document:** `data/medical_book.pdf`
- **Document length:** 637 pages
- **Chunk size:** 1,100 characters
- **Chunk overlap:** 180 characters
- **Embedding model:** `gemini-embedding-2`
- **Pinecone index:** `medical-agent-demo`
- **Vector dimensions:** 1,536
- **Pinecone region:** AWS `us-east-1`

These values describe the current configuration and may need updating if the embedding model or index changes.

## Run Locally

### Prerequisites

- Python 3.12 recommended
- Google Gemini API key
- Pinecone API key
- Git

### 1. Clone the repository

```bash
git clone <YOUR_PUBLIC_REPOSITORY_URL>
cd medical-agentic-chatbot
```

Replace `<YOUR_PUBLIC_REPOSITORY_URL>` with your GitHub repository URL.

### 2. Create and activate a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

If the repository contains `requirements.txt`:

```bash
pip install -r requirements.txt
```

If dependencies are managed through `pyproject.toml` and `uv`:

```bash
uv sync
```

Use the installation method supported by the dependency files included in the repository.

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=medical-agent-demo
```

Use the exact environment variable names expected by your application configuration. Never commit `.env` or expose API keys in source code.

### 5. Start the backend

```bash
uvicorn app.main:app --reload
```

Open the following URLs in your browser:

- Application/API root: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/api/health
- Interactive API documentation: http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Application root |
| `GET` | `/api/health` | Check API health |
| `POST` | `/api/chat` | Submit a chatbot request |

Refer to `/docs` for the actual request and response schemas.

## Deploy on Render

The backend can be deployed as a **Render Web Service**.

1. Push the project to a GitHub repository.
2. In Render, create a new **Web Service** and connect the repository.
3. Configure the build and start commands based on the project's dependency files.
4. Add the required environment variables under the Render service's **Environment** settings.
5. Deploy the service and verify the health-check endpoint.

Typical commands, if the project uses `requirements.txt`:

**Build command**

```bash
pip install -r requirements.txt
```

**Start command**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure the service's Python version to match the version supported by the project and its dependencies.

### Render environment variables

Add the required secrets in Render rather than committing them to GitHub:

- `GEMINI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX`

Include any additional variables required by your application's settings.

**Important:** If the frontend is served separately from the FastAPI backend, configure its API base URL to point to the deployed backend and set up CORS as needed.

## Knowledge-Base Ingestion

To process the medical PDF and populate the vector database, run the ingestion script from the project root:

```bash
python ingest.py
```

Run ingestion only when needed. If the existing Pinecone index is already populated, check the script's duplicate-handling behavior before running it again.

The PDF and its redistribution rights should be reviewed before publishing it in a public repository. If it cannot be redistributed, document how to obtain it separately rather than committing it.

## Security

- Keep `.env`, API keys, and other credentials out of Git.
- Add `.env` and `.venv/` to `.gitignore`.
- Never publish private credentials, database connection strings, or service tokens.
- Avoid committing large or copyrighted reference documents without permission.

## Medical Disclaimer

This project is intended for **medical education and informational purposes only**. It is not a substitute for professional medical advice, diagnosis, or treatment. AI-generated responses may be inaccurate or incomplete. Consult a qualified healthcare professional for personal medical concerns.

## Future Improvements

- Improve answer citations and source traceability.
- Expand automated API and frontend tests.
- Add robust image and voice workflows.
- Improve error handling, logging, and retrieval quality.
- Add authentication and request-rate limiting where appropriate.

## License

Choose a license before making the repository public. If you want others to use, modify, and distribute your code, consider adding an appropriate open-source license such as the MIT License.

---

**Built with FastAPI, Google Gemini, and Pinecone.**