from youtube_transcript_api import YouTubeTranscriptApi

video_id = 'tK1cfHQioLQ'

print(f"Testing video ID: {video_id}")
print()

try:
    print("Fetching transcript...")
    api = YouTubeTranscriptApi()
    transcript_data = api.fetch(video_id, languages=['en'])
    
    print(f'Type: {type(transcript_data)}')
    print(f'Dir: {[x for x in dir(transcript_data) if not x.startswith("_")]}')
    
    # Try to access the data
    if hasattr(transcript_data, 'entries'):
        entries = transcript_data.entries
    elif isinstance(transcript_data, list):
        entries = transcript_data
    else:
        entries = list(transcript_data)
    
    print(f'SUCCESS: Got transcript with {len(entries)} entries')
    print('First few entries:')
    for entry in entries[:5]:
        print(f"  {entry}")
        
except Exception as e:
    import traceback
    print(f'ERROR: {type(e).__name__} - {str(e)}')
    traceback.print_exc()
