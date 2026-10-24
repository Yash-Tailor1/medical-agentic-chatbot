const API_BASE = "http://127.0.0.1:8000";
const API_URL = `${API_BASE}/api/chat`;

// Leave empty if your backend API_TOKEN is not configured.
// For local development only, enter a matching token if required.
const API_TOKEN = "";

function apiHeaders(json = false) {
    const headers = {};

    if (json) {
        headers["Content-Type"] = "application/json";
    }

    if (API_TOKEN) {
        headers["Authorization"] = `Bearer ${API_TOKEN}`;
    }

    return headers;
}

const messagesElement = document.getElementById("messages");
const welcomeElement = document.getElementById("welcome");
const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");
const historyElement = document.getElementById("chat-history");

let conversation = [];
let chatHistory = [];
let isLoading = false;


let selectedImageFile = null;
let mediaRecorder = null;
let audioChunks = [];

function setMediaStatus(message) {
    document.getElementById("media-status").textContent = message;
}

function fileToDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error("Could not read the image."));

        reader.readAsDataURL(file);
    });
}

// IMAGE UPLOAD AND PREVIEW
document.getElementById("image-upload").addEventListener("change", event => {
    const file = event.target.files[0];
    if (!file) return;

    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif"
    ];

    if (!allowedTypes.includes(file.type)) {
        setMediaStatus("Choose a JPEG, PNG, WebP, or GIF image.");
        event.target.value = "";
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        setMediaStatus("Please choose an image smaller than 10 MB.");
        event.target.value = "";
        return;
    }

    selectedImageFile = file;

    const preview = document.getElementById("image-preview");
    preview.replaceChildren();

    const image = document.createElement("img");
    image.alt = "Selected image preview";
    image.src = URL.createObjectURL(file);

    const name = document.createElement("span");
    name.textContent = ` ${file.name} `;

    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Remove image";
    remove.addEventListener("click", clearSelectedImage);

    preview.append(image, name, remove);
    setMediaStatus("Image attached. Ask a question and send it.");
});

function clearSelectedImage() {
    selectedImageFile = null;
    document.getElementById("image-upload").value = "";
    document.getElementById("image-preview").replaceChildren();
}

// VOICE RECORDING AND TRANSCRIPTION
document.getElementById("record-button").addEventListener("click", async () => {
    const button = document.getElementById("record-button");

    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        button.textContent = "🎙️ Record voice";
        setMediaStatus("Processing recording...");
        return;
    }

    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        setMediaStatus("Voice recording is not supported by this browser.");
        return;
    }

    let stream;

    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        const options = MediaRecorder.isTypeSupported("audio/webm")
            ? { mimeType: "audio/webm" }
            : {};

        mediaRecorder = new MediaRecorder(stream, options);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onerror = () => {
            setMediaStatus("Recording failed. Please try again.");
        };

        mediaRecorder.onstop = async () => {
            stream.getTracks().forEach(track => track.stop());

            try {
                const mimeType = mediaRecorder.mimeType || "audio/webm";
                const extension = mimeType.includes("mp4") ? "m4a" : "webm";
                const audioBlob = new Blob(audioChunks, { type: mimeType });

                if (!audioBlob.size) {
                    throw new Error("The recording was empty.");
                }

                const formData = new FormData();
                formData.append("file", audioBlob, `recording.${extension}`);

                const response = await fetch(`${API_BASE}/api/transcribe`, {
                    method: "POST",
                    headers: apiHeaders(),
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(
                        `Transcription failed (${response.status}): ` +
                        (await response.text()).slice(0, 250)
                    );
                }

                const data = await response.json();

                if (!data.text) {
                    throw new Error("The API returned no transcription text.");
                }

                input.value = data.text;
                input.dispatchEvent(new Event("input"));
                input.focus();

                setMediaStatus("Transcription ready. Review it and press Send.");
            } catch (error) {
                console.error("Transcription error:", error);
                setMediaStatus(error.message);
            }
        };

        mediaRecorder.start();
        button.textContent = "⏹ Stop recording";
        setMediaStatus("Recording... click Stop recording when finished.");
    } catch (error) {
        if (stream) stream.getTracks().forEach(track => track.stop());
        console.error("Microphone error:", error);
        setMediaStatus("Microphone access failed. Check browser permissions.");
    }
});


function scrollToBottom() {
    messagesElement.scrollTop = messagesElement.scrollHeight;
}

function hideWelcome() {
    if (welcomeElement) {
        welcomeElement.remove();
    }
}

function addMessage(role, text, options = {}) {
    hideWelcome();

    const message = document.createElement("div");
    message.className = `message ${role === "user" ? "user" : "assistant"}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "Y" : "✚";

    const content = document.createElement("div");
    content.className = "message-content";

    const name = document.createElement("div");
    name.className = "message-name";
    name.textContent = role === "user" ? "You" : "MediAI";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    content.append(name, bubble);
    message.append(avatar, content);
    messagesElement.appendChild(message);

    if (options.typing) {
        bubble.textContent = "";

        const typing = document.createElement("div");
        typing.className = "typing";

        for (let i = 0; i < 3; i++) {
            typing.appendChild(document.createElement("span"));
        }

        bubble.appendChild(typing);
        message.id = "typing-indicator";
    }

    scrollToBottom();
    return message;
}

function addHistory(title) {
    const item = document.createElement("button");
    item.className = "history-item";
    item.textContent = title;
    item.title = title;
    item.addEventListener("click", () => {
        alert("Persistent chat history is not configured yet.");
    });

    historyElement.prepend(item);
}

async function sendMessage(text) {
    text = text.trim();

if ((!text && !selectedImageFile) || isLoading) return;

if (!text && selectedImageFile) {
    text = "Describe this image and identify any visible medical information.";
}

    isLoading = true;
    sendButton.disabled = true;

    addMessage("user", text);
    conversation.push({ role: "user", content: text });

    if (chatHistory.length === 0) {
        chatHistory.push(text);
        addHistory(text);
    }

    input.value = "";
    input.style.height = "auto";

    const typingMessage = addMessage("assistant", "", { typing: true });

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                question: text,
                history: conversation
            })
        });

        if (!response.ok) {
            const details = await response.text();
            throw new Error(
                `Backend returned ${response.status}: ${details.slice(0, 200)}`
            );
        }

        const data = await response.json();

        // Adapt these keys to match your FastAPI response schema.
        const answer =
            data.answer ??
            data.response ??
            data.message ??
            data.result;

        if (typeof answer !== "string") {
            throw new Error(
                "The API responded, but no text answer was found. " +
                "Check the response JSON in your backend."
            );
        }

        typingMessage.remove();
        addMessage("assistant", answer);

        conversation.push({
            role: "assistant",
            content: answer
        });

    } catch (error) {
        typingMessage.remove();

        console.error("Chat request failed:", error);

        addMessage(
            "assistant",
            "I couldn't connect to the medical assistant. " +
            "Please check that your Python backend is running and " +
            "that API_URL in script.js matches its endpoint.\n\n" +
            `Details: ${error.message}`
        );
    } finally {
        isLoading = false;
        sendButton.disabled = false;
        input.focus();
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value);
});

input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
});

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
    }
});

document.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", () => {
        sendMessage(button.dataset.prompt);
    });
});

document.getElementById("new-chat").addEventListener("click", () => {
    conversation = [];
    chatHistory = [];
    messagesElement.replaceChildren();
    historyElement.replaceChildren();

    const welcome = document.createElement("div");
    welcome.id = "welcome";
    welcome.className = "welcome";
    welcome.innerHTML = `
        <div class="welcome-icon">✚</div>
        <p class="eyebrow">YOUR PERSONAL AI ASSISTANT</p>
        <h1>How can I help<br>you today?</h1>
        <p class="welcome-text">
            Ask medical questions and explore health information
            with your AI assistant.
        </p>
    `;

    messagesElement.appendChild(welcome);
});

document.getElementById("clear-chat").addEventListener("click", () => {
    document.getElementById("new-chat").click();
});
