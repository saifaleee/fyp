import os
from Classified_Clips.FrameClipper26 import clip26frames
from Classified_Clips.Augmentation_script import augment_clips
from Classified_Clips.MMpose import process_all_videos
from Classified_Clips.Check26Frames import check_video_frames

def main():
    # Step 1: Define your input folders
    input_folders = {
        "left": "Classified_Clips/Left_Kicks",
        "right": "Classified_Clips/Right_Kicks",
        "center": "Classified_Clips/Center_Kicks"
    }
    
    # Step 1.5: Check video frames before processing
    print("Step 1: Checking video frames...")
    for folder_type, folder_path in input_folders.items():
        if os.path.exists(folder_path):
            print(f"\nChecking {folder_type} kicks...")
            check_video_frames(folder_path)
    
    # Confirm with user before proceeding
    user_input = input("\nDo you want to proceed with processing the videos? (y/n): ")
    if user_input.lower() != 'y':
        print("Processing cancelled.")
        return
    
    # Step 2: Clip the videos into 26 frames
    print("\nStep 2: Clipping videos to 26 frames...")
    for folder_type, folder_path in input_folders.items():
        if os.path.exists(folder_path):
            clip26frames(folder_path)
    
    # Step 3: Augment the clipped videos
    print("\nStep 3: Augmenting the processed videos...")
    results_folder = "Classified_Clips/Results"
    augment_clips(results_folder)
    
    # Step 4: Process all videos with MMPose
    print("\nStep 4: Processing videos with MMPose...")
    keypoints_folder = "Classified_Clips/Keypoints"
    processed_folders = process_all_videos(
        input_folder=results_folder,
        output_base_folder=keypoints_folder,
        return_vis=True,
        save_vis=True
    )
    
    print("\nProcessing complete!")
    print(f"- Processed videos are in: {results_folder}")
    print(f"- Keypoint data is in: {keypoints_folder}")

if __name__ == "__main__":
    main()