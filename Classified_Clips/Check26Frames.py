import os
import cv2

def delete_file_prompt(file_path):
    while True:
        response = input(f"Do you want to delete '{os.path.basename(file_path)}'? (y/n): ").lower()
        if response == 'y':
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
                return True
            except Exception as e:
                print(f"Error deleting file: {e}")
                return False
        elif response == 'n':
            print(f"Keeping: {file_path}")
            return False
        else:
            print("Please enter 'y' or 'n'")

def check_videos_for_26_frames(video_folder):
    # Ensure the folder exists
    if not os.path.exists(video_folder):
        print(f"Error: The folder '{video_folder}' does not exist.")
        return
    
    # List all video files in the folder
    video_files = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not video_files:
        print(f"No video files found in '{video_folder}'.")
        return
    
    print(f"Checking videos in folder: {video_folder}")
    
    # Iterate through all video files and check their frame count
    for video_file in video_files:
        video_path = os.path.join(video_folder, video_file)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Unable to open video {video_file}. Skipping...")
            continue
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Get total frame count
        cap.release()  # Release the video file
        
        if total_frames == 26:
            print(f"Video '{video_file}' has exactly 26 frames.")
        else:
            print(f"Video '{video_file}' does NOT have 26 frames (found {total_frames} frames).")
            if total_frames < 26:
                print(f"Warning: '{video_file}' has fewer than 26 frames!")
                delete_file_prompt(video_path)

# Input: Folder path containing videos
video_folder = "Left_Kicks"

check_videos_for_26_frames(video_folder)
