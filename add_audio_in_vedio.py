import subprocess
import os


def create_video_with_audio(
    video_path="trimed_bg_vedios.mp4",
    audio_path="audio_reel.mp3",
    output_path="vedio_with_audio.mp4"
) -> bool:
    """
    Creates a playable MP4 video using MP3 audio (most reliable).
    Returns True if successful, False otherwise.
    """

    print("🎬 Creating video with MP3 audio (safe mode)")

    try:
        # Validate inputs
        if not os.path.exists(video_path):
            print(f"❌ Video not found: {video_path}")
            return False

        if not os.path.exists(audio_path):
            print(f"❌ Audio not found: {audio_path}")
            return False

        print("📹 Using method: H.264 video + MP3 audio")
        print("🛡️ Reason: AAC silent-audio issue avoided")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",              # Keep original video
            "-c:a", "libmp3lame",        # MP3 audio (safe)
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-movflags", "+faststart",
            output_path
        ]

        print("🚀 Running FFmpeg:")
        print("🧾", " ".join(cmd))

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if os.path.exists(output_path):
            size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"✅ Video created successfully: {output_path}")
            print(f"📦 File size: {size:.2f} MB")
            return True

        print("❌ FFmpeg finished but output file not found")
        return False

    except subprocess.CalledProcessError as e:
        print("🔥 FFmpeg error occurred")
        print(e.stderr.decode(errors="ignore"))
        return False

    except Exception as e:
        print("🔥 Unexpected error")
        print(str(e))
        return False
    
