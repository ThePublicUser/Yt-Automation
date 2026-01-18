import os
import subprocess

# merge vedios from multiple vedios of piceles.

def merge_reel_videos(
    video_dir="reel_vedios",
    output_file="merged_bg_vedios.mp4",
    width=1080,
    height=1920,
    fps=30
) -> bool:
    """
    Merges all mp4 videos in a folder into a single vertical video.
    Returns True if video is generated successfully, False otherwise.
    """

    print("🔍 Checking video directory...")

    try:
        if not os.path.exists(video_dir):
            print(f"❌ Folder not found: {video_dir}")
            return False

        videos = sorted(
            os.path.join(video_dir, f)
            for f in os.listdir(video_dir)
            if f.lower().endswith(".mp4")
        )

        if not videos:
            print("❌ No .mp4 videos found in folder")
            return False

        print(f"🎞️ Found {len(videos)} videos")
        for i, v in enumerate(videos, 1):
            print(f"   {i}. {v}")

        # Build ffmpeg input args
        inputs = []
        for v in videos:
            inputs.extend(["-i", v])

        print("⚙️ Building FFmpeg filter graph...")

        filter_parts = []
        for i in range(len(videos)):
            filter_parts.append(
                f"[{i}:v]"
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"fps={fps}"
                f"[v{i}]"
            )

        v_labels = "".join(f"[v{i}]" for i in range(len(videos)))
        filter_complex = (
            "; ".join(filter_parts)
            + f"; {v_labels}concat=n={len(videos)}:v=1:a=0[outv]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            output_file
        ]

        print("🚀 Running FFmpeg...")
        print("🧾 Command:")
        print(" ".join(cmd))

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if os.path.exists(output_file):
            print(f"✅ Video successfully created: {output_file}")
            return True
        else:
            print("❌ FFmpeg finished but output file not found")
            return False

    except subprocess.CalledProcessError as e:
        print("🔥 FFmpeg failed")
        print(e.stderr.decode(errors="ignore"))
        return False

    except Exception as e:
        print("🔥 Unexpected error occurred")
        print(str(e))
        return False
if __name__ == "__main__":
    success =merge_reel_videos()
    print(success)