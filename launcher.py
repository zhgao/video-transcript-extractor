import sys
import os
import webbrowser
import threading
import time
import subprocess
from app import app

def open_browser():
    """Wait for server to start then open browser"""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:8080')

def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

if __name__ == '__main__':
    print("---------------------------------------------------")
    print("   🎥 YouTube Transcript Extractor - Starting...   ")
    print("---------------------------------------------------")
    
    if not check_ffmpeg():
        print("\n[WARNING] FFmpeg not found!")
        print("Whisper transcription requires FFmpeg to be installed.")
        print("Please install FFmpeg and add it to your PATH.\n")
        # We don't exit because YouTube API method might still work
    
    # Open browser in a separate thread
    threading.Thread(target=open_browser).start()
    
    # Run the app
    # host='0.0.0.0' allows external access, but '127.0.0.1' is safer for local tool
    app.run(port=8080)
