import edge_tts
import asyncio
import os

async def generate_audio(text, output_file="long_output.mp3", 
                                voice="en-US-JennyNeural", chunk_size=500):
    """Handles long text by splitting into chunks and merging them."""
    
    # 1. Basic Text Cleaning
    print("====Text Cleaning ====")
    text = text.replace("``", '"').replace("''", '"')
    
    # 2. Split text into manageable chunks
    print("====Splitting Text ====")
    words = text.split()
    chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    
    all_audio = []
    print("====Generating=====")
    try:
        # 3. Generate Audio for each chunk
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            communicate = edge_tts.Communicate(chunk, voice)
            
            temp_file = f"temp_chunk_{i}.mp3"
            await communicate.save(temp_file)
            all_audio.append(temp_file)
            
            # Small sleep to prevent being flagged as a bot
            await asyncio.sleep(0.5)
        
        # 4. Combine all chunks (Binary Merge)
        # This part must be OUTSIDE the loop above
        print("Merging audio files...")
        with open(output_file, 'wb') as outfile:
            for tf in all_audio: # Changed 'temp_files' to 'all_audio'
                with open(tf, 'rb') as infile:
                    outfile.write(infile.read())
        
        print(f"Success! Created: {output_file}")

    finally:
        # 5. Cleanup temporary files
        print("Cleaning up temporary files...")
        for temp_file in all_audio:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    return output_file

