from dotenv import load_dotenv
import asyncio
import json
import os
import sys

from audio_generator import generate_audio
from script_generator import generate_youtube_short_metadata, get_genre
from utils import generate_pexels_title_from_audio_and_text, cleanup_paths
from bg_vedio_generator import fetch_vertical_pixabay_videos
from merge_bg_vedios import merge_reel_videos
from trim_vedio import trim_vedio_to_audio_length
from add_audio_in_vedio import create_video_with_audio
from add_subtitle_to_vedio import add_subtitle
from youtube_automation import upload_video_to_yt

if __name__ == "__main__":
    load_dotenv()

    temp_files = [
        "audio_reel.mp3",
        "merged_bg_vedios.mp4",
        "vedio_with_audio.mp4",
        "tiktok_style.ass",
        "trimed_bg_vedios.mp4",
        "vedio_with_audio.mp4",
        "reel_vedios",
        "final_vedio.mp4"
    ]

    try:
        genre = get_genre()
        metadata = generate_youtube_short_metadata(genre)

        if not metadata:
            raise RuntimeError("Failed to generate metadata")

        script = metadata["script"]

        audio = asyncio.run(generate_audio(script, "audio_reel.mp3"))
        if audio != "audio_reel.mp3":
            raise RuntimeError("Audio generation failed")

        data = generate_pexels_title_from_audio_and_text(audio, script)
        if not data:
            raise RuntimeError("Failed to generate Pexels titles")

        api_key = os.getenv("PEXELS_API_KEY")
        vedios = fetch_vertical_pixabay_videos(data, api_key, 30, 15)
        if not vedios:
            raise RuntimeError("Failed to fetch Pixabay videos")

        is_vedio_merged = merge_reel_videos()
        if not is_vedio_merged:
            raise RuntimeError("Video merge failed")

        is_vedio_trimmed = trim_vedio_to_audio_length()
        if not is_vedio_trimmed:
            raise RuntimeError("Video trim failed")

        is_audio_attached = create_video_with_audio()
        if not is_audio_attached:
            raise RuntimeError("Audio attachment failed")

        is_subtitle_attached = add_subtitle()
        if not is_subtitle_attached:
            raise RuntimeError("Subtitle attachment failed")

        description = metadata["description"].rstrip(". ")
        description += (
            ".\n\nDerived from generative inference and should not be treated as empirical fact."
        )

        is_yt_uploaded = upload_video_to_yt(
            "final_vedio.mp4",
            metadata["title"],
            description,
            metadata["tags"],
            privacy_status="public",
        )

        if not is_yt_uploaded:
            raise RuntimeError("YouTube upload failed")

        print("==== Completed Successfully ====")

        cleanup_paths(*temp_files)
        sys.stdout.flush()
        sys.stderr.flush()

    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {e}", file=sys.stderr)
        sys.exit(1)  # ❌ GitHub Actions → RED
