let currentTranscript = '';

// Send URL on summarize
async function summarizeTranscript() {
    if (!currentTranscript) {
        showError('No transcript to summarize');
        return;
    }

    const urlInput = document.getElementById('videoUrl');
    const url = urlInput.value.trim();

    const summaryBtn = document.getElementById('summaryBtn');
    const summaryDiv = document.getElementById('summary');
    const summaryContent = document.getElementById('summaryContent');

    summaryBtn.disabled = true;
    summaryBtn.textContent = '⏳ Generating summary...';

    try {
        const response = await fetch('/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transcript: currentTranscript,
                url: url // Send URL to update DB
            })
        });

        const data = await response.json();

        if (data.success) {
            summaryContent.innerHTML = '<p>' + data.summary.replace(/\n/g, '<br>') + '</p>';
            summaryDiv.classList.remove('hidden');
            summaryDiv.style.display = 'block';
            summaryBtn.textContent = '✓ Summary Generated';
        } else {
            showError(data.error || 'Failed to generate summary');
            summaryBtn.textContent = '✨ Summarize';
            summaryBtn.disabled = false;
        }
    } catch (error) {
        showError('Error: ' + error.message);
        summaryBtn.textContent = '✨ Summarize';
        summaryBtn.disabled = false;
    }
}

async function extractTranscript() {
    const urlInput = document.getElementById('videoUrl');
    const url = urlInput.value.trim();

    if (!url) {
        showError('Please enter a video URL');
        return;
    }

    hideAll();
    showLoading();
    resetVisualizer();
    document.getElementById('progress-visualizer').style.display = 'flex';
    document.getElementById('progress-visualizer').classList.remove('hidden');

    try {
        const response = await fetch('/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url, force_whisper: false })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let transcriptParts = [];

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    handleStreamEvent(data, transcriptParts);
                }
            }
        }

    } catch (error) {
        hideLoading();
        showError('Network connection error: ' + error.message);
    }
}

function handleStreamEvent(data, transcriptParts) {
    if (data.status === 'step_update') {
        updateVisualizer(data.step, 'active');
        // Mark previous steps as completed/failed logic could be inferred
        // For simplicity:
        if (data.step === 'ytdlp') updateVisualizer('api', 'failed');
        if (data.step === 'whisper') {
            updateVisualizer('api', 'failed');
            updateVisualizer('ytdlp', 'failed');
            // Show detailed loading for whisper
            document.getElementById('loading').innerHTML = '<div class="spinner"></div><p>🤖 AI Transcription starting...</p>';
        }

        // Update loading text
        if (data.message) {
            const loadingP = document.querySelector('#loading p');
            if (loadingP) loadingP.textContent = data.message;
        }

    } else if (data.status === 'info') {
        console.log('Info:', data.message);

    } else if (data.status === 'downloading') {
        document.getElementById('loading').innerHTML = '<div class="spinner"></div><p>📥 ' + data.message + '</p>';

    } else if (data.status === 'processing') {
        document.getElementById('loading').innerHTML = '<div class="spinner"></div><p>⚙️ ' + data.message + '</p>';

    } else if (data.status === 'transcribing') {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('result').classList.remove('hidden');
        document.getElementById('transcript').innerHTML = '<div class="streaming-indicator">🎤 AI is transcribing audio...</div>';

    } else if (data.status === 'segment') {
        transcriptParts.push(data.text);
        currentTranscript = transcriptParts.join(' ');
        document.getElementById('transcript').innerHTML = formatMarkdown(currentTranscript) + '<span class="cursor">▋</span>';

    } else if (data.status === 'complete') {
        hideLoading();
        // Mark successful step
        if (document.getElementById('step-whisper').classList.contains('active')) {
            updateVisualizer('whisper', 'completed');
        } else if (document.getElementById('step-ytdlp').classList.contains('active')) {
            updateVisualizer('ytdlp', 'completed');
            updateVisualizer('api', 'failed');
        } else {
            updateVisualizer('api', 'completed');
        }

        currentTranscript = data.transcript;
        showResult(formatTranscript(data.transcript));

    } else if (data.status === 'error') {
        hideLoading();
        showError(data.error);
        // Mark current active step as failed
        document.querySelectorAll('.progress-step.active').forEach(el => {
            el.classList.remove('active');
            el.classList.add('failed');
        });
    }
}

function updateVisualizer(stepId, status) {
    const el = document.getElementById('step-' + stepId);
    if (!el) return;

    // Remove all status classes first to be safe, or just add
    el.classList.remove('active', 'completed', 'failed');
    el.classList.add(status);
}

function resetVisualizer() {
    const steps = ['api', 'ytdlp', 'whisper'];
    steps.forEach(step => {
        const el = document.getElementById('step-' + step);
        if (el) el.classList.remove('active', 'completed', 'failed');
    });
}




function formatMarkdown(text) {
    // Split into paragraphs (every 3-4 sentences for better readability)
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    let formatted = '';
    let paragraph = [];

    sentences.forEach((sentence, index) => {
        paragraph.push(sentence.trim());
        if (paragraph.length >= 3 || index === sentences.length - 1) {
            formatted += '<p class="transcript-paragraph">' + paragraph.join(' ') + '</p>\n';
            paragraph = [];
        }
    });

    return formatted || '<p class="transcript-paragraph">' + text + '</p>';
}

function formatTranscript(text) {
    return formatMarkdown(text);
}

function showLoading() {
    const loading = document.getElementById('loading');
    loading.classList.remove('hidden');
    loading.style.display = 'block';
    document.getElementById('extractBtn').disabled = true;
}

function hideLoading() {
    const loading = document.getElementById('loading');
    loading.classList.add('hidden');
    loading.style.display = 'none';
    document.getElementById('extractBtn').disabled = false;
}

function showResult(formattedTranscript) {
    const result = document.getElementById('result');
    document.getElementById('transcript').innerHTML = formattedTranscript;
    result.classList.remove('hidden');
    result.style.display = 'block';
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    errorDiv.style.display = 'block';
}

function hideAll() {
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const result = document.getElementById('result');

    loading.classList.add('hidden');
    loading.style.display = 'none';
    error.classList.add('hidden');
    error.style.display = 'none';
    result.classList.add('hidden');
    result.style.display = 'none';
}

function copyTranscript() {
    navigator.clipboard.writeText(currentTranscript).then(() => {
        const btn = document.querySelector('.copy-btn');
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        showError('Failed to copy: ' + err.message);
    });
}

// function summarizeTranscript() is defined at top now to fix scope issue if needed, 
// but actually we should just replace the existing one.
// Let's rely on the previous chunk having defined it, so we delete the old one here.
// Wait, I cannot delete efficiently without huge context.
// Better plan: just overwrite the existing summarizeTranscript function below. 

async function summarizeTranscript() {
    if (!currentTranscript) {
        showError('No transcript to summarize');
        return;
    }

    // Get URL from input or if loaded from history, we might need to store it globally.
    // For now try input.
    const urlInput = document.getElementById('videoUrl');
    const url = urlInput.value.trim();

    const summaryBtn = document.getElementById('summaryBtn');
    const summaryDiv = document.getElementById('summary');
    const summaryContent = document.getElementById('summaryContent');

    summaryBtn.disabled = true;
    summaryBtn.textContent = '⏳ Generating summary...';

    try {
        const response = await fetch('/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transcript: currentTranscript,
                url: url
            })
        });

        const data = await response.json();

        if (data.success) {
            summaryContent.innerHTML = '<p>' + data.summary.replace(/\n/g, '<br>') + '</p>';
            summaryDiv.classList.remove('hidden');
            summaryDiv.style.display = 'block';
            summaryBtn.textContent = '✓ Summary Generated';
        } else {
            showError(data.error || 'Failed to generate summary');
            summaryBtn.textContent = '✨ Summarize';
            summaryBtn.disabled = false;
        }
    } catch (error) {
        showError('Error: ' + error.message);
        summaryBtn.textContent = '✨ Summarize';
        summaryBtn.disabled = false;
    }
}

// Allow Enter key to submit
document.getElementById('videoUrl').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        extractTranscript();
    }
});

function switchTab(tab) {
    console.log('Switching to tab:', tab);

    const extractTab = document.getElementById('extractTab');
    const historyTab = document.getElementById('historyTab');
    const howtoTab = document.getElementById('howtoTab');
    const tabs = [extractTab, historyTab, howtoTab];
    const btns = document.querySelectorAll('.tab-btn');

    tabs.forEach(t => {
        if (t) {
            t.classList.remove('active');
            t.style.display = 'none'; // Ensure hidden
        }
    });
    btns.forEach(btn => btn.classList.remove('active'));

    if (tab === 'extract') {
        extractTab.classList.add('active');
        extractTab.style.display = 'block';
        btns[0].classList.add('active');
    } else if (tab === 'history') {
        historyTab.classList.add('active');
        historyTab.style.display = 'block';
        btns[1].classList.add('active');
        loadHistory();
    } else {
        howtoTab.classList.add('active');
        howtoTab.style.display = 'block';
        btns[2].classList.add('active');
    }
}

async function loadHistory() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '<div class="spinner"></div>';

    try {
        const response = await fetch('/history');
        const videos = await response.json();

        if (videos.length === 0) {
            historyList.innerHTML = '<p>No history found.</p>';
            return;
        }

        let html = '';
        videos.forEach(video => {
            const date = new Date(video.created_at).toLocaleString();
            const summaryBadge = video.has_summary ? '<span class="badge">📝 Summary</span>' : '';
            html += `
                <div class="history-item" onclick="loadHistoryItem('${video.video_id}')">
                    <div class="history-thumb">
                        <img src="https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg" alt="Highlight" onerror="this.src='https://via.placeholder.com/120x90?text=No+Img'">
                    </div>
                    <div class="history-info">
                        <h3>${video.title || video.url}</h3>
                        <p class="meta">📅 ${date} ${summaryBadge}</p>
                        <p class="url">${video.url}</p>
                    </div>
                </div>
            `;
        });
        historyList.innerHTML = html;

    } catch (error) {
        historyList.innerHTML = '<p class="error">Failed to load history.</p>';
    }
}

async function loadHistoryItem(videoId) {
    // Switch to extract tab
    switchTab('extract');
    hideAll();
    showLoading();
    document.getElementById('loading').innerHTML = '<p>Loading from history...</p>';

    try {
        const response = await fetch('/history/' + videoId);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        // Populate inputs
        document.getElementById('videoUrl').value = data.url;

        // Show result
        hideLoading();
        currentTranscript = data.transcript;
        showResult(formatTranscript(data.transcript));

        // Show summary if exists
        if (data.summary) {
            const summaryDiv = document.getElementById('summary');
            document.getElementById('summaryContent').innerHTML = '<p>' + data.summary.replace(/\n/g, '<br>') + '</p>';
            summaryDiv.classList.remove('hidden');
            summaryDiv.style.display = 'block';
        } else {
            document.getElementById('summary').classList.add('hidden');
            document.getElementById('summary').style.display = 'none';
        }

    } catch (error) {
        hideLoading();
        showError('Failed to load item: ' + error.message);
    }
}
