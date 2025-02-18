import cv2
import os

def extract_26_frames(video_path, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get output path
    output_filename = os.path.basename(video_path)
    output_path = os.path.join(output_folder, output_filename)
    
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # Frames per second
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Ensure the video is valid
    if not cap.isOpened():
        print(f"Error: Unable to process video {video_path}")
        return
    
    # Always include the first 3 and last 3 frames
    first_frames = list(range(0, min(3, total_frames)))
    last_frames = list(range(max(total_frames - 3, 0), total_frames))
    
    # Determine middle frames
    middle_frame_count = 26 - len(first_frames) - len(last_frames)
    middle_start = len(first_frames)
    middle_end = total_frames - len(last_frames)

    # Pick middle frames with consistent gaps
    middle_frames = []
    if middle_frame_count > 0 and middle_start < middle_end:
        gap = (middle_end - middle_start) / middle_frame_count
        middle_frames = [int(middle_start + i * gap) for i in range(middle_frame_count)]

    # Combine all selected frames
    frame_indices = sorted(set(first_frames + middle_frames + last_frames))

    # Prepare to save video
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            print(f"Error: Could not create output file for {video_path}")
            cap.release()
            return
            
        # Read and save selected frames
        frame_counter = 0
        frames_written = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_counter in frame_indices:
                out.write(frame)
                frames_written += 1
            frame_counter += 1
        
        # Release resources
        cap.release()
        out.release()

        if frames_written == 26:
            print(f"Successfully extracted 26 frames to {output_path}")
        else:
            print(f"Warning: Only wrote {frames_written} frames to {output_path}")
                
    except Exception as e:
        print(f"Error processing {video_path}: {str(e)}")
        if 'out' in locals():
            out.release()
        if 'cap' in locals():
            cap.release()

def clip26frames(input_folder):
    # Create Results directory at the same level as input folder
    results_dir = os.path.join(os.path.dirname(input_folder), "Results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Determine the output folder based on input folder name
    folder_name = os.path.basename(input_folder)
    if "left" in folder_name.lower():
        output_folder = "Processed_Left_Kicks"
    elif "right" in folder_name.lower():
        output_folder = "Processed_Right_Kicks"
    elif "center" in folder_name.lower():
        output_folder = "Processed_Center_Kicks"
    else:
        output_folder = "Processed_Other_Kicks"
    
    # Create output folder inside Results directory
    output_folder = os.path.join(results_dir, output_folder)
    os.makedirs(output_folder, exist_ok=True)
    
    # Process all videos in the input folder
    for video_file in os.listdir(input_folder):
        if video_file.endswith(('.mp4', '.avi', '.mov')):
            video_path = os.path.join(input_folder, video_file)
            extract_26_frames(video_path, output_folder)
