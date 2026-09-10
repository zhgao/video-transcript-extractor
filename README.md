# 🎥 AI Video Transcript Extractor

A powerful web application that extracts and summarizes video transcripts using cutting-edge AI technology.

## ✨ Features

- **Multi-Platform Support**: YouTube, TikTok, and 1000+ video platforms
- **Smart Extraction**: Automatically tries captions first, falls back to AI transcription
- **AI Speech Recognition**: Uses OpenAI Whisper for videos without captions
- **AI Summarization**: Generates concise summaries using Llama 3.2 (Ollama)
- **Real-Time Streaming**: Watch transcription progress in real-time
- **Beautiful UI**: Clean, modern interface with formatted paragraphs
- **One-Click Copy**: Easy transcript copying to clipboard

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Speech-to-Text**: OpenAI Whisper
- **AI Summarization**: Ollama (Llama 3.2)
- **Video Processing**: yt-dlp
- **Transcript API**: youtube-transcript-api
- **Frontend**: Vanilla JavaScript, CSS3

## 📋 Prerequisites

- Python 3.8+
- ffmpeg
- Ollama
- Chrome browser (for cookie authentication)

## 🚀 Installation

### 1. Install System Dependencies

```bash
# Install ffmpeg
brew install ffmpeg

# Install Ollama
brew install ollama
```

### 2. Clone and Setup

```bash
git clone https://github.com/zhgao/video-transcript-extractor.git
cd video-transcript-extractor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install AI Model

```bash
ollama pull llama3.2
```

### 4. Setup YouTube Cookies (Optional but Recommended)

To avoid YouTube blocking:
1. Install browser extension: "Get cookies.txt LOCALLY"
2. Go to youtube.com (logged in)
3. Export cookies as `cookies.txt` in project directory

## 🎯 Usage

### Start the Application

```bash
source venv/bin/activate
python app.py
```

Open browser: **http://localhost:8080**

### How It Works

1. **Paste Video URL**: Any YouTube, TikTok, or supported platform URL
2. **Extract Transcript**: 
   - First tries existing captions (fast, ~5 seconds)
   - If no captions, downloads audio and uses Whisper AI (~1-5 minutes)
3. **Summarize**: Click "✨ Summarize" for AI-generated summary
4. **Copy**: One-click copy to clipboard

## 🔧 How It Works Internally

### Extraction Flow

```
User pastes URL
    ↓
Try YouTube Transcript API (fast)
    ↓ (if blocked/no captions)
Try yt-dlp with browser cookies
    ↓ (if no captions found)
Download audio → Whisper AI transcription
    ↓
Display formatted transcript
```

### AI Transcription (Whisper)

When no captions exist:
1. Downloads audio using yt-dlp
2. Converts to MP3 format
3. Whisper AI transcribes speech to text
4. Streams results in real-time to browser

### AI Summarization (Ollama)

1. Sends transcript to local Ollama server
2. Llama 3.2 model generates 3-5 bullet point summary
3. Displays in highlighted summary box

## 📁 Project Structure

```
video-transcript-extractor/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── cookies.txt           # YouTube cookies (optional)
├── templates/
│   └── index.html        # Main web interface
├── static/
│   ├── script.js         # Frontend JavaScript
│   └── style.css         # Styling
├── venv/                 # Virtual environment
└── README.md            # This file
```

## 🔑 Key Functions

### Backend (app.py)

- `get_transcript()`: Main extraction logic with fallbacks
- `get_transcript_ytdlp()`: yt-dlp extraction with caption check
- `get_transcript_whisper()`: AI transcription using Whisper
- `stream_whisper_transcription()`: Real-time streaming to frontend
- `summarize_with_ollama()`: AI summarization

### Frontend (script.js)

- `extractTranscript()`: Handles user input and extraction
- `streamWhisperTranscription()`: Receives real-time updates
- `summarizeTranscript()`: Generates AI summary
- `formatMarkdown()`: Formats transcript into readable paragraphs

## 🎨 Features Explained

### Smart Fallback System

1. **Fast Path**: YouTube Transcript API (instant)
2. **Medium Path**: yt-dlp with cookies (5-10 seconds)
3. **Slow Path**: Whisper AI transcription (1-5 minutes)

### Real-Time Progress

Shows detailed steps:
- 📥 Step 1/4: Fetching video information
- 📥 Step 2/4: Downloading audio
- ⚙️ Step 3/4: Processing audio
- 🎤 Step 4/4: AI transcription in progress

### Formatted Output

- Auto-paragraphs every 3-4 sentences
- Larger first letter for each paragraph
- Justified text alignment
- Smooth scrolling

## 🐛 Troubleshooting

### "YouTube is blocking requests"
- Add cookies.txt file (see Setup section)
- Wait a few minutes between requests

### "Whisper transcription failed"
- Check ffmpeg is installed: `which ffmpeg`
- Ensure enough disk space for audio download

### "Failed to generate summary"
- Check Ollama is running: `ollama list`
- Ensure llama3.2 model is installed: `ollama pull llama3.2`

### Page shows "Extracting transcript..." on load
- Hard refresh: Cmd+Shift+R
- Clear browser cache
- Try incognito/private window

## 🔒 Privacy & Security

- All processing happens locally on your machine
- No data sent to external servers (except video platforms)
- Ollama runs completely offline
- Cookies are only used for YouTube authentication

## 📊 Performance

- **Caption extraction**: ~5 seconds
- **Whisper transcription**: 1-5 minutes (depends on video length)
- **AI summary**: 10-30 seconds
- **Model size**: Whisper base (~150MB), Llama 3.2 (~2GB)

## 🚧 Limitations

- Whisper transcription is slow for long videos (>30 min)
- Requires good internet for video download
- Some platforms may block automated access
- Summary quality depends on transcript accuracy

## 🔮 Future Improvements

- [ ] Support for multiple languages
- [ ] Timestamp-based navigation
- [ ] Export to PDF/TXT
- [ ] Batch processing multiple videos
- [ ] Custom summary prompts
- [ ] Speaker diarization (who said what)

## 📝 License

MIT License - Feel free to use and modify!

## 🙏 Credits

- OpenAI Whisper for speech recognition
- Ollama for local AI inference
- yt-dlp for video processing
- Flask for web framework

---

**Built with ❤️ using cutting-edge AI technology**
