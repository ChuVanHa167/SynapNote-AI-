# Backblaze B2 Configuration Guide

## Environment Variables

Add these variables to your `backend/.env` file:

```
# Backblaze B2 Configuration
BACKBLAZE_KEY_ID=4a77fa7873aa
BACKBLAZE_APPLICATION_KEY=003939064061b54c873ba6ba9a9322d0914a469ebc
BACKBLAZE_BUCKET_NAME=synapnote-videos
```

## Setup Steps

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Create a bucket in Backblaze B2 named `synapnote-ai` (or update BACKBLAZE_BUCKET_NAME)

3. Make sure the bucket is public (Settings > Bucket Info > Bucket is Public)

4. Run the backend server

## How It Works

### Upload Flow
- When a user uploads a video/audio file, it will be:
  1. Saved temporarily to local `uploads/` folder
  2. Converted to audio (MP3) if it's a video file using FFmpeg
  3. **Uploaded to Backblaze B2 cloud storage**
  4. The public URL from Backblaze will be stored in the database (`audio_url` field)
  5. If it's a video, the original video is also uploaded to Backblaze and stored in `video_url`

### File Structure in B2
```
audio/{meeting_id}.mp3      - Extracted/converted audio
video/{meeting_id}.{ext}    - Original video (if applicable)
```

### Delete Flow
- When a meeting is deleted:
  1. Files are deleted from Backblaze B2 (both audio and video if present)
  2. Local temp files are also cleaned up

### Fallback
- If Backblaze is not configured (missing env vars), files are stored locally only
- If Backblaze upload fails, the system falls back to local storage

## Security Notes

- Keep your `BACKBLAZE_APPLICATION_KEY` secure - it provides full access to your B2 bucket
- The bucket should be public only if you want files accessible via direct URL
- For production, consider implementing signed URLs for private buckets
