# MediAI frontend bundle

This bundle provides a complete standalone frontend for your existing FastAPI backend.

## Files
- `index.html` — page layout and controls
- `styles.css` — responsive MediAI styling
- `script.js` — chat, image inspection, voice transcription, text-to-speech, chat history

## Run it
Terminal 1, from your backend project root:
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Terminal 2, from the folder containing these three files:
```bash
python -m http.server 5500
```
Open http://127.0.0.1:5500

## Configuration
- The frontend uses `http://127.0.0.1:8000` as the API base.
- If `settings.api_token` is configured in the backend, set the same token in `API_TOKEN` in `script.js` for local testing. Do not commit real tokens to a public repo.
- Image endpoint currently accepts JPEG, PNG, WebP and image payloads up to 5 MB.
- Voice endpoints need `OPENAI_API_KEY` configured server-side.
- Markdown rendering uses the `marked` and `DOMPurify` CDN scripts. If you're offline, answers fall back to safe plain text.
- Recent conversations are kept in memory only and will disappear when the page is reloaded.

## Important
This replaces only the frontend files. It does not overwrite your FastAPI backend.
