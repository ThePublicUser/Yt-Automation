import subprocess
import json
import os


def get_duration(file_path: str) -> float:
    """Return duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        file_path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def trim_vedio_to_audio_length(
    video_path="merged_bg_vedios.mp4",
    audio_path="audio_reel.mp3",
    output_path="trimed_bg_vedios.mp4"
) -> bool:
    """
    Adjusts video speed or trims it to match audio duration.
    Returns True if output is created successfully.
    """

    print("🔍 Checking input files...")

    try:
        if not os.path.exists(video_path):
            print(f"❌ Video not found: {video_path}")
            return False

        if not os.path.exists(audio_path):
            print(f"❌ Audio not found: {audio_path}")
            return False

        print("⏱️ Reading durations using ffprobe...")

        video_dur = get_duration(video_path)
        audio_dur = get_duration(audio_path)

        print(f"🎞️ Video duration: {video_dur:.2f}s")
        print(f"🎵 Audio duration: {audio_dur:.2f}s")

        # Decide speed / trim
        speed = 1.0
        trim_end = None

        if video_dur < audio_dur:
            print("⚡ Video shorter than audio → trying speed-up")

            if video_dur * 1.2 >= audio_dur:
                speed = 1.2
                trim_end = audio_dur
            elif video_dur * 1.25 >= audio_dur:
                speed = 1.25
                trim_end = audio_dur
            else:
                speed = 1.25
                trim_end = audio_dur
                print("⚠️ Even 1.25x not enough, trimming anyway")

        else:
            print("✂️ Video longer than audio → trimming video")
            trim_end = audio_dur

        print(f"🎛️ Final settings → speed={speed}, trim_end={trim_end:.2f}s")

        # Build video filter
        setpts_filter = f"setpts={1/speed}*PTS"
        if trim_end:
            setpts_filter += f",trim=0:{trim_end}"

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter:v", setpts_filter,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        print("🚀 Running FFmpeg command:")
        print("🧾", " ".join(cmd))

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if os.path.exists(output_path):
            print(f"✅ Final output created: {output_path}")
            return True
        else:
            print("❌ FFmpeg finished but output file not found")
            return False

    except subprocess.CalledProcessError as e:
        print("🔥 FFmpeg execution failed")
        print(e.stderr.decode(errors="ignore"))
        return False

    except Exception as e:
        print("🔥 Unexpected error occurred")
        print(str(e))
        return False
    
