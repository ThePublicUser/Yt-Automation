import shutil
from script_generator import chunks_to_pexels_titles
from moviepy import AudioFileClip
import math
import os


def generate_pexels_title_from_audio_and_text(audio_path, script):
    duration = get_audio_duration(audio_path)
    total_videos  = math.ceil(duration / 10)  # 1 vedio per 10 sec

    # Split into exactly 'total_videos' parts
    print("==== Splitting Content into Chuncks to Generate bg vedio form")
    words = script.split()
    words_per_video = math.ceil(len(words) / total_videos)
    chunks = [" ".join(words[i:i + words_per_video]) 
              for i in range(0, len(words), words_per_video)][:total_videos]
    print("====chuncks made=====")
    titles =  chunks_to_pexels_titles(chunks)
    return titles

def get_audio_duration(audio_path):
    with AudioFileClip(audio_path) as audio:
        return audio.duration
    
def cleanup_paths(*paths):
    """
    Deletes files or folders if they exist.
    Safe to call multiple times.
    """

    print("🧹 Cleaning up files and folders...")
    
    for path in paths:
        if not path or not os.path.exists(path):
            continue

        try:
            print(path)
            if os.path.isfile(path):
                os.remove(path)
                print(f"🗑️ Deleted file: {path}")

            elif os.path.isdir(path):
                shutil.rmtree(path)
                print(f"🗑️ Deleted folder: {path}")

        except Exception as e:
            print(f"⚠️ Failed to delete {path}: {e}")

    return True
    
    
    


