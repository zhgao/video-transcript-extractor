#!/usr/bin/env python3
"""
YouTube Transcript Extractor
Extract transcripts/captions from YouTube videos
"""

from youtube_transcript_api import YouTubeTranscriptApi
import sys
import re


def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)',
        r'youtube\.com\/shorts\/([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume it's already a video ID
    return url


def get_transcript(video_url):
    """Get transcript from YouTube video"""
    try:
        video_id = extract_video_id(video_url)
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id, languages=['en'])
        
        # Combine all text segments
        full_transcript = ' '.join([snippet.text for snippet in transcript_data.snippets])
        return full_transcript
    
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python youtube_transcript.py <youtube_url>")
        print("Example: python youtube_transcript.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)
    
    video_url = sys.argv[1]
    print(f"Extracting transcript from: {video_url}\n")
    
    transcript = get_transcript(video_url)
    print(transcript)


if __name__ == "__main__":
    main()
