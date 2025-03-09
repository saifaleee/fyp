import requests
import time
import os
import argparse
import json

def test_api(api_url, video_path):
    """
    Test the penalty kick analysis API by:
    1. Uploading a video
    2. Checking processing status
    3. Downloading result files
    4. Cleaning up
    
    Args:
        api_url: Base URL of the API (e.g., http://localhost:5000 or https://abc123.ngrok.io)
        video_path: Path to the video file to upload
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return
    
    print(f"Testing API at: {api_url}")
    print(f"Using video file: {video_path}")
    print("-" * 50)
    
    # Step 1: Upload video
    print("\n1. Uploading video...")
    upload_url = f"{api_url}/api/process_video"
    
    try:
        with open(video_path, 'rb') as video_file:
            files = {'video': (os.path.basename(video_path), video_file, 'video/mp4')}
            response = requests.post(upload_url, files=files)
            
        if response.status_code != 200:
            print(f"Error uploading video: {response.status_code}")
            print(response.text)
            return
            
        result = response.json()
        task_id = result.get('task_id')
        print(f"Upload successful! Task ID: {task_id}")
        
    except Exception as e:
        print(f"Error uploading video: {e}")
        return
    
    # Step 2: Check processing status
    print("\n2. Checking processing status...")
    status_url = f"{api_url}/api/status/{task_id}"
    
    completed = False
    max_checks = 30  # Maximum number of status checks
    check_count = 0
    
    while not completed and check_count < max_checks:
        try:
            response = requests.get(status_url)
            if response.status_code != 200:
                print(f"Error checking status: {response.status_code}")
                print(response.text)
                break
                
            status_data = response.json()
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            
            print(f"Status: {status}, Progress: {progress}%")
            
            if status == 'completed':
                completed = True
                print("Processing completed successfully!")
                print(f"Output files: {json.dumps(status_data, indent=2)}")
            elif status == 'error':
                print(f"Processing error: {status_data.get('error')}")
                break
            else:
                # Wait before checking again
                time.sleep(5)
                check_count += 1
                
        except Exception as e:
            print(f"Error checking status: {e}")
            break
    
    if not completed:
        print("Processing did not complete within the expected time.")
        return
    
    # Step 3: Download result files
    print("\n3. Downloading result files...")
    
    # Create output directory
    output_dir = "api_test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Download visualization file
    print("Downloading visualization file...")
    viz_url = f"{api_url}/api/download/{task_id}/visualization"
    viz_path = os.path.join(output_dir, f"test_visualization.mp4")
    
    try:
        response = requests.get(viz_url, stream=True)
        if response.status_code == 200:
            with open(viz_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Visualization file saved to: {viz_path}")
        else:
            print(f"Error downloading visualization file: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error downloading visualization file: {e}")
    
    # Download keypoints file
    print("Downloading keypoints file...")
    keypoints_url = f"{api_url}/api/download/{task_id}/keypoints"
    keypoints_path = os.path.join(output_dir, f"test_keypoints.mp4")
    
    try:
        response = requests.get(keypoints_url, stream=True)
        if response.status_code == 200:
            with open(keypoints_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Keypoints file saved to: {keypoints_path}")
        else:
            print(f"Error downloading keypoints file: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error downloading keypoints file: {e}")
    
    # Step 4: Clean up
    print("\n4. Cleaning up...")
    cleanup_url = f"{api_url}/api/cleanup/{task_id}"
    
    try:
        response = requests.delete(cleanup_url)
        if response.status_code == 200:
            print("Cleanup successful!")
        else:
            print(f"Error during cleanup: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    print("\nAPI test completed!")
    print(f"Result files saved in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the penalty kick analysis API")
    parser.add_argument("--url", default="http://localhost:5000", 
                        help="API server URL (default: http://localhost:5000)")
    parser.add_argument("--video", required=True, 
                        help="Path to the video file to upload")
    
    args = parser.parse_args()
    test_api(args.url, args.video) 