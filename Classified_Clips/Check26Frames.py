import cv2
import os

def check_video_frames(folder_path):
    """
    Check the number of frames in each video in the specified folder.
    Returns True if all videos have sufficient frames (≥26), False otherwise.
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder {folder_path} does not exist")
        return False
    
    videos = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not videos:
        print(f"No videos found in {folder_path}")
        return False
    
    print(f"\nChecking videos in {folder_path}:")
    print("-" * 50)
    print(f"{'Video Name':<30} {'Total Frames':<15} {'Status':<10}")
    print("-" * 50)
    
    all_valid = True
    for video in videos:
        video_path = os.path.join(folder_path, video)
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"{video:<30} {'Error':<15} {'Failed':<10}")
            all_valid = False
            continue
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if total_frames < 26:
            status = "Too few"
            all_valid = False
        else:
            status = "OK"
            
        print(f"{video:<30} {total_frames:<15} {status:<10}")
    
    print("-" * 50)
    if all_valid:
        print("All videos have sufficient frames (≥26)")
    else:
        print("WARNING: Some videos have fewer than 26 frames!")
    
    return all_valid

if __name__ == "__main__":
    folder_path = "path/to/your/video/folder"
    check_video_frames(folder_path)
