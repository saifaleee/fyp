#!/usr/bin/env python3
"""
Football Penalty Analysis API Client

This script allows you to send videos to the Football Penalty Analysis API server,
check processing status, and download the results.

Usage:
    python api_client.py --video path/to/video.mp4 --server http://192.168.18.10
"""

import argparse
import os
import sys
import time
import requests
from tqdm import tqdm

def send_video(server_url, video_path):
    """Upload a video to the API server for processing"""
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return None
    
    print(f"Uploading video: {os.path.basename(video_path)}")
    upload_url = f"{server_url}/api/process_video"
    
    # Get file size for progress bar
    file_size = os.path.getsize(video_path)
    
    try:
        with open(video_path, 'rb') as video_file:
            # Create a progress bar for upload
            with tqdm(total=file_size, unit='B', unit_scale=True, desc="Uploading") as pbar:
                files = {'video': (os.path.basename(video_path), video_file, 'video/mp4')}
                
                # Use a custom monitor to track upload progress
                def upload_progress(monitor):
                    pbar.update(monitor.bytes_read - pbar.n)
                
                response = requests.post(
                    upload_url, 
                    files=files,
                    timeout=600  # 10 minute timeout for large videos
                )
                
        if response.status_code != 200:
            print(f"Error uploading video: {response.status_code}")
            print(response.text)
            return None
            
        result = response.json()
        task_id = result.get('task_id')
        print(f"✅ Upload successful! Task ID: {task_id}")
        return task_id
        
    except Exception as e:
        print(f"Error uploading video: {e}")
        return None

def check_status(server_url, task_id):
    """Check the processing status of a video"""
    status_url = f"{server_url}/api/status/{task_id}"
    
    try:
        response = requests.get(status_url)
        if response.status_code != 200:
            print(f"Error checking status: {response.status_code}")
            print(response.text)
            return None
            
        return response.json()
        
    except Exception as e:
        print(f"Error checking status: {e}")
        return None

def download_file(url, output_path):
    """Download a file with progress bar"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            print(f"Error downloading file: {response.status_code}")
            return False
        
        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Download with progress bar
        with open(output_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading {os.path.basename(output_path)}") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        print(f"✅ Downloaded: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Football Penalty Analysis API Client")
    parser.add_argument("--video", required=True, help="Path to the video file to upload")
    parser.add_argument("--server", default="http://192.168.18.10", help="API server URL (default: http://192.168.18.10)")
    parser.add_argument("--output", default="./results", help="Directory to save downloaded results (default: ./results)")
    
    args = parser.parse_args()
    
    # Normalize server URL (remove trailing slash if present)
    server_url = args.server.rstrip('/')
    
    print(f"🚀 Connecting to server: {server_url}")
    
    # Step 1: Upload video
    task_id = send_video(server_url, args.video)
    if not task_id:
        sys.exit(1)
    
    # Step 2: Check processing status
    print("\n⏳ Checking processing status...")
    
    completed = False
    max_checks = 60  # Check for up to 5 minutes (5 seconds between checks)
    check_count = 0
    
    with tqdm(total=100, desc="Processing") as pbar:
        last_progress = 0
        
        while not completed and check_count < max_checks:
            status_data = check_status(server_url, task_id)
            
            if not status_data:
                print("Failed to get status. Retrying...")
                time.sleep(5)
                check_count += 1
                continue
                
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            
            # Update progress bar
            if progress > last_progress:
                pbar.update(progress - last_progress)
                last_progress = progress
            
            if status == 'completed':
                pbar.update(100 - last_progress)  # Ensure we reach 100%
                completed = True
                print("✅ Processing completed successfully!")
            elif status == 'error':
                print(f"❌ Processing error: {status_data.get('error')}")
                sys.exit(1)
            else:
                # Wait before checking again
                time.sleep(5)
                check_count += 1
    
    if not completed:
        print("❌ Processing did not complete within the expected time.")
        sys.exit(1)
    
    # Step 3: Download result files
    print("\n📥 Downloading result files...")
    
    # Create output directory
    output_dir = os.path.join(args.output, f"task_{task_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the base filename from the original video
    base_filename = os.path.splitext(os.path.basename(args.video))[0]
    
    # Get status data to check available files
    status_data = check_status(server_url, task_id)
    download_urls = status_data.get('download_urls', {})
    
    # Download visualization file
    print("Attempting to download visualization file...")
    viz_url = f"{server_url}/api/download/{task_id}/visualization"
    viz_path = os.path.join(output_dir, f"{base_filename}_visualization.mp4")
    viz_success = download_file(viz_url, viz_path)
    
    if not viz_success:
        print("Trying alternative visualization file names...")
        alt_viz_url = f"{server_url}/api/download/{task_id}/processed"
        alt_viz_path = os.path.join(output_dir, f"{base_filename}_processed.mp4")
        download_file(alt_viz_url, alt_viz_path)
    
    # Download keypoints file
    print("Attempting to download keypoints file...")
    keypoints_url = f"{server_url}/api/download/{task_id}/keypoints"
    keypoints_path = os.path.join(output_dir, f"{base_filename}_keypoints.mp4")
    download_file(keypoints_url, keypoints_path)
    
    # Step 4: Clean up on server
    print("\n🧹 Cleaning up server resources...")
    cleanup_url = f"{server_url}/api/cleanup/{task_id}"
    
    try:
        response = requests.delete(cleanup_url)
        if response.status_code == 200:
            print("✅ Cleanup successful!")
        else:
            print(f"⚠️ Warning: Cleanup failed with status code {response.status_code}")
    except Exception as e:
        print(f"⚠️ Warning: Cleanup error: {e}")
    
    print("\n✨ All done! Your processed videos are available in:")
    print(f"   {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Process interrupted by user.")
        sys.exit(1) 