import os
import sys
import shutil
import glob
import cv2
import numpy as np
import subprocess
import time
from pathlib import Path

# Import required modules
from Classified_Clips.FrameClipper26 import clip26frames
from Classified_Clips.MMpose import process_all_videos
from Goal_Viz import process_video
from skeleton import predict_direction  # Import the prediction function

def create_folder(folder_path):
    """Create folder if it doesn't exist"""
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def create_keypoints_animation(keypoints_folder, output_video_path, fps=30):
    """Create a video from keypoints images"""
    print(f"\nCreating keypoints animation video...")
    
    # Find all visualization images
    image_files = sorted(glob.glob(os.path.join(keypoints_folder, "frame_*.jpg")))
    
    if not image_files:
        print(f"No keypoint visualization images found in {keypoints_folder}")
        return None
    
    # Read the first image to get dimensions
    first_image = cv2.imread(image_files[0])
    if first_image is None:
        print(f"Error: Could not read image {image_files[0]}")
        return None
    
    height, width, _ = first_image.shape
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Add each image to the video
    for i, image_file in enumerate(image_files):
        print(f"\rAdding frame {i+1}/{len(image_files)} to keypoints animation", end="")
        img = cv2.imread(image_file)
        if img is not None:
            video_writer.write(img)
    
    video_writer.release()
    print(f"\nKeypoints animation saved to: {output_video_path}")
    return output_video_path

def process_single_video(video_path, output_base_folder=None, model_path='penalty_conv3d_model.h5'):
    """Process a single video through all steps"""
    start_time = time.time()
    
    # Get video filename without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Create output folder
    if output_base_folder is None:
        output_base_folder = "Processed_Videos"
    
    output_folder = create_folder(os.path.join(output_base_folder, video_name))
    print(f"\n{'='*50}")
    print(f"Processing video: {video_path}")
    print(f"Output folder: {output_folder}")
    print(f"{'='*50}")
    
    # Step 1: Convert to 26 frames using FrameClipper26
    print("\nStep 1: Converting to 26 frames...")
    temp_folder = create_folder(os.path.join(output_folder, "temp"))
    
    # Copy the original video to temp folder with a unique name to avoid conflicts
    temp_original = os.path.join(temp_folder, f"{video_name}_original.mp4")
    shutil.copy2(video_path, temp_original)
    
    # Run frame clipper
    clip26frames(temp_folder)
    
    # Find the clipped video - check multiple possible locations
    clipped_videos = []
    
    # Check in the standard Results folder
    clipped_videos.extend(glob.glob(os.path.join("Classified_Clips", "Results", "**", f"{video_name}*.mp4"), recursive=True))
    
    # Check in the output folder's Results folder
    clipped_videos.extend(glob.glob(os.path.join(output_folder, "Results", "**", f"{video_name}*.mp4"), recursive=True))
    
    # Check in the temp folder's Results folder
    clipped_videos.extend(glob.glob(os.path.join(temp_folder, "Results", "**", f"{video_name}*.mp4"), recursive=True))
    
    # Check in the current directory's Results folder
    clipped_videos.extend(glob.glob(os.path.join("Results", "**", f"{video_name}*.mp4"), recursive=True))
    
    # Check for any MP4 file with the video name in the Results folders
    clipped_videos.extend(glob.glob(os.path.join("**", "Results", "**", f"{video_name}*.mp4"), recursive=True))
    
    if not clipped_videos:
        print(f"Error: Could not find clipped video for {video_name}")
        print("Searched in:")
        print(f"  - {os.path.join('Classified_Clips', 'Results', '**', f'{video_name}*.mp4')}")
        print(f"  - {os.path.join(output_folder, 'Results', '**', f'{video_name}*.mp4')}")
        print(f"  - {os.path.join(temp_folder, 'Results', '**', f'{video_name}*.mp4')}")
        print(f"  - {os.path.join('Results', '**', f'{video_name}*.mp4')}")
        print(f"  - {os.path.join('**', 'Results', '**', f'{video_name}*.mp4')}")
        
        # Last resort: try to find any MP4 file in the Results folders
        any_results = glob.glob(os.path.join("**", "Results", "**", "*.mp4"), recursive=True)
        if any_results:
            print("Found these videos in Results folders:")
            for video in any_results:
                print(f"  - {video}")
        
        return False
    
    clipped_video_path = clipped_videos[0]
    print(f"Clipped video found: {clipped_video_path}")
    
    # Copy the clipped video to our output folder
    clipped_video_output = os.path.join(output_folder, f"{video_name}_26frames.mp4")
    shutil.copy2(clipped_video_path, clipped_video_output)
    
    # Step 2: Run MMPose inference
    print("\nStep 2: Running MMPose inference...")
    keypoints_base_folder = create_folder(os.path.join(output_folder, "keypoints"))
    
    # Create a temporary folder just for this video to avoid processing other videos
    mmpose_input_folder = create_folder(os.path.join(output_folder, "mmpose_input"))
    temp_clipped_path = os.path.join(mmpose_input_folder, os.path.basename(clipped_video_output))
    shutil.copy2(clipped_video_output, temp_clipped_path)
    
    # Process the clipped video with MMPose
    processed_folders = process_all_videos(
        input_folder=mmpose_input_folder,
        output_base_folder=keypoints_base_folder,
        return_vis=True,
        save_vis=True
    )
    
    if not processed_folders:
        print("Error: MMPose processing failed")
        return False
    
    # Find the keypoints folder
    keypoints_folder = None
    for folder in processed_folders:
        if os.path.basename(folder).startswith(video_name):
            keypoints_folder = folder
            break
    
    if not keypoints_folder:
        print(f"Error: Could not find keypoints folder for {video_name}")
        # Try to find it manually
        possible_folders = glob.glob(os.path.join(keypoints_base_folder, "**", video_name + "*"), recursive=True)
        if possible_folders:
            keypoints_folder = possible_folders[0]
            print(f"Found potential keypoints folder: {keypoints_folder}")
        else:
            return False
    
    print(f"Keypoints generated in: {keypoints_folder}")
    
    # Step 3: Create keypoints animation video
    print("\nStep 3: Creating keypoints animation...")
    keypoints_video_path = os.path.join(output_folder, f"{video_name}_keypoints.mp4")
    keypoints_animation = create_keypoints_animation(keypoints_folder, keypoints_video_path)
    
    if not keypoints_animation:
        print("Warning: Could not create keypoints animation")
    
    # Step 4: Run prediction model on keypoints data
    print("\nStep 4: Running prediction model...")
    
    # Find the keypoints CSV file - search in multiple possible locations
    keypoints_csv = None
    possible_csv_paths = [
        os.path.join(keypoints_folder, f"{video_name}_keypoints.csv"),
        os.path.join(keypoints_folder, f"{video_name}_26frames_keypoints.csv"),
        os.path.join(keypoints_folder, f"{os.path.basename(keypoints_folder)}_keypoints.csv")
    ]
    
    # Also search recursively
    csv_files = glob.glob(os.path.join(keypoints_folder, "**", "*_keypoints.csv"), recursive=True)
    possible_csv_paths.extend(csv_files)
    
    for csv_path in possible_csv_paths:
        if os.path.exists(csv_path):
            keypoints_csv = csv_path
            print(f"Found keypoints CSV: {keypoints_csv}")
            break
    
    if not keypoints_csv:
        print(f"Error: Keypoints CSV file not found. Searched in:")
        for path in possible_csv_paths:
            print(f"  - {path}")
        prediction = "center"  # Default prediction
    else:
        # Run the prediction model
        prediction, confidence = predict_direction(keypoints_csv, model_path)
        if prediction is None:
            print("Warning: Prediction failed, using default 'center'")
            prediction = "center"
        else:
            print(f"Prediction: {prediction} (confidence: {confidence:.2f})")
    
    # Save prediction to a text file for reference
    prediction_file = os.path.join(output_folder, f"{video_name}_prediction.txt")
    with open(prediction_file, 'w') as f:
        f.write(prediction)
    
    # Step 5: Run Goal Visualization
    print("\nStep 5: Creating goal visualization...")
    visualization_path = os.path.join(output_folder, f"{video_name}_visualization.mp4")
    
    # Process the original video with Goal_Viz
    process_video(
        video_path=video_path,
        output_path=visualization_path,
        prediction=prediction,
        delay=1  # Fast processing
    )
    
    print(f"Visualization created: {visualization_path}")
    
    # Clean up temporary folders
    try:
        shutil.rmtree(mmpose_input_folder)
        print(f"Cleaned up temporary MMPose input folder")
    except Exception as e:
        print(f"Warning: Could not clean up temporary folder: {e}")
    
    # Final summary
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\n{'='*50}")
    print(f"Processing complete for: {video_name}")
    print(f"Total processing time: {processing_time:.2f} seconds")
    print(f"Output files in: {output_folder}")
    print(f"{'='*50}")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python MasterScript.py <video_file.mp4> [output_folder] [model_path]")
        return
    
    video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"Error: Video file {video_path} not found")
        return
    
    output_folder = None
    if len(sys.argv) >= 3:
        output_folder = sys.argv[2]
    
    model_path = 'penalty_conv3d_model.h5'
    if len(sys.argv) >= 4:
        model_path = sys.argv[3]
    
    if not os.path.exists(model_path):
        print(f"Warning: Model file {model_path} not found. Make sure it's in the correct location.")
    
    process_single_video(video_path, output_folder, model_path)

if __name__ == "__main__":
    main()