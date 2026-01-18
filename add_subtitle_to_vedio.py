import subprocess
import os
import sys
import json
import whisper



def add_subtitle(
    video_path="vedio_with_audio.mp4",
    audio_path="audio_reel.mp3",
    output_path="final_vedio.mp4",
    ass_file="tiktok_style.ass",
    whisper_model="base",
    language="en"
) -> bool:
    """
    Creates TikTok-style word-by-word captions using Whisper
    and burns them into the video.
    Returns True if successful, False otherwise.
    """

    print("=" * 60)
    print("🎬 TikTok-Style Word-by-Word Captions")
    print("=" * 60)

    try:
        # ------------------ VALIDATION ------------------
        if not os.path.exists(video_path):
            print(f"❌ Video not found: {video_path}")
            return False

        if not os.path.exists(audio_path):
            print(f"❌ Audio not found: {audio_path}")
            return False

        # ------------------ WHISPER SETUP ------------------
        print("\n🎤 Checking Whisper installation...")

        

        print(f"🧠 Loading Whisper model: {whisper_model}")
        model = whisper.load_model(whisper_model)

        # ------------------ TRANSCRIPTION ------------------
        print("🎙️ Transcribing audio with word-level timestamps...")
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language=language
        )

        print("✅ Transcription completed")

        # ------------------ ASS SUBTITLE CREATION ------------------
        print("\n📝 Creating TikTok-style ASS subtitle file...")

        ass_content = """[Script Info]
Title: TikTok Style Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,80,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,5,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        def seconds_to_ass_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            centisecs = int((seconds % 1) * 100)
            return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

        word_count = 0

        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                word = word_info["word"].strip()
                start = word_info["start"]
                end = word_info["end"]

                ass_content += (
                    f"Dialogue: 0,"
                    f"{seconds_to_ass_time(start)},"
                    f"{seconds_to_ass_time(end)},"
                    f"Default,,0,0,0,,{word}\n"
                )
                word_count += 1

        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(ass_content)

        print(f"✅ Subtitle file created: {ass_file}")
        print(f"📝 Total words: {word_count}")

        # ------------------ BURN SUBTITLES ------------------
        print("\n🎬 Rendering video with burned-in captions...")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"ass={ass_file}",
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
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

        if not os.path.exists(output_path):
            print("❌ Output video not created")
            return False

        size_mb = os.path.getsize(output_path) / (1024 * 1024)

        print("\n" + "=" * 60)
        print("🎉 TikTok-STYLE CAPTIONS ADDED!")
        print("=" * 60)
        print(f"📁 Output: {output_path}")
        print(f"💾 Size: {size_mb:.2f} MB")
        print(f"📝 Words rendered: {word_count}")
        print("=" * 60)

        return True

    except subprocess.CalledProcessError as e:
        print("🔥 FFmpeg or Whisper execution failed")
        print(e.stderr.decode(errors="ignore"))
        return False

    except Exception as e:
        print("🔥 Unexpected error occurred")
        print(str(e))
        return False
