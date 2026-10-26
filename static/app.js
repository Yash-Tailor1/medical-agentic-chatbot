
const $ = id => document.getElementById(id);

let history = [];
let imageData = null;
let recorder = null;
let audioChunks = [];
let cameraStream = null;
let lastAnswer = '';

const headers = () => {
    const h = {};
    const token = $('token').value.trim();

    if (token) {
        h.Authorization = `Bearer ${token}`;
    }

    return h;
};

function bubble(text, kind = 'bot', sources = []) {
    const el = document.createElement('article');
    el.className = kind;
    el.textContent = text;

    if (sources.length) {
        const s = document.createElement('div');
        s.className = 'sources';
        s.textContent =
            'Sources: ' +
            sources.slice(0, 8)
                .map(x => x.type === 'pdf'
                    ? `PDF page ${x.page}`
                    : x.url)
                .join(' | ');

        el.appendChild(s);
    }

    $('messages').appendChild(el);
    $('messages').scrollTop = $('messages').scrollHeight;

    return el;
}

// Check backend status
async function check() {
    try {
        const r = await fetch('/api/health');
        const d = await r.json();

        $('status').textContent = d.configured
            ? '● Connected'
            : '⚠ Configure API keys';
    } catch {
        $('status').textContent = '● Server offline';
    }
}

check();

// Image upload
function setImage(file) {
    if (!file) return;

    if (
        !['image/png', 'image/jpeg', 'image/webp'].includes(file.type) ||
        file.size > 5e6
    ) {
        alert('Use PNG/JPEG/WebP under 5MB');
        return;
    }

    const reader = new FileReader();

    reader.onload = () => {
        imageData = reader.result;
        $('thumbnail').src = imageData;
        $('preview').hidden = false;
    };

    reader.readAsDataURL(file);
}

$('image').addEventListener('change', e => {
    setImage(e.target.files[0]);
});

$('remove').onclick = () => {
    imageData = null;
    $('preview').hidden = true;
    $('image').value = '';
};

// Chat submission
$('chatForm').addEventListener('submit', async e => {
    e.preventDefault();

    const message = $('message').value.trim();

    if (!message) return;

    const prior = history.slice(-8);

    bubble(message, 'user');

    $('message').value = '';
    $('send').disabled = true;

    const pending = bubble('Thinking…');

    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                ...headers(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                history: prior,
                image_data: imageData
            })
        });

        const d = await r.json();

        if (!r.ok) {
            throw new Error(d.detail || 'Request failed');
        }

        pending.textContent = d.answer;
        lastAnswer = d.answer;

        if (d.sources?.length) {
            const src = document.createElement('div');
            src.className = 'sources';

            src.textContent =
                'Sources: ' +
                d.sources.slice(0, 8)
                    .map(x => x.type === 'pdf'
                        ? `PDF page ${x.page}`
                        : x.url)
                    .join(' | ');

            pending.appendChild(src);
        }

        history.push(
            { role: 'user', content: message },
            { role: 'assistant', content: d.answer }
        );

        $('remove').click();

    } catch (err) {
        pending.textContent = 'Error: ' + err.message;
    } finally {
        $('send').disabled = false;
        $('messages').scrollTop = $('messages').scrollHeight;
    }
});

// Microphone recording and transcription
$('mic').onclick = async () => {
    if (recorder && recorder.state === 'recording') {
        recorder.stop();
        $('mic').textContent = '🎤 Voice';
        return;
    }

    if (!navigator.mediaDevices?.getUserMedia ||
        typeof MediaRecorder === 'undefined') {
        alert('Microphone recording is not supported in this browser.');
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        audioChunks = [];
        recorder = new MediaRecorder(stream);

        recorder.ondataavailable = e => {
            if (e.data.size > 0) {
                audioChunks.push(e.data);
            }
        };

        recorder.onstop = async () => {
            stream.getTracks().forEach(t => t.stop());

            const blob = new Blob(audioChunks, {
                type: recorder.mimeType
            });

            const data = new FormData();
            data.append('file', blob, 'voice.webm');

            $('mic').disabled = true;
            $('mic').textContent = 'Processing…';

            try {
                const r = await fetch('/api/transcribe', {
                    method: 'POST',
                    headers: headers(),
                    body: data
                });

                const out = await r.json();

                if (!r.ok) {
                    throw new Error(
                        out.detail || 'Transcription failed'
                    );
                }

                $('message').value = out.text;

            } catch (e) {
                alert(e.message);
            } finally {
                $('mic').disabled = false;
                $('mic').textContent = '🎤 Voice';
            }
        };

        recorder.start();
        $('mic').textContent = '⏹ Stop recording';

    } catch (e) {
        alert('Microphone unavailable: ' + e.message);
    }
};

// Listen to the latest answer using browser speech synthesis
$('listen').onclick = () => {
    if (!lastAnswer) {
        alert('Ask a question first');
        return;
    }

    if (!('speechSynthesis' in window)) {
        alert('Speech synthesis is not supported by this browser.');
        return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(lastAnswer);

    utterance.lang = 'en-IN';
    utterance.rate = 1;
    utterance.pitch = 1;

    $('listen').disabled = true;

    utterance.onend = () => {
        $('listen').disabled = false;
    };

    utterance.onerror = () => {
        $('listen').disabled = false;
        alert('Unable to play speech.');
    };

    window.speechSynthesis.speak(utterance);
};

// Open camera
$('camera').onclick = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
        alert('Camera access is not supported in this browser.');
        return;
    }

    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });

        $('video').srcObject = cameraStream;
        $('video').hidden = false;
        $('cameraActions').hidden = false;

    } catch (e) {
        alert('Camera unavailable: ' + e.message);
    }
};

// Close camera and release resources
$('closeCamera').onclick = () => {
    cameraStream?.getTracks().forEach(t => t.stop());

    cameraStream = null;
    $('video').srcObject = null;
    $('video').hidden = true;
    $('cameraActions').hidden = true;
};

// Capture camera image
$('snap').onclick = () => {
    const v = $('video');
    const c = $('canvas');

    if (!v.videoWidth || !v.videoHeight) {
        alert('Camera is not ready yet. Please try again.');
        return;
    }

    c.width = v.videoWidth;
    c.height = v.videoHeight;

    c.getContext('2d').drawImage(
        v,
        0,
        0,
        c.width,
        c.height
    );

    c.toBlob(blob => {
        if (blob) {
            setImage(
                new File(
                    [blob],
                    'camera.jpg',
                    { type: 'image/jpeg' }
                )
            );
        }
    }, 'image/jpeg', 0.85);

    $('closeCamera').click();
};
