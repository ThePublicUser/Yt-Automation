import requests
import os
from pathlib import Path

PEXELS_VIDEO_API = "https://api.pexels.com/videos/search"

def fetch_vertical_pixabay_videos(
    search_titles,
    api_key,
    per_page=15,
    timeout=15
):
    """
    Download one most relevant vertical HD video per keyword from Pexels.
    Videos are saved as ved_1.mp4, ved_2.mp4, etc. in reel_vedios directory.
    
    Args:
        search_titles (dict): Dictionary with structure {'title': [keyword1, keyword2, ...]}
                              Each keyword gets ONE video downloaded
        api_key (str): Your Pexels API key
        per_page (int): Number of videos to fetch per keyword for selection
        timeout (int): Request timeout in seconds
    
    Returns:
        list: List of downloaded video file paths
    """
    # Create reel_vedios directory if it doesn't exist
    output_dir = Path("reel_vedios")
    output_dir.mkdir(exist_ok=True)
    
    downloaded_videos = []
    video_counter = 1
    
    # Pexels requires API key in headers
    headers = {
        "Authorization": api_key.strip()  # Remove any whitespace
    }
    
    # Extract the list of keywords (each keyword is actually a title)
    # search_titles = {'title': ['keyword1', 'keyword2', 'keyword3']}
    for main_key, keyword_list in search_titles.items():
        for keyword in keyword_list:
            
            
            best_video = None
            best_score = -1
            
            try:
                print(f"\n   Searching Pexels for: '{keyword}'...")
                
                # Pexels API parameters for vertical videos
                params = {
                    'query': keyword,
                    'orientation': 'portrait',  # Vertical videos
                    'per_page': min(per_page, 80),  # Pexels max is 80
                    'size': 'medium',
                }
                
                # Make the API request
                response = requests.get(
                    PEXELS_VIDEO_API,
                    headers=headers,
                    params=params,
                    timeout=timeout
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Process videos and find the best one
                if 'videos' in data and data['videos']:
                    
                    for video in data['videos']:
                        # Calculate relevance score
                        score = calculate_video_score(video, keyword)
                        
                        if score > best_score:
                            best_score = score
                            best_video = video
                            best_video['search_keyword'] = keyword
                
                else:
                    print(f"   ⚠️ No videos found for: {keyword}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏱️ Timeout error for: {keyword}")
                continue
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    print(f"   ⚠️ Rate limit exceeded. Wait before making more requests.")
                elif response.status_code == 401:
                    print(f"   🔐 Invalid API key. Check your Pexels API key.")
                else:
                    print(f"   ❌ HTTP error: {e}")
                continue
                
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Request error: {str(e)}")
                continue
                
            except ValueError as e:
                print(f"   ⚠️ JSON parsing error: {str(e)}")
                continue
            
            # Download the best video for this keyword
            if best_video:
                video_filename = f"ved_{video_counter}.mp4"
                video_path = output_dir / video_filename
                
                success = download_best_quality_video(
                    best_video, 
                    video_path, 
                    headers
                )
                
                if success:
                    downloaded_videos.append(str(video_path))
                    print(f"\n   ✅ Downloaded: {video_filename}")
                    print(f"      Duration: {best_video['duration']}s")
                    print(f"      Dimensions: {best_video['width']}x{best_video['height']}")
                    print(f"      Keyword: '{best_video['search_keyword']}'")
                    print(f"      Relevance score: {best_score:.2f}")
                    print(f"      By: {best_video['user']['name']}")
                    video_counter += 1
                else:
                    print(f"   ❌ Failed to download video for: '{keyword}'")
            else:
                print(f"\n   ⚠️ No suitable video found for: '{keyword}'")
    
    print(f"\n{'='*70}")
    print(f"🎬 DOWNLOAD COMPLETE!")
    print(f"   Total videos downloaded: {len(downloaded_videos)}")
    print(f"   Location: {output_dir.absolute()}")
    print(f"{'='*70}\n")
    
    return downloaded_videos


def calculate_video_score(video, keyword):
    """
    Calculate relevance score for a video based on multiple factors.
    
    Scoring factors:
    - Duration match (10-15 seconds is ideal, minimum 10s)
    - Video quality (HD preferred)
    - Aspect ratio (closer to 9:16 is better for Reels)
    
    Returns:
        float: Score (higher is better, -1 means disqualified)
    """
    score = 0.0
    
    # 1. DURATION SCORING (40 points max) - Most important
    duration = video.get('duration', 0)
    
    if duration < 10:
        # Too short - disqualify
        return -1
    elif 10 <= duration <= 15:
        # Perfect duration range (ideal for Reels) - full points
        score += 40
    elif 15 < duration <= 20:
        # Acceptable but not ideal - reduced points
        score += 30 - (duration - 15)
    else:
        # Too long - low score
        score += 10
    
    # 2. VIDEO QUALITY SCORING (30 points max)
    has_hd = False
    has_uhd = False
    
    if 'video_files' in video and video['video_files']:
        for file in video['video_files']:
            # FIXED: Handle None values properly
            if file and isinstance(file, dict):
                quality = file.get('quality')
                if quality:  # Only process if quality exists
                    quality_lower = quality.lower()
                    if quality_lower == 'hd':
                        has_hd = True
                    elif quality_lower in ['uhd', '4k']:
                        has_uhd = True
    
    if has_uhd:
        score += 30
    elif has_hd:
        score += 25
    else:
        score += 10  # SD quality
    
    # 3. ASPECT RATIO SCORING (20 points max)
    # Ideal for Reels/Stories: 9:16 = 0.5625
    width = video.get('width', 1)
    height = video.get('height', 1)
    
    if height > 0:
        aspect_ratio = width / height
        ideal_ratio = 9 / 16
        ratio_diff = abs(aspect_ratio - ideal_ratio)
        
        if ratio_diff < 0.05:
            score += 20  # Very close to ideal
        elif ratio_diff < 0.1:
            score += 15
        elif ratio_diff < 0.2:
            score += 10
        else:
            score += 5
    
    # 4. POPULARITY/ENGAGEMENT (10 points max)
    # Base score for being in search results
    score += 10
    
    return score


def download_best_quality_video(video, output_path, headers):
    """
    Download the highest quality HD video file.
    
    Priority: UHD/4K > HD > SD
    
    Args:
        video (dict): Video object from Pexels API
        output_path (Path): Where to save the video
        headers (dict): Authorization headers
    
    Returns:
        bool: True if download successful, False otherwise
    """
    if 'video_files' not in video or not video['video_files']:
        print(f"      ❌ No video files available")
        return False
    
    # Define quality priority
    quality_priority = {
        'uhd': 3,
        '4k': 3,
        'hd': 2,
        'sd': 1,
        'mobile': 0
    }
    
    # Find best quality file
    best_file = None
    best_quality_score = -1
    
    for file in video['video_files']:
        # FIXED: Handle None and check if file is a dict
        if not file or not isinstance(file, dict):
            continue
            
        quality = file.get('quality')
        if not quality:  # Skip if no quality field
            continue
            
        quality_lower = quality.lower()
        quality_score = quality_priority.get(quality_lower, 0)
        
        # Also consider resolution - larger usually means better quality
        file_width = file.get('width', 0)
        file_height = file.get('height', 0)
        file_size = file_width * file_height
        
        total_score = quality_score * 1000000 + file_size
        
        if total_score > best_quality_score and 'link' in file:
            best_quality_score = total_score
            best_file = file
    
    if not best_file:
        print(f"      ❌ No suitable quality found")
        return False
    
    try:
        download_url = best_file['link']
        quality = best_file.get('quality', 'unknown')
        width = best_file.get('width', 'unknown')
        height = best_file.get('height', 'unknown')
        
        print(f"      📥 Downloading {quality.upper()} quality ({width}x{height})...")
        
        # Download the video file
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Get file size for progress tracking
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        # Write to file in chunks
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                   
        return True
        
    except Exception as e:
        print(f"      ❌ Download failed: {str(e)}")
        # Clean up partial download
        if output_path.exists():
            output_path.unlink()
        return False



