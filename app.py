#!/usr/bin/env python3
"""
YouTube Transcript Extractor - Web Interface
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import whisper
import re
import os
import tempfile
import json
import time
import sqlite3
import datetime
import concurrent.futures
from urllib.parse import urlparse, parse_qs

# --- Configuration ---
ENABLE_OLLAMA = True  # Re-enabled for Service Mode


def is_youtube_url(url):
    check_url = url.lower()
    return 'youtube.com' in check_url or 'youtu.be' in check_url

def extract_video_id(url):
    """Extract the video ID from a YouTube URL."""
    # Examples:
    # - http://youtu.be/SA2iWivDJiE
    # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    # - http://www.youtube.com/embed/SA2iWivDJiE
    # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    
    if not is_youtube_url(url):
        return None
        
    if 'youtu.be' in url:
        return url.split('/')[-1].split('?')[0]
    
    parsed = urlparse(url)
    if 'youtube' in parsed.netloc or 'youtube' in parsed.path:
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        if parsed.path.startswith(('/embed/', '/v/')):
            return parsed.path.split('/')[2]
            
    return None

DATA_DB = 'transcripts.db'

def init_db():
    start_time = time.time()
    try:
        with sqlite3.connect(DATA_DB) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    transcript TEXT,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")
    print(f"DB Init took {time.time() - start_time:.4f}s")

# Initialize DB on startup
init_db()

def get_video_from_db(video_id):
    try:
        with sqlite3.connect(DATA_DB) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
            return c.fetchone()
    except Exception as e:
        print(f"DB Get Error: {e}")
        return None

def save_video_to_db(video_id, url, transcript, title=None, summary=None):
    try:
        with sqlite3.connect(DATA_DB) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO videos (video_id, url, title, transcript, summary)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    transcript=excluded.transcript,
                    summary=excluded.summary,
                    title=excluded.title
            ''', (video_id, url, title, transcript, summary))
            conn.commit()
            print(f"Saved to DB: {video_id}")
    except Exception as e:
        print(f"DB Save Error: {e}")

app = Flask(__name__)

# Load Whisper model (lazy loading)
whisper_model = None

YOUTUBE_API_TIMEOUT_SECONDS = 8
NETWORK_TIMEOUT_SECONDS = 15
COOKIE_FILE = 'cookies.txt'
BROWSER_COOKIE_SOURCE = ('chrome',)

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model (this may take a moment on first run)...")
        whisper_model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
    return whisper_model


def get_event(status, **kwargs):
    """Helper to format SSE events"""
    data = {'status': status}
    data.update(kwargs)
    return f"data: {json.dumps(data)}\n\n"

def fetch_youtube_transcript_with_timeout(video_id):
    """Fetch transcript captions without letting the request block the whole stream."""
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(
            lambda: YouTubeTranscriptApi().fetch(video_id, languages=['en'])
        )
        return future.result(timeout=YOUTUBE_API_TIMEOUT_SECONDS)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

def ytdlp_extract_info(video_url, base_opts, download=False):
    """Try yt-dlp with exported cookies, then retry with browser cookies if needed."""
    cookie_attempts = []
    if os.path.exists(COOKIE_FILE):
        cookie_attempts.append(('cookies.txt', {'cookiefile': COOKIE_FILE}))
    cookie_attempts.append(('Chrome browser cookies', {'cookiesfrombrowser': BROWSER_COOKIE_SOURCE}))

    last_error = None
    for label, cookie_opts in cookie_attempts:
        try:
            ydl_opts = dict(base_opts)
            ydl_opts.update(cookie_opts)
            print(f"Trying yt-dlp with {label}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(video_url, download=download)
        except Exception as e:
            last_error = e
            print(f"yt-dlp with {label} failed: {e}")

    if last_error:
        raise last_error
    raise RuntimeError("yt-dlp failed before making an extraction attempt")

def stream_extraction(video_url, force_whisper=False):
    """
    Unified streaming extraction process.
    Yields events: step_update, info, complete, error
    """
    
    # --- Step 0: Check Local DB ---
    video_id = extract_video_id(video_url)
    if video_id:
        existing = get_video_from_db(video_id)
        if existing and existing['transcript']:
            yield get_event('complete', transcript=existing['transcript'], from_cache=True)
            # If summary exists, we might want to send it too, but current contract sends transcript first.
            return

    # --- Step 1: YouTube API (Fast Path) ---
    if not force_whisper and is_youtube_url(video_url):
        yield get_event('step_update', step='api', message='Checking YouTube Transcript API...')
        time.sleep(0.5)  # Visual delay
        
        video_id = extract_video_id(video_url)
        if video_id and len(video_id) == 11:
            try:
                transcript_data = fetch_youtube_transcript_with_timeout(video_id)
                full_transcript = ' '.join([snippet.text for snippet in transcript_data.snippets])
                if video_id:
                   save_video_to_db(video_id, video_url, full_transcript)
                yield get_event('complete', transcript=full_transcript)
                return
            except Exception as e:
                print(f"YouTube API failed: {str(e)}")
                yield get_event('info', message='YouTube API failed, trying next method...')
    
    # --- Step 2: yt-dlp (Medium Path) ---
    if not force_whisper:
        yield get_event('step_update', step='ytdlp', message='Checking captions with yt-dlp...')
        
        try:
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': NETWORK_TIMEOUT_SECONDS,
            }
            info = ytdlp_extract_info(video_url, ydl_opts, download=False)
                
            subs = None
            if 'subtitles' in info and 'en' in info['subtitles']:
                subs = info['subtitles']['en']
            elif 'automatic_captions' in info and 'en' in info['automatic_captions']:
                subs = info['automatic_captions']['en']
            
            if subs:
                # Parse subtitles logic
                json3_url = None
                for sub in subs:
                    if sub.get('ext') == 'json3':
                        json3_url = sub.get('url')
                        break
                
                if json3_url:
                    import requests
                    import json
                    response = requests.get(json3_url, timeout=NETWORK_TIMEOUT_SECONDS)
                    data = response.json()
                    transcript_parts = []
                    for event in data.get('events', []):
                        if 'segs' in event:
                            for seg in event['segs']:
                                if 'utf8' in seg:
                                    transcript_parts.append(seg['utf8'])
                    full_transcript = ' '.join(transcript_parts).replace('\n', ' ')
                    if video_id:
                         save_video_to_db(video_id, video_url, full_transcript)
                    yield get_event('complete', transcript=full_transcript)
                    return
        except Exception as e:
            print(f"yt-dlp error: {str(e)}")
            # Continue to next step
    
    # --- Step 3: Whisper AI (Slow Path) ---
    yield get_event('step_update', step='whisper', message='Falling back to AI transcription...')
    
    # Reuse existing Whisper logic but yield events designed for the visualizer
    try:
        # We process the existing stream_whisper_transcription generator
        for event in stream_whisper_transcription(video_url):
            # Parse the event to unify message format if needed, or just pass through
            # The existing event format is: data: {"status": "...", ...}
            # We want to make sure the frontend can handle it.
            # actually stream_whisper_transcription already yields formatted SSE strings.
            # We just need to ensure the status codes align with what we want for the visualizer updates.
            # Existing statuses: downloading, processing, transcribing, segment, complete, error
            
            yield event
            
    except Exception as e:
        yield get_event('error', error=str(e))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/extract', methods=['POST'])
def extract():
    data = request.get_json()
    video_url = data.get('url', '')
    force_whisper = data.get('force_whisper', False)
    
    if not video_url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    # Always stream
    return Response(
        stream_with_context(stream_extraction(video_url, force_whisper)),
        mimetype='text/event-stream'
    )


def stream_whisper_transcription(video_url):
    """Stream Whisper transcription progress with detailed logs"""
    try:
        yield f"data: {json.dumps({'status': 'downloading', 'message': 'Step 1/4: Fetching video information...'})}\n\n"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = os.path.join(temp_dir, 'audio')
            
            yield f"data: {json.dumps({'status': 'downloading', 'message': 'Step 2/4: Downloading audio from video...'})}\n\n"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_path + '.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': NETWORK_TIMEOUT_SECONDS,
            }
            info = ytdlp_extract_info(video_url, ydl_opts, download=True)
            duration = info.get('duration', 0)
            duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "unknown"
            
            yield f"data: {json.dumps({'status': 'processing', 'message': f'Step 3/4: Processing audio (duration: {duration_str})...'})}\n\n"
            
            final_audio_path = audio_path + '.mp3'
            if not os.path.exists(final_audio_path):
                files = os.listdir(temp_dir)
                audio_files = [f for f in files if f.endswith(('.mp3', '.m4a', '.webm', '.opus'))]
                if audio_files:
                    final_audio_path = os.path.join(temp_dir, audio_files[0])
                else:
                    yield f"data: {json.dumps({'status': 'error', 'error': 'Audio file not found'})}\n\n"
                    return
            
            yield f"data: {json.dumps({'status': 'transcribing', 'message': 'Step 4/4: AI transcription in progress...'})}\n\n"
            
            model = get_whisper_model()
            
            # Transcribe with word-level timestamps
            result = model.transcribe(final_audio_path, language='en', word_timestamps=True)
            
            # Stream segments as they're available
            for i, segment in enumerate(result['segments']):
                text = segment['text'].strip()
                if text:
                    yield f"data: {json.dumps({'status': 'segment', 'text': text})}\n\n"
                    time.sleep(0.05)  # Small delay for visual effect
            
            yield f"data: {json.dumps({'status': 'complete', 'transcript': result['text']})}\n\n"
            
            # Save to DB
            v_id = extract_video_id(video_url)
            if v_id:
                save_video_to_db(v_id, video_url, result['text'])
            
    except Exception as e:
        yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"


def summarize_with_ollama(transcript):
    """Generate summary using Ollama"""
    try:
        import requests
        
        prompt = f"""Please provide a concise summary of this video transcript in 3-5 bullet points:

{transcript[:4000]}

Summary:"""
        
        response = requests.post('http://localhost:11434/api/generate', 
            json={
                'model': 'llama3.2',
                'prompt': prompt,
                'stream': False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()['response']
        else:
            return None
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

def generate_title_with_ollama(transcript):
    """Generate a short title using Ollama"""
    try:
        import requests
        
        prompt = f"""Provide a very short, catchy 3-6 word title for this text. Do not use quotes.
Text:
{transcript[:2000]}

Title:"""
        
        response = requests.post('http://localhost:11434/api/generate', 
            json={
                'model': 'llama3.2',
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['response'].strip().strip('"')
        else:
            return None
    except Exception as e:
        print(f"Ollama Title error: {e}")
        return None


@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.get_json()
    transcript = data.get('transcript', '')
    
    if not transcript:
        return jsonify({'success': False, 'error': 'No transcript provided'})
    
    summary = summarize_with_ollama(transcript)
    
    if summary:
        # Generate Title
        title = generate_title_with_ollama(transcript)
        
        # Update summary in DB if possible
        # We need video_id or url here. The frontend sends only transcript.
        # Ideally frontend sends URL too.
        url = data.get('url') # Needs frontend update
        if url:
             v_id = extract_video_id(url)
             if v_id:
                 # We prefer to update only summary but our save helper does upsert.
                 # Let's just use SQL to update unique row
                 try:
                    with sqlite3.connect(DATA_DB) as conn:
                        c = conn.cursor()
                        # Update both summary and title
                        if title:
                            c.execute('UPDATE videos SET summary = ?, title = ? WHERE video_id = ?', (summary, title, v_id))
                        else:
                            c.execute('UPDATE videos SET summary = ? WHERE video_id = ?', (summary, v_id))
                        conn.commit()
                        print(f"Summary and Title ({title}) saved for {v_id}")
                 except Exception as e:
                     print(f"Error saving summary: {e}")
                     
        return jsonify({'success': True, 'summary': summary, 'title': title})
    else:
        return jsonify({'success': False, 'error': 'Failed to generate summary. Make sure Ollama is running with llama3.2 model.'})


@app.route('/history', methods=['GET'])
def history():
    """Get list of processed videos"""
    try:
        with sqlite3.connect(DATA_DB) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT video_id, url, title, created_at, CASE WHEN summary IS NOT NULL THEN 1 ELSE 0 END as has_summary FROM videos ORDER BY created_at DESC')
            rows = c.fetchall()
            return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history/<video_id>', methods=['GET'])
def get_history_item(video_id):
    """Get details for a specific video"""
    row = get_video_from_db(video_id)
    if row:
        return jsonify(dict(row))
    return jsonify({'error': 'Not found'}), 404

def test_whisper():
    """Test endpoint to force Whisper transcription"""
    data = request.get_json()
    video_url = data.get('url', '')
    
    if not video_url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    result = get_transcript_whisper(video_url)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
