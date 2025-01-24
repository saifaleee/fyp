import os
from Classified_Clips.organize_files import organize_videos
from Classified_Clips.Augmentation_script import augment_video
from TAM.get_bbox import process_all_videos
from Classified_Clips.MMPOSE.MMpose import Infer3D
from Classified_Clips.Check26Frames import check_videos_for_26_frames
def main():
    
    input_folders = {
        "left": "Left_Kicks",
        "right": "Right_Kicks",
        "center": "Center_Kicks"
    }

    # Step 1: Check the frames of clips and delete any that are not 26 frames
    print("Step 1: Check for 26 Frames...")

    check_videos_for_26_frames("left")
    check_videos_for_26_frames("right")
    check_videos_for_26_frames("center")


    # Step 2: 
    print("Step 2: Performing data augmentation...")
    
    output_folders = {
        "left": "right_augmented",
        "right": "left_augmented",
        "center": "center_augmented"
    }
    for category, input_folder in input_folders.items():
        output_folder = output_folders[category]
        os.makedirs(output_folder, exist_ok=True)
        for video in os.listdir(input_folder):
            if video.endswith('.mp4'):
                input_path = os.path.join(input_folder, video)
                output_path = os.path.join(output_folder, video)
                augment_video(input_path, output_path)

    # Step 3: Process videos using Track-Anything (TAM)
    print("Step 3: Processing videos with Track-Anything...")
    result_dirs = {
        "left": "Result_Left",
        "center": "Result_Center",
        "right": "Result_Right"
    }
    cropped_dirs = {
        "left": "cropped_vid_left",
        "center": "cropped_vid_center",
        "right": "cropped_vid_right"
    }
    sample_dirs = {
        "left": "sample_frames_left",
        "center": "sample_frames_center",
        "right": "sample_frames_right"
    }
    for category in ["left", "center", "right"]:
        process_all_videos(
            result_dirs[category],
            cropped_dirs[category],
            sample_dirs[category]
        )

    # Step 4: Clip videos to 26 frames
    print("Step 4: Clipping videos to 26 frames...")
    for category, cropped_dir in cropped_dirs.items():
        output_dir = f"clipped_{category}"
        os.makedirs(output_dir, exist_ok=True)
        for video in os.listdir(cropped_dir):
            if video.endswith('.mp4'):
                video_path = os.path.join(cropped_dir, video)
                extract_26_frames(video_path, output_dir)

    # Step 5: Run MMPose inference
    print("Step 5: Running MMPose inference...")
    infer3d = Infer3D()
    processed_folder = "./processed"
    os.makedirs(processed_folder, exist_ok=True)
    
    for category in ["left", "center", "right"]:
        clipped_dir = f"clipped_{category}"
        for video in os.listdir(clipped_dir):
            if video.endswith('.mp4'):
                video_path = os.path.join(clipped_dir, video)
                infer3d.infer_video(video_path, processed_folder, return_vis=True, save_vis=True)

    print("Pipeline completed successfully!")

if __name__ == "__main__":
    main()